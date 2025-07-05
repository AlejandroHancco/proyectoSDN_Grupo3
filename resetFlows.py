import requests
import json

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080

CLEAR_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/clear"
ADD_FLOW_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"
SWITCHES_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json"

def get_switches():
    try:
        response = requests.get(SWITCHES_URL)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Error al obtener switches: {e}")
        return []

def clear_flows(switch_dpid):
    try:
        url = f"{CLEAR_URL}/{switch_dpid}/json"
        response = requests.get(url)
        response.raise_for_status()
        print(f"✅ Reglas limpiadas para switch {switch_dpid}")
    except Exception as e:
        print(f"❌ Error al limpiar reglas en {switch_dpid}: {e}")

def add_default_flow(switch_dpid):
    flow = {
        "switch": switch_dpid,
        "name": f"default-to-controller",
        "priority": "0",
        "eth_type": "0x0800",
        "active": "true",
        "actions": "output=controller"
    }
    try:
        response = requests.post(ADD_FLOW_URL, data=json.dumps(flow))
        response.raise_for_status()
        print(f"✅ Regla por defecto insertada en {switch_dpid}")
    except Exception as e:
        print(f"❌ Error al insertar regla en {switch_dpid}: {e}")

def main():
    switches = get_switches()
    if not switches:
        print("⚠️ No hay switches conectados")
        return

    for switch in switches:
        dpid = switch.get("switchDPID")
        if dpid:
            clear_flows(dpid)
            add_default_flow(dpid)

if __name__ == "__main__":
    main()
