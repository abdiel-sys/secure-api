from flask import Blueprint, jsonify, request, current_app
import datetime
import bcrypt
import sqlite3
from db import get_db_connection
from pydantic import BaseModel, ValidationError, EmailStr, ConfigDict, Field
from flask_jwt_extended import create_access_token

auth_bp = Blueprint("auth", __name__)


class UserSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=10)

    model_config = ConfigDict(extra="forbid")


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        user = UserSchema(**request.json)
    except ValidationError as e:
        current_app.logger.warning(f"Error de validacion {request.remote_addr}: {e}")
        return jsonify({"ERROR 400": "Credenciales Invalidas"}), 400

    conn = get_db_connection()
    data = conn.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    conn.close()
    if not data:
        current_app.logger.info(f"Usuario no existe desde: {request.remote_addr}")
        return jsonify({"ERROR": "Usuario no existe"})

    hash_db = data["password"]
    if isinstance(hash_db, str):
        hash_db = hash_db.encode("utf-8")

    password_input = user.password.encode("utf-8")

    if bcrypt.checkpw(password_input, hash_db):
        access_token = create_access_token(
            identity=str(data["id"]),
            additional_claims={"email": data["email"], "role": data["role"]},
            expires_delta=datetime.timedelta(hours=24),
        )

        current_app.logger.info(f"Login exitoso de: {request.remote_addr}")
        return jsonify(
            {"SUCCESS 201": "Bienvenido a la aplicación", "token": access_token}
        ), 201
    else:
        current_app.logger.warning(f"Credenciales inválidas de {request.remote_addr}")

        return jsonify({"ERRROR": "Credenciales inválidas"}), 401


@auth_bp.route("/registro", methods=["POST"])
def registro():
    try:
        user = UserSchema(**request.json)
    except ValidationError as e:
        current_app.logger.warning(f"Error de validacion {request.remote_addr}: {e}")
        return jsonify({"ERROR 400": "Credenciales Invalidas"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users")

        data = cursor.fetchall()
        for row in data:
            if row[0] == user.email:
                current_app.logger.warning(
                    f"Correo ya existe: {user.email} desde {request.remote_addr}"
                )
                return jsonify({"ERROR 409": "El usuario ya existe"}), 409

        bpassword = user.password.encode("utf-8")
        salt = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(bpassword, salt)

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (user.email, hash_password),
        )
        conn.commit()
        conn.close()
    except sqlite3.Error:
        return jsonify({"ERROR 500": "Error en el servidor"}), 500

    return jsonify({"SUCCESS 201": "Usuario Registrado"}), 201
