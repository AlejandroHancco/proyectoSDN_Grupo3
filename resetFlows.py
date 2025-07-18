#Este script sirve para borrar todos los flow entries de los switches y dejar los default
#Es decir, solo se permiten reglas para que hagan reconocimiento por mac y por FloodLight, no hay ping entre hosts
#Nota: Nunca habrá ping entre hosts solo el acceso por el puerto de los cursos que se implementan automaticamente cada vez que se loguea 
import requests
# Dirección IP del controlador Floodlight
CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080

# IP y puerto del host permitido (servidor login)
DEST_IP = "00:00:1a:74:72:3f:ef:44"
DEST_TCP_PORT = "9000"
OUTPUT_PORT = "3"  

# URLs del controlador
SWITCHES_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json"
CLEAR_FLOW_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/clear"
ADD_FLOW_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"

def get_switches():
    try:
        response = requests.get(SWITCHES_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error al obtener switches: {e}")
        return []

def clear_flows(dpid):
    try:
        url = f"{CLEAR_FLOW_URL}/{dpid}/json"
        response = requests.get(url)
        response.raise_for_status()
        print(f"Flows eliminados para switch {dpid}")
    except Exception as e:
        print(f"Error limpiando flows de {dpid}: {e}")

def add_discovery_and_allowed_flows(dpid):
    flows = [
        {
            "switch": dpid,
            "name": f"{dpid}-arp",
            "priority": "500",
            "eth_type": "0x0806",
            "active": "true",
            "actions": "output=controller"
        },
        {
            "switch": dpid,
            "name": f"{dpid}-lldp",
            "priority": "500",
            "eth_type": "0x88cc",
            "active": "true",
            "actions": "output=controller"
        },
        {
            "switch": dpid,
            "name": f"{dpid}-tcp-to-192.168.101.105-8000",
            "priority": "400",
            "eth_type": "0x0800",      
            "ip_proto": "6",          
            "ipv4_dst": DEST_IP,
            "tcp_dst": DEST_TCP_PORT,
            "active": "true",
            "actions": f"output={OUTPUT_PORT}"
        }
    ]

    for flow in flows:
        try:
            response = requests.post(ADD_FLOW_URL, json=flow)
            response.raise_for_status()
            print(f"Flow agregado en {dpid}: {flow['name']}")
        except Exception as e:
            print(f"Error agregando flow en {dpid}: {e}")

def main():
    switches = get_switches()
    if not switches:
        print("ALERTA: No hay switches conectados al controlador.")
        return

    for sw in switches:
        dpid = sw.get("switchDPID")
        if dpid:
            clear_flows(dpid)
            add_discovery_and_allowed_flows(dpid)

if __name__ == "__main__":
    main()

