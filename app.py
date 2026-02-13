import sqlite3
import bcrypt
from pydantic import BaseModel, ValidationError, EmailStr, ConfigDict, Field
from flask import Flask, jsonify, request

app = Flask(__name__)

class UserSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8, max_length = 10)

    model_config = ConfigDict(extra="forbid")

@app.route('/register', methods=['POST'])
def register_user():
    try:
        user = UserSchema(**request.json)
    except ValidationError as e:
        return jsonify({"error" : "Credenciales Invalidas"}), 400
    return jsonify({"message" : "Validacion correcta"}), 201


if __name__ == '__main__':
    app.run(debug=True)
