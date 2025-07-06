
# freeRadiusUtil.py
import subprocess

FREERADIUS_USERS_FILE = "/etc/freeradius/3.0/users"

def agregar_a_freeradius(username, password):
    with open(FREERADIUS_USERS_FILE, "a") as f:
        f.write(f"\n{username}\tCleartext-Password := \"{password}\"\n")
    reiniciar_freeradius()

def actualizar_password(username, password):
    lines = open(FREERADIUS_USERS_FILE).read().splitlines()
    with open(FREERADIUS_USERS_FILE, "w") as f:
        skip = False
        for line in lines:
            if skip:
                skip = False
                continue
            if line.startswith(username + "\t"):
                f.write(f"{username}\tCleartext-Password := \"{password}\"\n")
                skip = True
            else:
                f.write(line + "\n")
    reiniciar_freeradius()

def eliminar_de_freeradius(username):
    lines = open(FREERADIUS_USERS_FILE).read().splitlines()
    with open(FREERADIUS_USERS_FILE, "w") as f:
        skip = False
        for line in lines:
            if skip:
                skip = False
                continue
            if line.startswith(username + "\t"):
                skip = True
            else:
                f.write(line + "\n")
    reiniciar_freeradius()

def reiniciar_freeradius():
    try:
        subprocess.run(["sudo", "systemctl", "restart", "freeradius"], check=True)
        print("FreeRADIUS reiniciado correctamente.")
    except subprocess.CalledProcessError as e:
        print("Error reiniciando FreeRADIUS:", e)
