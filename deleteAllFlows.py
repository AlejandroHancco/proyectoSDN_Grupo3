# Borra todos los flows en caso resetFlows falle
import requests

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm"

def get_all_flows():
    print("[INFO] Obteniendo flows actuales...")
    try:
        response = requests.get(f"{BASE_URL}/staticflowpusher/list/all/json")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERR] Error conectando a Floodlight: {e}")
        return {}

def delete_flow(flow_name):
    try:
        data = {"name": flow_name}
        response = requests.delete(f"{BASE_URL}/staticflowpusher/json", json=data)
        if response.status_code == 200:
            print(f"[OK] Deleted {flow_name}")
        else:
            print(f"[ERR] Falló eliminación de {flow_name}: {response.status_code}")
    except Exception as e:
        print(f"[ERR] Error al eliminar {flow_name}: {e}")

def get_switches():
    try:
        response = requests.get(f"{BASE_URL}/core/controller/switches/json")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"[ERR] No se pudo obtener switches: {e}")
        return []

def insert_default_flow(switch_dpid):
    default_flow = {
        "switch": switch_dpid,
        "name": f"default_ctrl_{switch_dpid[-2:]}",
        "priority": 0,
        "active": True,
        "actions": "output=controller"
    }
    try:
        response = requests.post(f"{BASE_URL}/staticflowpusher/json", json=default_flow)
        if response.status_code == 200:
            print(f"[OK] Default flow inserted en {switch_dpid}")
        else:
            print(f"[ERR] No se pudo insertar default flow en {switch_dpid}: {response.text}")
    except Exception as e:
        print(f"[ERR] Error al insertar default flow en {switch_dpid}: {e}")

def delete_all_flows():
    all_flows = get_all_flows()

    for switch, flow_list in all_flows.items():
        for flow_entry in flow_list:
            for flow_name in flow_entry.keys():
                delete_flow(flow_name)

    # print("[INFO] Reinserción de reglas default hacia el controller...")

    # switches = get_switches()
    """
    for sw in switches:
        try:
            dpid = sw["switchDPID"]
            insert_default_flow(dpid)
        except KeyError:
            print(f"[ERR] No se encontró 'switchDPID' en {sw}")
        except Exception as e:
            print(f"[ERR] Error inesperado con switch: {e}")
    """

if __name__ == "__main__":
    delete_all_flows()
