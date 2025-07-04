import requests
import json

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
ADD_FLOW_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher/json"
ALLOWED_PORT = 30000

def get_switches():
    url = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al obtener la lista de switches: {e}")
        return []

def add_flow(flow):
    try:
        response = requests.post(ADD_FLOW_URL, json=flow)
        response.raise_for_status()
        print(f"Flow {flow['name']} agregado al switch {flow['switch']}")
    except requests.exceptions.RequestException as e:
        print(f"Error al agregar flow {flow['name']}: {e}")

def main():
    switches = get_switches()
    if not switches:
        print("No se encontraron switches conectados.")
        return

    for i, switch in enumerate(switches):
        dpid = switch.get("switchDPID")
        if not dpid:
            continue

        # Permitir tráfico hacia puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_dst_{ALLOWED_PORT}_{i}",
            "priority": "40000",
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tcp_dst": str(ALLOWED_PORT),
            "active": "true",
            "actions": "output=flood"
        })

        # Permitir tráfico desde puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_src_{ALLOWED_PORT}_{i}",
            "priority": "40000",
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tcp_src": str(ALLOWED_PORT),
            "active": "true",
            "actions": "output=flood"
        })

        # Permitir ARP
        add_flow({
            "switch": dpid,
            "name": f"allow_arp_{i}",
            "priority": "30000",
            "eth_type": "0x0806",
            "active": "true",
            "actions": "output=flood"
        })

        # Bloquear el resto del tráfico IPv4
        add_flow({
            "switch": dpid,
            "name": f"block_all_ipv4_{i}",
            "priority": "1000",
            "eth_type": "0x0800",
            "active": "true",
            "actions": ""
        })

if __name__ == "__main__":
    main()
