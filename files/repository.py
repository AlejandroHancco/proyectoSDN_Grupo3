#Este script son las funciones del sql y algunas que implican el uso del FreeRadius y Floodlight
import mysql.connector
import os
import subprocess
import requests
from . import flowUtils
# Configuración MySQL
db_config = {
    "host": "192.168.201.200",
    "user": "grupo3",
    "password": "grupo3",
    "database": "sdnG03_db"
}
CONTROLLER_IP = "127.0.0.1"  
CONTROLLER_PORT = 8080      

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

def agregar_flows_para_usuario(username):
    user = get_user_db(username)
    if not user:
        print(f"Usuario {username} no encontrado.")
        return

    rol_id = user['rol']
    ip_usuario = user['ip']
    sw_src = user['sw_id']
    port_src = user['sw_port']
    mac_src = user['mac']

    if not sw_src:
        print(f"No se encontró punto de conexión para {username}")
        return

    cursos = get_cursos_usuario_por_rol(username, rol_id)
    if not cursos:
        print(f"No se encontraron cursos para {username}")
        return

    for curso in cursos:
        servidores = get_servidores_permitidos(curso['idcurso'])
        for srv in servidores:
            # Obtenemos todos los datos directamente del servidor devuelto
            sw_dst = srv['sw_id']
            port_dst = srv['sw_port']
            mac_dst = srv['mac']

            if not sw_dst or not port_dst:
                print(f"Datos incompletos del servidor para el curso {curso['idcurso']}")
                continue

            handler = f"{username}-{srv['ip']}-{srv['puerto']}"

            flowUtils.crear_conexion(
                src_dpid=sw_src,
                src_port=port_src,
                dst_dpid=sw_dst,
                dst_port=port_dst,
                ip_usuario=ip_usuario,
                ip_recurso=srv['ip'],
                mac_usuario=mac_src,
                mac_recurso=mac_dst,
                port_recurso=srv['puerto'],
                handlername=handler
            )
    agregar_flows_por_regla_de_rol(username)

            
def get_user_db(username):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT u.iduser, u.username, u.password, u.names, u.lastnames,
                   u.code, u.rol, u.session, u.time_stamp, u.ip, u.sw_id,
                   u.sw_port, u.mac, r.rolname
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
def get_profesores_de_curso(idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT u.username, u.names, u.lastnames
            FROM inscripcion i
            JOIN user u ON i.user_iduser = u.iduser
            WHERE i.curso_idcurso = %s AND i.rol_id = 3
        """, (idcurso,))
        profesores = cursor.fetchall()
        cursor.close()
        conn.close()
        return profesores
    except Exception as e:
        print(f"DB error get_profesores_de_curso: {e}")
        return []


# ---------- CURSOS ----------
def get_cursos_usuario_por_rol(username, rol_id):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.idcurso, c.nombre, c.codigo, c.estado, c.puerto
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
        cursor.execute("SELECT idcurso, nombre, codigo,puerto, estado FROM curso")
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
def get_servidores_permitidos(idcurso, rol_id=None):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # Obtener puerto del curso
        cursor.execute("SELECT puerto FROM curso WHERE idcurso = %s", (idcurso,))
        curso = cursor.fetchone()
        cursor.close()
        conn.close()

        if not curso:
            print(f"No se encontró curso con ID {idcurso}")
            return []

        return [{
            "ip": "10.0.0.3",
            "puerto": curso["puerto"],
            "mac": "fa:16:3e:a7:e1:fb",
            "sw_id": "00:00:1a:74:72:3f:ef:44",
            "sw_port": 3
        }]
    except Exception as e:
        print(f"DB error servidores permitidos por curso: {e}")
        return []


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

        # 1. Eliminar inscripciones asociadas al curso
        cursor.execute("DELETE FROM inscripcion WHERE curso_idcurso = %s", (idcurso,))

        # 2. Eliminar curso
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
def eliminar_inscripcion_alumno(username, idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Obtener el ID del usuario
        cursor.execute("SELECT iduser FROM user WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]

        # Eliminar la inscripción como alumno (rol_id = 2)
        cursor.execute("""
            DELETE FROM inscripcion
            WHERE user_iduser = %s AND curso_idcurso = %s AND rol_id = 2
        """, (user_id, idcurso))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error eliminar inscripcion alumno: {e}")

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

def eliminar_inscripcion_profesor(username, idcurso):
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        # Obtener el ID del usuario
        cursor.execute("SELECT iduser FROM user WHERE username = %s", (username,))
        user_id = cursor.fetchone()[0]

        # Eliminar la inscripción solo si fue hecha como profesor (rol_id = 3)
        cursor.execute("""
            DELETE FROM inscripcion
            WHERE user_iduser = %s AND curso_idcurso = %s AND rol_id = 3
        """, (user_id, idcurso))

        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB error eliminar inscripcion profesor: {e}")

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

        # 1. Obtener ID del usuario
        cursor.execute("SELECT iduser FROM user WHERE username = %s", (username,))
        result = cursor.fetchone()
        if result:
            iduser = result[0]

            # 2. Eliminar inscripciones relacionadas
            cursor.execute("DELETE FROM inscripcion WHERE user_iduser = %s", (iduser,))

            # 3. Eliminar usuario
            cursor.execute("DELETE FROM user WHERE iduser = %s", (iduser,))

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


#Logout
def eliminar_flows_usuario(ip_usuario, mac_usuario):
    LIST_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/list/all/json"
    REMOVE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"

    try:
        response = requests.get(LIST_URL)
        response.raise_for_status()
        all_flows = response.json()

        for dpid, flow_list in all_flows.items():
            for flow_dict in flow_list:
                # Algunos controladores encapsulan flows con su nombre como clave
                for flow_name, flow in flow_dict.items():
                    match = flow.get("match", {})
                    eth_src = match.get("eth_src", "")
                    eth_dst = match.get("eth_dst", "")
                    ip_src = match.get("ipv4_src", "")
                    ip_dst = match.get("ipv4_dst", "")

                    if mac_usuario in (eth_src, eth_dst) or ip_usuario in (ip_src, ip_dst):
                        eliminar_flow(flow_name)
                        print(f"Eliminado flow: {flow_name}")
    except Exception as e:
        print(f"Error eliminando flows del usuario: {e}")


def eliminar_flow(flow_name):
    REMOVE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"
    try:
        response = requests.delete(REMOVE_URL, json={"name": flow_name})
        response.raise_for_status()
    except Exception as e:
        print(f"Error al eliminar flow {flow_name}: {e}")

def eliminar_flows_de_usuario_para_curso(username, idcurso):
    LIST_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/list/all/json"
    try:
        user = get_user_db(username)
        if not user:
            print(f"Usuario {username} no encontrado.")
            return

        servidores = get_servidores_permitidos(idcurso)

        response = requests.get(LIST_URL)
        response.raise_for_status()
        all_flows = response.json()

        for srv in servidores:
            base_name = f"{username}-{srv['ip']}-{srv['puerto']}"

            for dpid, flow_list in all_flows.items():
                for flow_dict in flow_list:
                    for flow_name in flow_dict:
                        if flow_name.startswith(base_name):
                            eliminar_flow(flow_name)
                            print(f"Eliminado flow del curso: {flow_name}")
    except Exception as e:
        print(f"Error eliminando flows del curso {idcurso} para {username}: {e}")

def agregar_flows_por_regla_de_rol(username):
    user = get_user_db(username)
    if not user:
        print(f"Usuario {username} no encontrado.")
        return

    ip_usuario = user['ip']
    mac_usuario = user['mac']
    sw_src = user['sw_id']
    port_src = user['sw_port']
    rol_id = user['rol']

    if not sw_src:
        print(f"No se encontró punto de conexión para {username}")
        return

    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)

        # ✅ Consulta reglas permitidas para este rol
        cursor.execute("""
            SELECT r.name, r.svr_ip, r.svr_port, r.svr_mac, r.sw_id, r.sw_port
            FROM rule r
            JOIN role_has_rule rr ON rr.rule_idrule = r.idrule
            WHERE rr.role_idrole = %s AND r.action = 'allow'
        """, (rol_id,))
        reglas = cursor.fetchall()

        cursor.close()
        conn.close()

        for regla in reglas:
            handlername = f"{username}-{regla['svr_ip']}-{regla['svr_port']}"

            flowUtils.crear_conexion(
                src_dpid=sw_src,
                src_port=port_src,
                dst_dpid=regla['sw_id'],
                dst_port=regla['sw_port'],
                ip_usuario=ip_usuario,
                ip_recurso=regla['svr_ip'],
                mac_usuario=mac_usuario,
                mac_recurso=regla['svr_mac'],
                port_recurso=regla['svr_port'],
                handlername=handlername
            )
            print(f"Regla aplicada: {handlername}")

    except Exception as e:
        print(f"Error aplicando reglas por rol: {e}")
