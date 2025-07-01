# -*- coding: utf-8 -*-
import mysql.connector
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept

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

def authenticate_user(username, password):
    req = client.CreateAuthPacket(code=AccessRequest, User_Name=username)
    req["User-Password"] = req.PwCrypt(password)
    reply = client.SendPacket(req)
    return reply.code == AccessAccept

def get_user_db(username):
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
def actualizar_usuario(username, names, lastnames, rol):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE user SET names = %s, lastnames = %s, rol = %s WHERE username = %s",
            (names, lastnames, rol, username)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error actualizar_usuario: {e}")
def get_cursos_alumno(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.idcurso, c.nombre, c.estado
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

def get_all_usuarios():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.username, u.names, u.lastnames, r.rolname
            FROM user u
            JOIN role r ON u.rol = r.idrole
        """)
        usuarios = cursor.fetchall()
        cursor.close()
        conn.close()
        return usuarios
    except Exception as e:
        print(f"DB error usuarios: {e}")
        return []

def get_all_cursos():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idcurso, nombre, estado FROM curso")
        cursos = cursor.fetchall()
        cursor.close()
        conn.close()
        return cursos
    except Exception as e:
        print(f"DB error cursos: {e}")
        return []
def get_curso_por_id(idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM curso WHERE idcurso = %s", (idcurso,))
        curso = cursor.fetchone()
        cursor.close()
        conn.close()
        return curso
    except Exception as e:
        print(f"DB error get_curso_por_id: {e}")
        return None

def actualizar_curso(idcurso, nombre, estado):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE curso SET nombre = %s, estado = %s WHERE idcurso = %s", (nombre, estado, idcurso))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error actualizar_curso: {e}")


def actualizar_curso(idcurso, nombre, estado):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE curso SET nombre = %s, estado = %s WHERE idcurso = %s", (nombre, estado, idcurso))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error actualizar_curso: {e}")


def eliminar_curso(idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM curso WHERE idcurso = %s", (idcurso,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error eliminar_curso: {e}")

