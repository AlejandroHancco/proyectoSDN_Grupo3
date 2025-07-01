# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, session, redirect, url_for
from files import repository

app = Flask(__name__)
app.secret_key = "grupo3"

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
                cursos = repository.get_cursos_alumno(username)
                return render_template("cursos.html", usuario=usuario, cursos=cursos)
            elif rol == "profesor":
                return render_template("profesorPrincipal.html", usuario=usuario)
            elif rol == "admin":
                usuarios = repository.get_all_usuarios()
                cursos = repository.get_all_cursos()
                return render_template("adminPrincipal.html", usuario=usuario, usuarios=usuarios, cursos=cursos)
            elif rol == "invitado":
                return render_template("invitadoPrincipal.html", usuario=usuario)
            else:
                return f"Rol desconocido: {rol}", 403
        else:
            return "Credenciales inválidas", 401
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# Editar curso
@app.route("/editar_curso/<int:idcurso>", methods=["GET", "POST"])
def editar_curso(idcurso):
    if request.method == "POST":
        nombre = request.form.get("nombre")
        estado = request.form.get("estado")
        repository.actualizar_curso(idcurso, nombre, estado)
        return redirect(url_for("login"))  # Redirige a login o a donde veas el admin
    curso = repository.get_curso_por_id(idcurso)
    return render_template("editarCurso.html", curso=curso)

# Eliminar curso
@app.route("/eliminar_curso/<int:idcurso>")
def eliminar_curso(idcurso):
    repository.eliminar_curso(idcurso)
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=30000, debug=True)
