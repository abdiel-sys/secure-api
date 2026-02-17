import email_validator
import sqlite3
import bcrypt
from pydantic import BaseModel, ValidationError, EmailStr, ConfigDict, Field
from flask import Flask, jsonify, request

app = Flask(__name__)

class UserSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length = 8, max_length = 10)

    model_config = ConfigDict(extra="forbid")

class ActualizarPasswordSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=10)
    new_password: str = Field(min_length=8, max_length=10)

class AcutalizarRoleSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=10)
    new_role:  str

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

        cursor.execute("INSERT INTO usuarios (email, password) VALUES (?, ?)", (user.email, hash_password))
        conn.commit()
    except sqlite3.Error as error:
        return jsonify({"ERROR 500" : "Error en el servidor"}), 500

    return jsonify({"SUCCESS 201" : "Usuario Registrado"}), 201

@app.route('/actualizar_pass', methods=['PUT'])
def actualizar_pass():
    try:
        user = ActualizarPasswordSchema(**request.json)
    except ValidationError as e:
        return jsonify({"ERROR 400" : "Credenciales invalidas"})
    
    try:
        conn = sqlite3.connect('userdata.db')
        cursor =  conn.cursor()
        cursor.execute('SELECT id, password FROM usuarios WHERE email =?', (user.email, )) 
        data = cursor.fetchone()
        if data:
            old_password = user.password.encode("utf-8")
            new_password = user.new_password.encode("utf-8")
            if bcrypt.checkpw(old_password, data[1]):
                salt = bcrypt.gensalt()
                hash_password = bcrypt.hashpw(new_password, salt)
                cursor.execute("UPDATE usuarios SET password = ? WHERE id = ?", (hash_password, data[0]))
                conn.commit()
            else:
                return jsonify({"Error" : "Contrasenas no coninciden"})

        else: 
            return jsonify({"ERROR": "Usuario no existe"})
        return jsonify({"SUCCESS 201" : "Usuario actualizado"})

    except sqlite3.Error as error:
        print(error)
        return jsonify({"ERROR 500" : "Error en el servidor"}), 500

@app.route('/actualizar_role', methods=['PUT'])
def actualizar_role():
    try:
        user = AcutalizarRoleSchema(**request.json)
    except ValidationError as e:
        return jsonify({"ERROR 400" : "Credenciales invalidas"})
    
    try:
        conn = sqlite3.connect('userdata.db')
        cursor =  conn.cursor()
        cursor.execute('SELECT id, password FROM usuarios WHERE email =?', (user.email, )) 
        data = cursor.fetchone()
        if data:
            password = user.password.encode("utf-8")
            if bcrypt.checkpw(password, data[1]):
                cursor.execute("UPDATE usuarios SET role = ? WHERE id = ?", (user.new_role, data[0]))
                conn.commit()
            else:
                return jsonify({"Error" : "Contrasenas no coninciden"})

        else: 
            return jsonify({"ERROR": "Usuario no existe"})
        return jsonify({"SUCCESS 201" : "Usuario actualizado"})

    except sqlite3.Error as error:
        print(error)
        return jsonify({"ERROR 500" : "Error en el servidor"}), 500




if __name__ == '__main__':
    app.run(debug=True)
