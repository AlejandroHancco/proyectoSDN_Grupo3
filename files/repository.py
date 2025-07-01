import mysql.connector
import os

# Configuración MySQL
db_config = {
    "host": "192.168.201.200",
    "user": "grupo3",
    "password": "grupo3",
    "database": "sdnG03_db"
}

FREERADIUS_USERS_FILE = "/etc/freeradius/3.0/users"

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
    except Exception as e:
        print(f"DB error eliminar usuario: {e}")

def actualizar_curso(idcurso, nombre, estado):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE curso SET nombre=%s, estado=%s WHERE idcurso=%s
        """, (nombre, estado, idcurso))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error actualizar curso: {e}")

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

def crear_curso(nombre, estado):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO curso (nombre, estado) VALUES (%s, %s)", (nombre, estado))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error crear curso: {e}")

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
    except Exception as e:
        print(f"DB error crear usuario: {e}")

# Funciones internas para archivo FreeRADIUS

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
            else:
                new_lines.append(line)

        with open(FREERADIUS_USERS_FILE, "w") as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error eliminando de FreeRADIUS: {e}")
