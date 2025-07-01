import mysql.connector
import os
import subprocess

# Configuración MySQL
db_config = {
    "host": "192.168.201.200",
    "user": "grupo3",
    "password": "grupo3",
    "database": "sdnG03_db"
}

FREERADIUS_USERS_FILE = "/etc/freeradius/3.0/users"

# ---------- AUTENTICACIÓN ----------
def authenticate_user(username, password):
    from pyrad.client import Client
    from pyrad.dictionary import Dictionary
    from pyrad.packet import AccessRequest, AccessAccept

    client = Client(server="127.0.0.1", secret=b"testing123", dict=Dictionary("dictionary"))
    client.AuthPort = 1812
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

# ---------- CURSOS ----------
def get_cursos_usuario_por_rol(username, rol_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.idcurso, c.nombre, c.codigo, c.estado
            FROM curso c
            JOIN inscripcion i ON c.idcurso = i.curso_idcurso
            JOIN user u ON i.user_iduser = u.iduser
            WHERE u.username = %s AND i.rol_id = %s
        """
        cursor.execute(query, (username, rol_id))
        cursos = cursor.fetchall()
        cursor.close()
        conn.close()
        return cursos
    except Exception as e:
        print(f"DB error cursos por rol: {e}")
        return []


def get_all_cursos():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idcurso, nombre, codigo, estado FROM curso")
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
        print(f"DB error get curso: {e}")
        return None

def crear_curso(nombre, estado, codigo):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO curso (nombre, estado, codigo) VALUES (%s, %s, %s)", (nombre, estado, codigo))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error crear curso: {e}")

def actualizar_curso(idcurso, nombre, estado, codigo):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("UPDATE curso SET nombre = %s, estado = %s, codigo = %s WHERE idcurso = %s",
                       (nombre, estado, codigo, idcurso))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error actualizar curso: {e}")

def eliminar_curso(idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM curso WHERE idcurso = %s", (idcurso,))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error eliminar curso: {e}")

# ---------- INSCRIPCIONES ----------
def inscribir_usuario_en_curso(username, idcurso, rol_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT iduser FROM user WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO inscripcion (user_iduser, curso_idcurso, rol_id)
            VALUES (%s, %s, %s)
        """, (user_id, idcurso, rol_id))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error inscribir usuario: {e}")

def get_inscritos_en_curso(idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.username, u.names, u.lastnames
            FROM inscripcion i
            JOIN user u ON i.user_iduser = u.iduser
            WHERE i.curso_idcurso = %s AND i.rol_id = 2
        """, (idcurso,))
        inscritos = cursor.fetchall()
        cursor.close()
        conn.close()
        return inscritos
    except Exception as e:
        print(f"DB error inscritos: {e}")
        return []

# ---------- USUARIOS ----------
def get_all_usuarios(exclude_username=None):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        if exclude_username:
            cursor.execute("""
                SELECT u.username, u.names, u.lastnames, r.rolname
                FROM user u
                JOIN role r ON u.rol = r.idrole
                WHERE u.username != %s
            """, (exclude_username,))
        else:
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

def get_all_roles():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT idrole, rolname FROM role")
        roles = cursor.fetchall()
        cursor.close()
        conn.close()
        return roles
    except Exception as e:
        print(f"DB error roles: {e}")
        return []

def crear_usuario(username, password, names, lastnames, rol):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO user (username, password, names, lastnames, rol)
            VALUES (%s, %s, %s, %s, %s)
        """, (username, password, names, lastnames, rol))
        conn.commit()
        cursor.close()
        conn.close()
        _agregar_a_freeradius(username, password)
        _reiniciar_freeradius()
    except Exception as e:
        print(f"DB error crear usuario: {e}")

def actualizar_usuario(username, names, lastnames, rol, password=None):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE user SET names=%s, lastnames=%s, rol=%s WHERE username=%s
        """, (names, lastnames, rol, username))
        conn.commit()
        cursor.close()
        conn.close()
        if password:
            _actualizar_freeradius_password(username, password)
            _reiniciar_freeradius()
    except Exception as e:
        print(f"DB error actualizar usuario: {e}")

def eliminar_usuario(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM user WHERE username = %s", (username,))
        conn.commit()
        cursor.close()
        conn.close()
        _eliminar_de_freeradius(username)
        _reiniciar_freeradius()
    except Exception as e:
        print(f"DB error eliminar usuario: {e}")

# ---------- FREERADIUS ----------
def _agregar_a_freeradius(username, password):
    try:
        with open(FREERADIUS_USERS_FILE, "a") as f:
            f.write(f"\n{username}\tCleartext-Password := \"{password}\"\n\tReply-Message := \"Bienvenido {username}\"\n")
    except Exception as e:
        print(f"Error escribiendo en FreeRADIUS: {e}")

def _actualizar_freeradius_password(username, password):
    try:
        with open(FREERADIUS_USERS_FILE, "r") as f:
            lines = f.readlines()

        new_lines = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if line.strip().startswith(username):
                new_lines.append(f"{username}\tCleartext-Password := \"{password}\"\n")
                new_lines.append(f"\tReply-Message := \"Bienvenido {username}\"\n")
                skip_next = True
            else:
                new_lines.append(line)

        with open(FREERADIUS_USERS_FILE, "w") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error actualizando FreeRADIUS: {e}")

def _eliminar_de_freeradius(username):
    try:
        with open(FREERADIUS_USERS_FILE, "r") as f:
            lines = f.readlines()

        new_lines = []
        skip_next = False
        for line in lines:
            if skip_next:
                skip_next = False
                continue
            if line.strip().startswith(username):
                skip_next = True
                continue
            new_lines.append(line)

        with open(FREERADIUS_USERS_FILE, "w") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error eliminando de FreeRADIUS: {e}")

def _reiniciar_freeradius():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "freeradius"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error al reiniciar FreeRADIUS: {e}")
