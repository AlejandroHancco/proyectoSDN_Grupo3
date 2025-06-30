# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept
import mysql.connector

# ----------------------------
# -- Configuración de Flask --
# ----------------------------
app = Flask(__name__)
app.secret_key = "grupo4"

# --------------------------------------
# -- Configuración del cliente RADIUS --
# --------------------------------------
RADIUS_SERVER = "127.0.0.1"
RADIUS_PORT = 1812
SECRET = b"testing123"
DICT_PATH = "dictionary"  # Asegúrate que este archivo existe y es correcto

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT

# ----------------------------
# -- Configuración MySQL BD --
# ----------------------------
db_config = {
    "host": "192.168.201.200",
    "user": "grupo3",
    "password": "grupo3",
    "database": "sdnG03_db"
}

# Función para obtener el rol del usuario
def get_user_role(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT rol FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        return result[0] if result else None
    finally:
        cursor.close()
        conn.close()

# Función para obtener cursos de alumno
def get_cursos_alumno(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*
            FROM curso c
            JOIN inscripcion i ON c.idcurso = i.curso_idcurso
            JOIN user u ON u.iduser = i.user_iduser
            WHERE u.username = %s
        """
        cursor.execute(query, (username,))
        cursos = cursor.fetchall()
        return cursos
    finally:
        cursor.close()
        conn.close()

# Ruta principal - login
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
        req["User-Password"] = req.PwCrypt(password)

        try:
            reply = client.SendPacket(req)
            if reply.code == AccessAccept:
                rol = get_user_role(username)
                if rol == "alumno":
                    cursos = get_cursos_alumno(username)
                    return render_template("cursos.html", cursos=cursos, usuario=username)
                else:
                    return f"Bienvenido {username}, rol: {rol}"
            else:
                return "❌ Acceso denegado (Access-Reject u otro código)"
        except Exception as e:
            return f"⚠️ Error al comunicarse con FreeRADIUS: {e}"

    return render_template("login.html")

# ------------------
# -- Arranque app --
# ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
