import requests

CONTROLLER = "http://127.0.0.1:8080"
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


def build_flow(switch, in_port, out_port, flow_id, src, dst, port, reverse=False):
    return {
        "switch": switch,
        "name": flow_id,
        "priority": "40000",
        "etherType": "0x0800",
        "ip_proto": "6",  # TCP
        "ipv4_src": dst if reverse else src,
        "ipv4_dst": src if reverse else dst,
        "tcp_src": str(port) if reverse else None,
        "tcp_dst": None if reverse else str(port),
        "in_port": str(in_port),
        "active": "true",
        "actions": f"output={out_port}"
    }


def push_flow(flow):
    # Remove null fields (like tcp_src or tcp_dst depending on direction)
    clean_flow = {k: v for k, v in flow.items() if v is not None}
    try:
        res = requests.post(PUSH_URL, json=clean_flow)
        res.raise_for_status()
        print(f"[OK] Flow inserted on switch {flow['switch']}")
    except Exception as e:
        print(f"[ERR] Failed to insert flow on switch {flow['switch']}: {e}")


def main():
    # Flujos de ida (cliente a servidor)
    for i in range(len(route)):
        sw = route[i]["dpid"]

        in_port = host_in_port if i == 0 else route[i - 1]["out_port"]
        out_port = server_out_port if i == len(route) - 1 else route[i]["out_port"]

        flow_id = f"tcp_fwd_{i}"
        flow = build_flow(sw, in_port, out_port, flow_id, src_ip, dst_ip, dst_port)
        push_flow(flow)

    # Flujos de retorno (servidor a cliente)
    for i in reversed(range(len(route))):
        sw = route[i]["dpid"]

        out_port = host_in_port if i == 0 else route[i - 1]["out_port"]
        in_port = server_out_port if i == len(route) - 1 else route[i]["out_port"]

        flow_id = f"tcp_bwd_{i}"
        flow = build_flow(sw, in_port, out_port, flow_id, src_ip, dst_ip, dst_port, reverse=True)
        push_flow(flow)


if __name__ == "__main__":
    main()
