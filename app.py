import sqlite3
import bcrypt
from pydantic import BaseModel, ValidationError, EmailStr, ConfigDict, Field
from flask import Flask, jsonify, request

app = Flask(__name__)

class UserSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8, max_length = 10)

    model_config = ConfigDict(extra="forbid")

@app.route('/registro', methods=['POST'])
def register_user():
    try:
        user = UserSchema(**request.json)
    except ValidationError as e:
        return jsonify({"ERROR 400" : "Credenciales Invalidas"}), 400

    try:
        conn = sqlite3.connect('userdata.db')
        cursor = conn.cursor()
        cursor.execute("SELECT email FROM usuarios")

        data = cursor.fetchall()

        for row in data:
            if (row[0] == user.email):
                return jsonify({"ERROR 409": "El usuario ya existe"}), 409

        bpassword = user.password.encode("utf-8")
        salt = bcrypt.gensalt()
        hash_password = bcrypt.hashpw(bpassword, salt)

        cursor.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)", (user.email, hash_password.decode()))
        conn.commit()
    except sqlite3.Error as error:
        return jsonify({"ERROR 500" : "Error en el servidor"}), 500

    return jsonify({"SUCCESS 201" : "Usuario Registrado"}), 201

if __name__ == '__main__':
    app.run(debug=True)
