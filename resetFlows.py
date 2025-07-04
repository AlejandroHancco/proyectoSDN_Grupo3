import requests
import json
from requests.exceptions import RequestException

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowentrypusher"
ALLOWED_PORT = 30000
CONTROLLER_DST_IP = "10.20.12.162"

def delete_all_flows():
    """Elimina todas las reglas existentes (compatible con Floodlight 1.2)"""
    try:
        # Obtener lista de flujos
        response = requests.get(f"{BASE_URL}/list/all/json")
        if response.status_code == 200:
            flows = response.json()
            for switch_flows in flows.values():
                for flow in switch_flows:
                    for flow_name in flow.keys():
                        # Eliminar cada flujo individualmente
                        delete_response = requests.delete(
                            f"{BASE_URL}/json",
                            data=json.dumps({"name": flow_name}),
                            headers={"Content-Type": "application/json"}
                        )
                        if delete_response.status_code != 200:
                            print(f"Error eliminando flujo {flow_name}: {delete_response.text}")
        print("Flujos existentes eliminados correctamente")
    except RequestException as e:
        print(f"Error de conexión: {str(e)}")

def get_switches():
    """Obtiene switches conectados (compatible con Floodlight 1.2)"""
    try:
        response = requests.get(f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/core/controller/switches/json")
        if response.status_code == 200:
            return response.json()
        print(f"Error obteniendo switches: {response.text}")
        return []
    except RequestException as e:
        print(f"Error de conexión: {str(e)}")
        return []

def add_flow(switch_dpid, flow_name, flow_data):
    """Agrega un flujo (adaptado para Floodlight 1.2)"""
    try:
        # Estructura básica requerida por Floodlight 1.2
        flow = {
            "switch": switch_dpid,
            "name": flow_name,
            "cookie": "0",
            "priority": "32768",
            "active": "true",
            "actions": ""
        }
        
        # Actualizar con los datos específicos del flujo
        flow.update(flow_data)
        
        # Enviar el flujo al controlador
        response = requests.post(
            f"{BASE_URL}/json",
            data=json.dumps(flow),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"Flujo {flow_name} agregado correctamente en {switch_dpid}")
        else:
            print(f"Error agregando flujo {flow_name}: {response.text}")
    except RequestException as e:
        print(f"Error de conexión: {str(e)}")

def configure_flows():
    """Configura los flujos compatibles con Floodlight 1.2"""
    print("Iniciando configuración para Floodlight 1.2...")
    
    # 1. Limpiar flujos existentes
    delete_all_flows()
    
    # 2. Obtener switches conectados
    switches = get_switches()
    if not switches:
        print("No se encontraron switches conectados")
        return
    
    # 3. Configurar flujos en cada switch
    for switch in switches:
        dpid = switch["switchDPID"]
        print(f"\nConfigurando switch {dpid}")
        
        # Flujo 1: Permitir ARP (prioridad más alta)
        add_flow(dpid, f"allow_arp_{dpid[-2:]}", {
            "priority": "40000",
            "eth_type": "0x0806",
            "actions": "output=flood"
        })
        
        # Flujo 2: Permitir TCP destino 30000
        add_flow(dpid, f"allow_tcp_dst_{dpid[-2:]}", {
            "priority": "35000",
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tp_dst": str(ALLOWED_PORT),
            "actions": "output=flood"
        })
        
        # Flujo 3: Permitir TCP origen 30000
        add_flow(dpid, f"allow_tcp_src_{dpid[-2:]}", {
            "priority": "35000",
            "eth_type": "0x0800",
            "ip_proto": "6",
            "tp_src": str(ALLOWED_PORT),
            "actions": "output=flood"
        })
        
        # Flujo 4: Bloquear ICMP al controlador
        add_flow(dpid, f"block_icmp_{dpid[-2:]}", {
            "priority": "30000",
            "eth_type": "0x0800",
            "ip_proto": "1",
            "nw_dst": CONTROLLER_DST_IP,
            "actions": ""
        })
        
        # Flujo 5: Bloquear todo IPv4 restante (prioridad baja)
        add_flow(dpid, f"block_all_ipv4_{dpid[-2:]}", {
            "priority": "1000",
            "eth_type": "0x0800",
            "actions": ""
        })

if __name__ == "__main__":
    configure_flows()
    print("\nConfiguración completada")
