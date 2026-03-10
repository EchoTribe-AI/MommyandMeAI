from flask import Flask, send_from_directory

app = Flask(__name__)

@app.route('/')
def index():
    return send_from_directory('.', 'steph-ai-plan.html')

@app.route('/architecture')
def architecture():
    return send_from_directory('.', 'steph-architecture.html')

@app.route('/plan')
def plan():
    return send_from_directory('.', 'steph-ai-plan.html')

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=5000, debug=os.environ.get('FLASK_DEBUG', 'false').lower() == 'true')
