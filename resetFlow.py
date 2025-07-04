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
        print(f"[ERROR] No se pudo obtener switches: {e}")
        return []

def delete_all_flows():
    print("[INFO] Eliminando todos los flows existentes...")
    try:
        res = requests.get(f"{BASE_URL}/list/all/json")
        res.raise_for_status()
        data = res.json()

        for switch, switch_flows in data.items():
            for flow_dict in switch_flows:
                for name in flow_dict:
                    delete_response = requests.delete(f"{BASE_URL}/json", json={"name": name})
                    if delete_response.ok:
                        print(f"[OK] Flow eliminado: {name}")
                    else:
                        print(f"[WARN] Falló eliminar {name}: {delete_response.status_code}")
    except Exception as e:
        print(f"[ERROR] Error al eliminar flows: {e}")

def add_flow(flow):
    try:
        res = requests.post(f"{BASE_URL}/json", json=flow)
        res.raise_for_status()
        print(f"[OK] Flow agregado: {flow['name']} (switch {flow['switch']})")
    except Exception as e:
        print(f"[ERROR] No se pudo agregar {flow['name']} ({flow['switch']}): {e}")

def main():
    delete_all_flows()

    switches = get_switches()
    if not switches:
        print("[ERROR] No hay switches conectados.")
        return

    for i, sw in enumerate(switches):
        dpid = sw["switchDPID"]

        # Permitir ARP
        add_flow({
            "switch": dpid,
            "name": f"allow_arp_{i}",
            "priority": "30000",
            "active": "true",
            "match": {
                "eth_type": "0x0806"
            },
            "instructions": {
                "instruction_apply_actions": {
                    "actions": "output=flood"
                }
            }
        })

        # Permitir TCP hacia puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_dst_{i}",
            "priority": "25000",
            "active": "true",
            "match": {
                "eth_type": "0x0800",
                "ip_proto": "0x6",
                "tcp_dst": str(ALLOWED_PORT)
            },
            "instructions": {
                "instruction_apply_actions": {
                    "actions": "output=flood"
                }
            }
        })

        # Permitir TCP desde puerto 30000
        add_flow({
            "switch": dpid,
            "name": f"allow_tcp_src_{i}",
            "priority": "25000",
            "active": "true",
            "match": {
                "eth_type": "0x0800",
                "ip_proto": "0x6",
                "tcp_src": str(ALLOWED_PORT)
            },
            "instructions": {
                "instruction_apply_actions": {
                    "actions": "output=flood"
                }
            }
        })

        # Bloquear ICMP hacia el controlador
        add_flow({
            "switch": dpid,
            "name": f"block_icmp_to_controller_{i}",
            "priority": "20000",
            "active": "true",
            "match": {
                "eth_type": "0x0800",
                "ip_proto": "0x1",
                "ipv4_dst": CONTROLLER_DST_IP
            },
            "instructions": {
                "none": "drop"
            }
        })

        # Bloquear todo IPv4 restante
        add_flow({
            "switch": dpid,
            "name": f"block_all_ipv4_{i}",
            "priority": "1000",
            "active": "true",
            "match": {
                "eth_type": "0x0800"
            },
            "instructions": {
                "none": "drop"
            }
        })

if __name__ == "__main__":
    main()
