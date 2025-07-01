# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for
from files import repository

app = Flask(__name__)
app.secret_key = "grupo3"

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
            session["usuario"] = usuario

            rol = usuario["rolname"].lower()

            if rol == "alumno":
                return redirect(url_for("panel_alumno"))
            elif rol == "profesor":
                return render_template("profesorPrincipal.html", usuario=usuario)
            elif rol == "administrador":
                return redirect(url_for("panel_admin"))
            elif rol == "invitado":
                return render_template("invitadoPrincipal.html", usuario=usuario)
            else:
                return f"Rol desconocido: {rol}", 403
        else:
            return render_template("login.html", error="Credenciales inválidas")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ---------- PANEL ADMIN ----------
@app.route("/admin")
def panel_admin():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]
    rol = usuario.get("rolname", "").lower()

    if rol != "administrador":
        return "Acceso no autorizado", 403

    usuarios = repository.get_all_usuarios(session["usuario"]["username"])
    cursos = repository.get_all_cursos()
    return render_template("adminPrincipal.html", usuario=usuario, usuarios=usuarios, cursos=cursos)

# ---------- PANEL ALUMNO ----------
@app.route("/panelAlumno")
def panel_alumno():
    if "usuario" not in session:
        return redirect(url_for("login"))

    usuario = session["usuario"]
    username = usuario["username"]

    cursos_inscritos = repository.get_cursos_alumno(username)
    all_cursos = repository.get_all_cursos()
    ids_inscritos = {c["idcurso"] for c in cursos_inscritos}
    cursos_disponibles = [c for c in all_cursos if c["estado"] == "activo" and c["idcurso"] not in ids_inscritos]

    return render_template("alumnoPrincipal.html", usuario=usuario,
                           cursos_inscritos=cursos_inscritos,
                           cursos_disponibles=cursos_disponibles)

@app.route("/inscribirse/<int:idcurso>")
def inscribirse(idcurso):
    if "usuario" not in session:
        return redirect(url_for("login"))

    username = session["usuario"]["username"]
    try:
        repository.inscribir_usuario_en_curso(username, idcurso)
    except Exception as e:
        print(f"Error inscribiendo en curso: {e}")
    return redirect(url_for("panel_alumno"))

# ---------- CURSOS ----------
@app.route("/editar_curso/<int:idcurso>", methods=["GET", "POST"])
def editar_curso(idcurso):
    if request.method == "POST":
        nombre = request.form.get("nombre")
        estado = request.form.get("estado")
        repository.actualizar_curso(idcurso, nombre, estado)
        return redirect(url_for("panel_admin"))
    curso = repository.get_curso_por_id(idcurso)
    return render_template("editarCurso.html", curso=curso)

@app.route("/eliminar_curso/<int:idcurso>")
def eliminar_curso(idcurso):
    repository.eliminar_curso(idcurso)
    return redirect(url_for("panel_admin"))

@app.route("/crear_curso", methods=["GET", "POST"])
def crear_curso():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        estado = request.form.get("estado")
        repository.crear_curso(nombre, estado)
        return redirect(url_for("panel_admin"))
    return render_template("editarCurso.html", curso=None)

# ---------- USUARIOS ----------
@app.route("/editar_usuario/<username>", methods=["GET", "POST"])
def editar_usuario(username):
    if request.method == "POST":
        names = request.form.get("names")
        lastnames = request.form.get("lastnames")
        rol = int(request.form.get("rol"))
        repository.actualizar_usuario(username, names, lastnames, rol)
        return redirect(url_for("panel_admin"))
    usuario = repository.get_user_db(username)
    roles = repository.get_all_roles()
    return render_template("editarUsuario.html", usuario=usuario, roles=roles)

@app.route("/eliminar_usuario/<username>")
def eliminar_usuario(username):
    repository.eliminar_usuario(username)
    return redirect(url_for("panel_admin"))

@app.route("/crear_usuario", methods=["GET", "POST"])
def crear_usuario():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        names = request.form.get("names")
        lastnames = request.form.get("lastnames")
        rol = int(request.form.get("rol"))
        repository.crear_usuario(username, password, names, lastnames, rol)
        return redirect(url_for("panel_admin"))
    roles = repository.get_all_roles()
    return render_template("editarUsuario.html", usuario=None, roles=roles)

# ---------- MAIN ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
