from flask import Blueprint, request, jsonify
from services.ai_service import generate_content
from services.encryption_util import encrypt_message, generate_key
from functools import wraps
import time
import os
from datetime import datetime, timedelta

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

@api.route('/v1/generate', methods=['POST'])
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
        return jsonify({'response': result})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api.route('/v1/status', methods=['GET'])
def status():
    return jsonify({
        'status': 'healthy',
        'model': 'gemini-1.5-flash'
    })

@api.route('/v1/settings/api-key', methods=['GET'])
def get_api_key():
    try:
        with open('api.txt', 'r') as f:
            return jsonify({'api_key': f.read().strip()})
    except:
        return jsonify({'error': 'Could not read API key'}), 500

@api.route('/v1/settings/api-key', methods=['POST'])
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

@api.route('/v1/statistics', methods=['GET'])
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