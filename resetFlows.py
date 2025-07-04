import requests
import json

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher"
ALLOWED_PORT = 30000
CONTROLLER_DST_IP = "10.20.12.162"

def delete_all_flows():
    """Elimina todas las reglas existentes en todos los switches"""
    try:
        response = requests.get(f"{BASE_URL}/list/all/json")
        if response.status_code == 200:
            flows = response.json()
            for switch in flows.values():
                for flow in switch:
                    for flow_name in flow.keys():
                        requests.delete(f"{BASE_URL}/json", json={"name": flow_name})
        print("Todas las reglas existentes han sido eliminadas")
    except Exception as e:
        print(f"Error al eliminar flujos: {e}")

def get_switches():
    """Obtiene la lista de switches conectados al controlador"""
    try:
        response = requests.get(f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json")
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error al obtener switches: {e}")
        return []

def push_flow(switch_dpid, flow_name, flow_data):
    """Envía una regla de flujo a un switch específico"""
    try:
        flow_data.update({
            "switch": switch_dpid,
            "name": flow_name
        })
        response = requests.post(
            f"{BASE_URL}/json",
            headers={"Content-Type": "application/json"},
            data=json.dumps(flow_data)
        )
        if response.status_code == 200:
            print(f"Regla {flow_name} agregada correctamente al switch {switch_dpid}")
        else:
            print(f"Error al agregar regla {flow_name}: {response.text}")
    except Exception as e:
        print(f"Error al enviar regla {flow_name}: {e}")

def configure_flows():
    """Configura todas las reglas OpenFlow en los switches conectados"""
    delete_all_flows()
    switches = get_switches()
    
    if not switches:
        print("No se encontraron switches conectados")
        return

    for switch in switches:
        dpid = switch["switchDPID"]
        print(f"\nConfigurando reglas en el switch {dpid}")

        # 1. Permitir tráfico ARP (prioridad más alta)
        push_flow(dpid, f"allow_arp_{dpid[-2:]}", {
            "priority": 40000,
            "eth_type": "0x0806",
            "actions": "output=flood"
        })

        # 2. Permitir TCP destino puerto 30000
        push_flow(dpid, f"allow_tcp_dst_{dpid[-2:]}", {
            "priority": 35000,
            "eth_type": "0x0800",
            "ip_proto": 6,
            "tcp_dst": ALLOWED_PORT,
            "actions": "output=flood"
        })

        # 3. Permitir TCP origen puerto 30000
        push_flow(dpid, f"allow_tcp_src_{dpid[-2:]}", {
            "priority": 35000,
            "eth_type": "0x0800",
            "ip_proto": 6,
            "tcp_src": ALLOWED_PORT,
            "actions": "output=flood"
        })

        # 4. Bloquear ICMP hacia el controlador
        push_flow(dpid, f"block_icmp_to_controller_{dpid[-2:]}", {
            "priority": 30000,
            "eth_type": "0x0800",
            "ip_proto": 1,
            "ipv4_dst": CONTROLLER_DST_IP,
            "actions": "drop"
        })

        # 5. Bloquear todo el tráfico IPv4 restante (prioridad más baja)
        push_flow(dpid, f"block_all_ipv4_{dpid[-2:]}", {
            "priority": 1000,
            "eth_type": "0x0800",
            "actions": "drop"
        })

if __name__ == "__main__":
    print("Iniciando configuración de reglas OpenFlow...")
    configure_flows()
    print("\nConfiguración completada")
