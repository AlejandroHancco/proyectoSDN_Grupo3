# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept
import mysql.connector

app = Flask(__name__)
app.secret_key = "grupo4"

# Configuración MySQL
db_config = {
    "host": "192.168.201.200",
    "user": "grupo3",
    "password": "grupo3",
    "database": "sdnG03_db"
}

# Configuración FreeRADIUS
RADIUS_SERVER = "127.0.0.1"
RADIUS_PORT = 1812
SECRET = b"testing123"
DICT_PATH = "dictionary"

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT

def authenticateUser(username, password):
    req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
    req["User-Password"] = req.PwCrypt(password)
    reply = client.SendPacket(req)
    return reply.code == AccessAccept

def getUserDb(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.username, u.names, u.lastnames, u.code, u.rol, r.rolname
            FROM user u
            JOIN role r ON u.rol = r.idrole
            WHERE u.username = %s
        """
        cursor.execute(query, (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        return user
    except Exception as e:
        print(f"DB error: {e}")
        return None

def getCursosAlumno(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.nombre, c.estado
            FROM curso c
            JOIN inscripcion i ON c.idcurso = i.curso_idcurso
            JOIN user u ON i.user_iduser = u.iduser
            WHERE u.username = %s AND c.estado = 'activo'
        """
        cursor.execute(query, (username,))
        cursos = cursor.fetchall()
        cursor.close()
        conn.close()
        return cursos
    except Exception as e:
        print(f"DB error cursos: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if authenticateUser(username, password):
            usuario = getUserDb(username)
            if not usuario:
                return "Usuario no encontrado en BD", 404
            session["usuario"] = usuario
            if usuario["rolname"].lower() == "alumno":
                cursos = getCursosAlumno(username)
                return render_template("cursos.html", usuario=usuario, cursos=cursos)
            else:
                return f"Bienvenido {usuario['names']} {usuario['lastnames']}, rol: {usuario['rolname']}"
        else:
            return "Credenciales inválidas", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
