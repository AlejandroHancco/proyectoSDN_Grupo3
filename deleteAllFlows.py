import requests

CONTROLLER_IP = "127.0.0.1"  # Cambia si tu controlador no está en localhost
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}"

FLOW_PUSH_URL = f"{BASE_URL}/wm/staticflowpusher/json"
GET_SWITCHES_URL = f"{BASE_URL}/wm/core/controller/switches/json"
LIST_FLOWS_URL = f"{BASE_URL}/wm/staticflowpusher/list/all/json"


def get_switches():
    try:
        res = requests.get(GET_SWITCHES_URL)
        res.raise_for_status()
        return [sw["dpid"] for sw in res.json()]
    except Exception as e:
        print(f"[ERR] No se pudo obtener switches: {e}")
        return []


def get_all_flows():
    try:
        res = requests.get(LIST_FLOWS_URL)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"[ERR] No se pudo obtener flows: {e}")
        return {}


def delete_flow(flow_name):
    try:
        res = requests.delete(FLOW_PUSH_URL, json={"name": flow_name})
        if res.status_code == 200:
            print(f"[OK] Deleted {flow_name}")
        else:
            print(f"[ERR] Al borrar {flow_name}: {res.text}")
    except Exception as e:
        print(f"[ERR] Exception al borrar flow {flow_name}: {e}")


def add_controller_flow(switch_dpid):
    flow = {
        "switch": switch_dpid,
        "name": f"to_controller_{switch_dpid[-4:]}",
        "priority": 0,
        "active": True,
        "actions": "output=controller"
    }
    try:
        res = requests.post(FLOW_PUSH_URL, json=flow)
        if res.status_code == 200:
            print(f"[OK] Flow to controller insertado en {switch_dpid}")
        else:
            print(f"[ERR] Insertar flow en {switch_dpid}: {res.text}")
    except Exception as e:
        print(f"[ERR] Error insertando default flow en {switch_dpid}: {e}")


def reset_all_flows():
    print("[INFO] Obteniendo flows actuales...")
    flows = get_all_flows()
    for switch_dpid, flow_list in flows.items():
        for flow_entry in flow_list:
            for flow_name in flow_entry.keys():
                delete_flow(flow_name)

    print("[INFO] Reinserción de reglas default hacia el controller...")
    switches = get_switches()
    for dpid in switches:
        add_controller_flow(dpid)


if __name__ == "__main__":
    reset_all_flows()
