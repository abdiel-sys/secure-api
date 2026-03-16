import time
import os
from flask import Flask, request, jsonify, g
from rutas.auth import auth_bp
from rutas.surveys import survey_bp
from flask_jwt_extended import JWTManager
from config import Config
import logging
from logging.handlers import RotatingFileHandler

app = Flask(__name__)

# -----------------------------
# Configure Logging
# -----------------------------
handler = RotatingFileHandler("app.log", maxBytes=1000000, backupCount=5)

handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))

handler.setLevel(logging.DEBUG)

app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)


# -----------------------------
# Before request (start timer)
# -----------------------------
@app.before_request
def start_timer():
    g.start_time = time.time()


# -----------------------------
# After request (log response)
# -----------------------------
@app.after_request
def log_request(response):
    duration = round((time.time() - g.start_time) * 1000, 2)

    app.logger.info(
        f"{request.remote_addr} "
        f"{request.method} "
        f"{request.path} "
        f"{response.status_code} "
        f"{duration}ms"
    )

    return response


# -----------------------------
# Register blueprints
# -----------------------------
app.register_blueprint(auth_bp)
app.register_blueprint(survey_bp)

# -----------------------------
# JWT Config
# -----------------------------
app.config["JWT_SECRET_KEY"] = Config.SECRET_KEY
jwt = JWTManager(app)


# -----------------------------
# Global error handler
# -----------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error(f"Unhandled error: {str(e)}")
    return jsonify({"error": "Internal Server Error"}), 500


# -----------------------------
# Run server
# -----------------------------
if __name__ == "__main__":
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        app.logger.info("Starting Flask API")
    app.run(debug=True, port=5000)
