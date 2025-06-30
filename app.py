# -*- coding: utf-8 -*-
from flask import Flask, render_template, request
from pyrad.client import Client
from pyrad.dictionary import Dictionary
from pyrad.packet import AccessRequest, AccessAccept

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
DICT_PATH = "dictionary"  # Asegúrate que este archivo existe

client = Client(server=RADIUS_SERVER, secret=SECRET, dict=Dictionary(DICT_PATH))
client.AuthPort = RADIUS_PORT

# ----------------------------
# -- Ruta de login principal --
# ----------------------------
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
                return "✅ Login exitoso (Access-Accept recibido)"
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
