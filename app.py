from flask import Flask
from rutas.auth import auth_bp
from rutas.surveys import survey_bp
from flask_jwt_extended import JWTManager
from config import Config

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(survey_bp)
app.config["JWT_SECRET_KEY"] = Config.SECRET_KEY
jwt = JWTManager(app)

if __name__ == "__main__":
    app.run(debug=True, port=5000)
