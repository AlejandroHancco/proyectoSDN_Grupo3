# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for
from functools import wraps
from files import repository
from files import flowUtils
app = Flask(__name__)
app.secret_key = "grupo3"

# ---------- DECORADORES ----------
#Funciona para que validen los roles a modo de html
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if "usuario" not in session:
                return redirect(url_for("login"))
            user_rol = session["usuario"]["rolname"].lower()
            if user_rol not in [r.lower() for r in roles]:
                return "Acceso no autorizado", 403
            return f(*args, **kwargs)
        return wrapped
    return decorator

# ---------- LOGIN ----------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if repository.authenticate_user(username, password):
            usuario = repository.get_user_db(username)
            if not usuario:
                return "Usuario no encontrado en BD", 404
            repository.actualizar_timestamp_login(username)
            session["usuario"] = usuario
            repository.agregar_flows_para_usuario(username)
            rol = usuario["rolname"].lower()
            return redirect(url_for(f"panel_{rol}"))
        else:
            return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    usuario = session.get("usuario")
    if usuario:
        ip_usuario = usuario.get("ip")
        mac_usuario = usuario.get("mac")
        if ip_usuario and mac_usuario:
            repository.eliminar_flows_usuario(ip_usuario, mac_usuario)
    session.clear()
    return redirect(url_for("login"))


# ---------- PANEL ADMIN ----------
@app.route("/panel_administrador")
@role_required("administrador")
def panel_administrador():
    usuario = session["usuario"]
    usuarios = repository.get_all_usuarios(usuario["username"])
    cursos = repository.get_all_cursos()
    return render_template("adminPrincipal.html", usuario=usuario, usuarios=usuarios, cursos=cursos)

# ---------- PANEL ALUMNO ----------
@app.route("/panel_alumno")
@role_required("alumno")
def panel_alumno():
    usuario = session["usuario"]
    username = usuario["username"]
    
    cursos_inscritos = repository.get_cursos_usuario_por_rol(username, 2)
    all_cursos = repository.get_all_cursos()
    ids_inscritos = {c["idcurso"] for c in cursos_inscritos}

    cursos_disponibles = [c for c in all_cursos if c["estado"] == "activo" and c["idcurso"] not in ids_inscritos]

    # Agrega profesores a todos los cursos disponibles
    for curso in cursos_disponibles:
        curso["profesores"] = repository.get_profesores_de_curso(curso["idcurso"])

    # También agrega profesores a los cursos inscritos
    for curso in cursos_inscritos:
        curso["profesores"] = repository.get_profesores_de_curso(curso["idcurso"])

    return render_template("alumnoPrincipal.html",
                           usuario=usuario,
                           cursos_inscritos=cursos_inscritos,
                           cursos_disponibles=cursos_disponibles)


@app.route("/inscribirse/<int:idcurso>")
@role_required("alumno")
def inscribirse(idcurso):
    username = session["usuario"]["username"]
    try:
        repository.inscribir_usuario_en_curso(username, idcurso,rol_id=2)
        repository.agregar_flows_para_usuario(username)
    except Exception as e:
        print(f"Error inscribiendo en curso: {e}")
    return redirect(url_for("panel_alumno"))

# ---------- PANEL INVITADO ----------
@app.route("/panel_invitado")
@role_required("invitado")
def panel_invitado():
    usuario = session["usuario"]
    all_cursos = repository.get_all_cursos()
    cursos_disponibles = [c for c in all_cursos if c["estado"] == "activo"]
    return render_template("invitadoPrincipal.html", usuario=usuario, cursos_disponibles=cursos_disponibles)

# ---------- PANEL PROFESOR ----------
@app.route("/panel_profesor")
@role_required("profesor")
def panel_profesor():
    usuario = session["usuario"]
    username = usuario["username"]
    
    cursos = repository.get_cursos_usuario_por_rol(username,3)
    
    cursos_con_inscritos = []
    for curso in cursos:
        inscritos = repository.get_inscritos_en_curso(curso["idcurso"])
        cursos_con_inscritos.append({
            "curso": curso,
            "inscritos": inscritos
        })
    
    return render_template("profesorPrincipal.html", usuario=usuario, cursos_info=cursos_con_inscritos)

# ---------- CURSOS ----------
@app.route("/editar_curso/<int:idcurso>", methods=["GET", "POST"])
@role_required("administrador")
def editar_curso(idcurso):
    if request.method == "POST":
        nombre = request.form.get("nombre")
        estado = request.form.get("estado")
        codigo = request.form.get("codigo")  # ← Agregado
        repository.actualizar_curso(idcurso, nombre, estado, codigo)  # ← Modificado
        return redirect(url_for("panel_administrador"))
    curso = repository.get_curso_por_id(idcurso)
    return render_template("editarCurso.html", curso=curso)

@app.route("/eliminar_curso/<int:idcurso>")
@role_required("administrador")
def eliminar_curso(idcurso):
    repository.eliminar_curso(idcurso)
    return redirect(url_for("panel_administrador"))

@app.route("/crear_curso", methods=["GET", "POST"])
@role_required("administrador")
def crear_curso():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        estado = request.form.get("estado")
        codigo = request.form.get("codigo")  # ← Agregado
        repository.crear_curso(nombre, estado, codigo)  # ← Modificado
        return redirect(url_for("panel_administrador"))
    return render_template("editarCurso.html", curso=None)

# ---------- USUARIOS ----------
@app.route("/editar_usuario/<username>", methods=["GET", "POST"])
@role_required("administrador")
def editar_usuario(username):
    if request.method == "POST":
        names = request.form.get("names")
        lastnames = request.form.get("lastnames")
        rol = int(request.form.get("rol"))
        repository.actualizar_usuario(username, names, lastnames, rol)
        return redirect(url_for("panel_administrador"))
    usuario = repository.get_user_db(username)
    roles = repository.get_all_roles()
    return render_template("editarUsuario.html", usuario=usuario, roles=roles)

@app.route("/eliminar_usuario/<username>")
@role_required("administrador")
def eliminar_usuario(username):
    repository.eliminar_usuario(username)
    return redirect(url_for("panel_administrador"))

@app.route("/asignar_curso/<username>", methods=["GET", "POST"])
@role_required("administrador")
def asignar_curso(username):
    profesor = repository.get_user_db(username)
    if not profesor or profesor["rolname"].lower() != "profesor":
        return "No es un profesor válido", 400

    if request.method == "POST":
        idcurso = request.form.get("idcurso")
        try:
            repository.inscribir_usuario_en_curso(username, idcurso, rol_id=3)  # Rol 3 = Profesor
        except Exception as e:
            print(f"Error asignando curso a profesor: {e}")
        return redirect(url_for("asignar_curso", username=username))

    cursos_asignados = repository.get_cursos_usuario_por_rol(username, 3)
    all_cursos = repository.get_all_cursos()
    ids_asignados = {c["idcurso"] for c in cursos_asignados}
    cursos_disponibles = [c for c in all_cursos if c["estado"] == "activo" and c["idcurso"] not in ids_asignados]

    return render_template("asignarCurso.html",
                       profesor=profesor,
                       cursos_asignados=cursos_asignados,
                       cursos_disponibles=cursos_disponibles)


@app.route("/desinscribirse/<int:idcurso>")
@role_required("alumno")
def desinscribirse(idcurso):
    username = session["usuario"]["username"]
    try:
        # 1. Eliminar la inscripción
        repository.eliminar_inscripcion_alumno(username, idcurso)

        # 2. Eliminar los flows generados para ese curso en particular
        repository.eliminar_flows_de_usuario_para_curso(username, idcurso)

        # 3. (Opcional) Regenerar todos los flows restantes
        repository.agregar_flows_para_usuario(username)
    except Exception as e:
        print(f"Error al desinscribirse del curso: {e}")
    return redirect(url_for("panel_alumno"))


@app.route("/desasignar_curso/<username>/<int:idcurso>")
@role_required("administrador")
def desasignar_curso(username, idcurso):
    try:
        repository.eliminar_inscripcion_profesor(username, idcurso)
    except Exception as e:
        print(f"Error al desasignar curso: {e}")
    return redirect(url_for("asignar_curso", username=username))



@app.route("/crear_usuario", methods=["GET", "POST"])
@role_required("administrador")
def crear_usuario():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        names = request.form.get("names")
        lastnames = request.form.get("lastnames")
        rol = int(request.form.get("rol"))
        repository.crear_usuario(username, password, names, lastnames, rol)
        return redirect(url_for("panel_administrador"))
    roles = repository.get_all_roles()
    return render_template("editarUsuario.html", usuario=None, roles=roles)

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
