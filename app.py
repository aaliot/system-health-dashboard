from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/health')
def health_check():
    return jsonify({"status":"UP"})

@app.route('/version')
def version():
    return jsonify({"version": "1.0.0"})

@app.route('/environment')
def environment():
    return jsonify({"environment": os.environ.get("APP_ENV", "unknown")})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)