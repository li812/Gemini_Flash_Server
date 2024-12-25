from flask import Flask, render_template
from routes.api import api

app = Flask(__name__)
app.register_blueprint(api, url_prefix='/api')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/settings')
def settings():
    return render_template('settings.html')

@app.route('/usage')
def usage():
    return render_template('usage.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5050, debug=True)