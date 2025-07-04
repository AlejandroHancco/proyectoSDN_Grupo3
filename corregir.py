import requests

CONTROLLER_IP = "127.0.0.1"
CONTROLLER_PORT = 8080
BASE_URL = f"http://{CONTROLLER_IP}:{CONTROLLER_PORT}/wm/staticflowpusher"

def fix_eth_type(match_dict):
    # Corrige el eth_type: de "0x0x800" o "0x0x806" a entero decimal
    eth_type = match_dict.get("eth_type", None)
    if eth_type is not None:
        if isinstance(eth_type, str):
            # limpiar string y convertir
            if "0x0x800" in eth_type:
                match_dict["eth_type"] = 2048
            elif "0x0x806" in eth_type:
                match_dict["eth_type"] = 2054
            else:
                # intenta convertir hex a int si tiene 0x solo una vez
                try:
                    if eth_type.startswith("0x"):
                        match_dict["eth_type"] = int(eth_type, 16)
                except:
                    pass
    return match_dict

def get_all_flows():
    url = f"{BASE_URL}/list/all/json"
    r = requests.get(url)
    r.raise_for_status()
    return r.json()

def delete_flow(name):
    url = f"{BASE_URL}/json"
    r = requests.delete(url, json={"name": name})
    r.raise_for_status()

def add_flow(flow):
    url = f"{BASE_URL}/json"
    r = requests.post(url, json=flow)
    r.raise_for_status()

def main():
    flows = get_all_flows()

    for switch, flow_list in flows.items():
        for flow_dict in flow_list:
            for flow_name, flow in flow_dict.items():
                print(f"Procesando flow {flow_name} en switch {switch}")

                # Arreglar eth_type en el match
                if "match" in flow:
                    flow["match"] = fix_eth_type(flow["match"])

                # Eliminar flow original
                delete_flow(flow_name)
                print(f"Flow {flow_name} eliminado.")

                # Reagregar flow corregido
                add_flow(flow)
                print(f"Flow {flow_name} agregado corregido.")

if __name__ == "__main__":
    main()
