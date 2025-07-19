import re
import subprocess
import time

LOG_FILE = "/var/log/suricata/fast.log"
WHITELIST = {
    "192.168.201.200",
    "192.168.201.201",
    "192.168.201.202",
    "192.168.201.203",
    "192.168.201.204",
    "192.168.201.205"
}

blocked_ips = set()

RULES = [
    {
        "name": "Posible ataque ICMP flood",
        "msg": "Posible ataque ICMP flood",
        "regex": re.compile(r"Posible ataque ICMP flood.* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
    },
    {
        "name": "Escaneo SYN detectado",
        "msg": "Escaneo SYN detectado",
        "regex": re.compile(r"Escaneo SYN detectado.* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
    },
    {
        "name": "Posible ataque fuerza bruta SSH",
        "msg": "Posible ataque fuerza bruta SSH",
        "regex": re.compile(r"Posible ataque fuerza bruta SSH.* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
    },
    {
        "name": "Posible intento de ejecución remota (RCE)",
        "msg": "Posible intento de ejecución remota (RCE)",
        "regex": re.compile(r"Posible intento de ejecución remota \(RCE\).* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
    },
    {
        "name": "Posible UDP flood",
        "msg": "Posible UDP flood",
        "regex": re.compile(r"Posible UDP flood.* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
    },
{
    "name": "Ping de tamaño anómalo detectado",
    "msg": "Ping de tamaño anómalo detectado",
    "regex": re.compile(r"Ping de tamaño anómalo detectado.* (\d{1,3}(?:\.\d{1,3}){3}):\d+ ->")
}

]

def bloquear_ip(ip, reason):
    if ip in blocked_ips or ip in WHITELIST:
        return
    print(f"Bloqueando IP: {ip} por motivo: {reason}")
    try:
        subprocess.run(["sudo", "iptables", "-I", "INPUT", "-s", ip, "-j", "DROP"], check=True)
        blocked_ips.add(ip)
    except subprocess.CalledProcessError as e:
        print(f"Error al bloquear IP {ip}: {e}")

def seguir_log():
    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)  # Ir al final para solo leer nuevas líneas
        while True:
            linea = f.readline()
            if not linea:
                time.sleep(0.2)
                continue
            yield linea

def main():
    print("Iniciando monitor de Suricata para bloqueo automático...")
    for linea in seguir_log():
        for rule in RULES:
            if rule["msg"] in linea:
                match = rule["regex"].search(linea)
                if match:
                    ip_origen = match.group(1)
                    bloquear_ip(ip_origen, rule["name"])
                break  # No revisar más reglas para esta línea

if __name__ == "__main__":
    main()
