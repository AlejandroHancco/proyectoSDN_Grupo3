import requests

FLOODLIGHT_IP = "127.0.0.1"
BASE = f"http://{FLOODLIGHT_IP}:8080/wm"
PUSH = f"{BASE}/staticflowpusher/json"
DEVICE_URL = f"{BASE}/device/"
FLOWLIST_URL = f"{BASE}/staticflowpusher/list/all/json"

def get_switch_dpids():
    try:
        res = requests.get(DEVICE_URL)
        res.raise_for_status()
        devices = res.json()
    except:
        return []
    dpids = set()
    for dev in devices:
        for ap in dev.get("attachmentPoint", []):
            dpid = ap.get("switchDPID")
            if dpid:
                dpids.add(dpid)
    return list(dpids)

def get_flows():
    try:
        res = requests.get(FLOWLIST_URL)
        res.raise_for_status()
        return res.json()
    except:
        return {}

def delete_flow(name):
    requests.delete(PUSH, json={"name": name})

def push_flow(dpid):
    flow = {
        "switch": dpid,
        "name": f"default_ctrl_{dpid[-2:]}",
        "priority": 0,
        "active": "true",
        "actions": "output=controller"
    }
    requests.post(PUSH, json=flow)

def main():
    dpids = get_switch_dpids()
    if not dpids:
        print("No se detectaron switches.")
        return

    print(f"Switches: {dpids}")
    flows = get_flows()
    for dpid, f_list in flows.items():
        for entry in f_list:
            for name in entry:
                if "controller" not in name:
                    delete_flow(name)
    for d in dpids:
        push_flow(d)
    print("Proceso completado.")

if __name__ == "__main__":
    main()
