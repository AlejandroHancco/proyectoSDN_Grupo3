import requests

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher"
ALLOWED_PORT = 30000
CONTROLLER_DST_IP = "10.20.12.162"

def get_switches():
    url = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json"
    try:
        res = requests.get(url)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error al obtener switches: {e}")
        return []

def delete_all_flows():
    try:
        res = requests.get(f"{BASE_URL}/list/all/json")
        res.raise_for_status()
        data = res.json()
        for switch_flows in data.values():
            for flow_dict in switch_flows:
                for name in flow_dict.keys():
                    requests.delete(f"{BASE_URL}/json", json={"name": name})
    except Exception as e:
        print(f"Error al eliminar flows: {e}")

def add_flow(flow):
    try:
        res = requests.post(f"{BASE_URL}/json", json=flow)
        res.raise_for_status()
        print(f"[OK] Flow {flow['name']} agregado al switch {flow['switch']}")
    except Exception as e:
        print(f"[ERR] Flow {flow['name']}: {e}")

def main():
    delete_all_flows()

    switches = get_switches()
    if not switches:
        print("No hay switches conectados.")
        return

    for i, sw in enumerate(switches):
        dpid = sw["switchDPID"]

        # Permitir ARP (0x0806)
        add_flow({
            "switch": dpid,
            "name": f"allow_arp_{i}",
            "priority": 30000,
            "eth_type": "0x0806",  # Formato hexadecimal
            "active": True,
            "actions": "output=flood"  # Formato directo para acciones simples
        })

        # Permitir TCP destino puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_dst_{i}",
            "priority": 25000,
            "eth_type": "0x0800",  # IPv4
            "ip_proto": 6,         # TCP
            "tcp_dst": ALLOWED_PORT,
            "active": True,
            "actions": "output=flood"
        })

        # Permitir TCP origen puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_src_{i}",
            "priority": 25000,
            "eth_type": "0x0800",
            "ip_proto": 6,
            "tcp_src": ALLOWED_PORT,
            "active": True,
            "actions": "output=flood"
        })

        # Bloquear ICMP hacia controlador
        add_flow({
            "switch": dpid,
            "name": f"block_icmp_to_controller_{i}",
            "priority": 40000,  # Mayor prioridad que las reglas de permiso
            "eth_type": "0x0800",
            "ip_proto": 1,      # ICMP
            "ipv4_dst": CONTROLLER_DST_IP,
            "active": True,
            "actions": "drop"  # Acción explícita de descartar
        })

        # Bloquear todo IPv4 restante (prioridad más baja)
        add_flow({
            "switch": dpid,
            "name": f"block_all_ipv4_{i}",
            "priority": 1000,
            "eth_type": "0x0800",
            "active": True,
            "actions": "drop"
        })

if __name__ == "__main__":
    main()
