from flask import Blueprint, jsonify, request
from datetime import timezone
import datetime
import bcrypt
import jwt
import sqlite3
from config import Config
from db import get_db_connection
from pydantic import BaseModel, ValidationError, EmailStr, ConfigDict, Field

auth_bp = Blueprint("auth", __name__)


class UserSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=10)

    model_config = ConfigDict(extra="forbid")


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        user = UserSchema(**request.json)
    except ValidationError:
        return jsonify({"ERROR 400": "Credenciales Invalidas"}), 400

    conn = get_db_connection()
    data = conn.execute("SELECT * FROM users WHERE email = ?", (user.email,)).fetchone()
    conn.close()

    if not data:
        return jsonify({"ERROR": "Usuario no existe"})

    hash_db = data["password"]
    if isinstance(hash_db, str):
        hash_db = hash_db.encode("utf-8")

    password_input = user.password.encode("utf-8")

    if bcrypt.checkpw(password_input, hash_db):
        payload = {
            "user_id": data["id"],
            "email": data["email"],
            "role": data["role"],
            "exp": datetime.datetime.now(timezone.utc) + datetime.timedelta(hours=24),
            "iat": datetime.datetime.now(timezone.utc),
        }

        token = jwt.encode(payload, Config.SECRET_KEY, algorithm=Config.JWT_ALGORITHM)

        return jsonify(
            {"SUCCESS 201": "Bienvenido a la aplicación", "token": token}
        ), 201
    else:
        return jsonify({"ERRROR": "Credenciales inválidas"}), 401


@auth_bp.route("/registro", methods=["POST"])
def registro():
    try:
        user = UserSchema(**request.json)
    except ValidationError:
        return jsonify({"ERROR 400": "Credenciales Invalidas"}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM users")

        data = cursor.fetchall()
        for row in data:
            if row[0] == user.email:
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
    except sqlite3.Error as e:
        print(e)
        return jsonify({"ERROR 500": "Error en el servidor"}), 500

    return jsonify({"SUCCESS 201": "Usuario Registrado"}), 201
