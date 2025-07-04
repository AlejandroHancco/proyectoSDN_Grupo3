import requests

CONTROLLER = "http://localhost:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta: switches intermedios en orden, con out_port hacia el siguiente switch
route = [
    {"dpid": "00:00:72:e0:80:7e:85:4c", "out_port": 3},
    {"dpid": "00:00:aa:51:aa:ba:72:41", "out_port": 5},
    {"dpid": "00:00:5e:c7:6e:c6:11:4c", "out_port": 3},
]

# Puertos hacia los hosts
host_in_port = 2  # desde 10.0.0.1
server_out_port = 3  # hacia 10.0.0.3

def build_flow(switch, in_port, out_port, flow_id):
    return {
        "switch": switch,
        "name": flow_id,
        "priority": "40000",
        "eth_type": "0x0800",  # CORRECTO para IPv4
        "ip_proto": "6",  # TCP
        "ipv4_src": src_ip,
        "ipv4_dst": dst_ip,
        "tcp_dst": str(dst_port),
        "in_port": str(in_port),
        "active": "true",
        "actions": f"output={out_port}"
    }

def push_flow(flow):
    try:
        res = requests.post(PUSH_URL, json=flow)
        res.raise_for_status()
        print(f"[OK] Flow inserted on switch {flow['switch']}")
    except Exception as e:
        print(f"[ERR] Failed to insert flow on switch {flow['switch']}: {e}")

def main():
    for i in range(len(route)):
        sw = route[i]["dpid"]

        if i == 0:
            in_port = host_in_port
        else:
            in_port = route[i-1]["out_port"]

        if i == len(route) - 1:
            out_port = server_out_port
        else:
            out_port = route[i]["out_port"]

        flow_id = f"tcp_to_server_{i}"
        flow = build_flow(sw, in_port, out_port, flow_id)
        push_flow(flow)

if __name__ == "__main__":
    main()
