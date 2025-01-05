from flask import Blueprint, request, jsonify
from services.ai_service import generate_content
from services.encryption_util import encrypt_message, generate_key
from functools import wraps
import time
import os
from datetime import datetime, timedelta

import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model

api = Blueprint('api', __name__)
request_times = []

daily_requests = {
    'count': 0,
    'date': datetime.now().date()
}

# Replace existing hourly tracking variables with a single structure
hourly_stats = {
    'date': datetime.now().date(),
    'data': [0] * 24,  # Store actual requests per hour
    'current_hour': datetime.now().hour
}

def rate_limit(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        now = time.time()
        request_times.append(now)
        request_times[:] = [t for t in request_times if t > now - 60]
        if len(request_times) > 60:
            return jsonify({'error': 'Rate limit exceeded'}), 429
        return f(*args, **kwargs)
    return decorated_function

@api.route('/llm/generate', methods=['POST'])
@rate_limit
def generate():
    try:
        data = request.get_json()
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        current_time = datetime.now()
        current_hour = current_time.hour
        
        # Increment request count for current hour
        hourly_stats['data'][current_hour] += 1
        daily_requests['count'] += 1
        
        result = generate_content(data['prompt'])
        print(f"""\n\n
              prompt --->  {data['prompt']}\n\n
              result --->  {result}
              """)
        return jsonify({'response': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/llm/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'healthy',
        'model': 'gemini-1.5-flash'
    })

@api.route('/llm/settings/api-key', methods=['GET'])
def get_api_key():
    try:
        with open('api.txt', 'r') as f:
            return jsonify({'api_key': f.read().strip()})
    except:
        return jsonify({'error': 'Could not read API key'}), 500

@api.route('/llm/settings/api-key', methods=['POST'])
def update_api_key():
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({'error': 'No API key provided'}), 400
        
        key = generate_key()
        encrypted_api_key = encrypt_message(data['api_key'], key)
        
        # Write the encrypted key first
        with open('key.txt', 'wb') as f:
            f.write(key)
            
        # Then write the encrypted API key
        with open('api.txt', 'w') as f:
            f.write(encrypted_api_key)
        
        return jsonify({'message': 'API key updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/llm/statistics', methods=['GET'])
def get_statistics():
    current_time = datetime.now()
    current_date = current_time.date()
    current_hour = current_time.hour

    # Reset for new day
    if hourly_stats['date'] != current_date:
        hourly_stats['date'] = current_date
        hourly_stats['data'] = [0] * 24
        daily_requests['count'] = 0
        daily_requests['date'] = current_date
        hourly_stats['current_hour'] = current_hour

    # Calculate rate limit
    now = time.time()
    current_rate = len([t for t in request_times if t > now - 60])

    return jsonify({
        'requests_today': daily_requests['count'],
        'current_rate': f"{current_rate}/60",
        'hourly_requests': hourly_stats['data']
    })
    
    


model = load_model('src/dl_model/cosmic_image_classification.h5')

categories = ['Asteroid', 'Black Hole', 'Comet', 'Constellation', 'Nebula', 'Planet', 'Star']

def preprocess_image(image_path):
    image_data = tf.io.read_file(image_path)
    image = tf.image.decode_jpeg(image_data, channels=3)
    image = tf.image.resize(image, [500, 500]) / 255.0
    return tf.expand_dims(image, axis=0) 

@api.route('/image_classification/classify', methods=['POST'])
def classify_image():
    print("Received request to classify image")
    
    # Check if file was uploaded
    if 'image' not in request.files:
        print("No image file provided")
        return jsonify({'error': 'No image file provided'}), 400
        
    file = request.files['image']
    print(f"File uploaded: {file.filename}")
    
    # Validate file type
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        print("Invalid file type")
        return jsonify({'error': 'Invalid file type. Please upload PNG or JPG'}), 400

    # Save uploaded file temporarily
    temp_path = 'temp_uploads/temp_image.jpg'
    os.makedirs('temp_uploads', exist_ok=True)
    file.save(temp_path)
    print(f"File saved temporarily at {temp_path}")

    try:
        # Preprocess and predict
        processed_image = preprocess_image(temp_path)
        print("Image preprocessed")
        predictions = model.predict(processed_image)
        print(f"Predictions: {predictions}")
        
        # Get top 3 predictions with probabilities
        top_3_indices = np.argsort(predictions[0])[-3:][::-1]
        results = [
            {
                'category': categories[i],
                'confidence': float(predictions[0][i])
            }
            for i in top_3_indices
        ]
        print(f"Top 3 predictions: {results}")

        return jsonify({
            'success': True,
            'predictions': results
        })

    except Exception as e:
        print(f"Error during classification: {str(e)}")
        return jsonify({'error': str(e)}), 500

    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
            print(f"Temporary file {temp_path} removed")
