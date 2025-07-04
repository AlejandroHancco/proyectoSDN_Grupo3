import requests

CONTROLLER = "http://10.20.12.162:8080"
SWITCHES_URL = f"{CONTROLLER}/switches"
FLOWS_URL = f"{CONTROLLER}/wm/staticflowpusher/list/all/json"
DELETE_URL = f"{CONTROLLER}/wm/staticflowpusher/json"
PUSH_URL = DELETE_URL

def get_all_switches():
    try:
        res = requests.get(SWITCHES_URL)
        res.raise_for_status()
        return [sw["dpid"] for sw in res.json()]
    except Exception as e:
        print(f"Error getting switches: {e}")
        return []

def get_all_flows():
    try:
        res = requests.get(FLOWS_URL)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        print(f"Error getting flows: {e}")
        return {}

def delete_flow(name):
    res = requests.delete(DELETE_URL, json={"name": name})
    if res.status_code == 200:
        print(f"[✓] Deleted {name}")
    else:
        print(f"[✗] Failed to delete {name}: {res.text}")

def push_default_controller_flow(dpid):
    flow = {
        "switch": dpid,
        "name": f"default_ctrl_{dpid[-2:]}",
        "priority": 0,
        "active": True,
        "actions": "output=controller"
    }
    res = requests.post(PUSH_URL, json=flow)
    if res.status_code == 200:
        print(f"[✓] Inserted controller flow for {dpid}")
    else:
        print(f"[✗] Failed to insert flow for {dpid}: {res.text}")

def main():
    switches = get_all_switches()
    flows = get_all_flows()

    for dpid, flow_list in flows.items():
        for entry in flow_list:
            for name in entry.keys():
                # Solo borra si no es el default controller flow
                if not name.startswith("default_ctrl_"):
                    delete_flow(name)

    for dpid in switches:
        push_default_controller_flow(dpid)

if __name__ == "__main__":
    main()
