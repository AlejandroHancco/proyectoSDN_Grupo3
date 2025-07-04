import requests

CONTROLLER = "http://127.0.0.1:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

# IPs de los hosts
src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta en orden desde host origen hasta host destino
route = [
    {"dpid": "00:00:72:e0:80:7e:85:4c", "out_port": 3},  # sw1
    {"dpid": "00:00:aa:51:aa:ba:72:41", "out_port": 5},  # sw2
    {"dpid": "00:00:5e:c7:6e:c6:11:4c", "out_port": 3},  # sw3
]

host_in_port = 2     # puerto de entrada del host 10.0.0.1 en el primer switch
server_out_port = 3  # puerto de salida al servidor 10.0.0.3 en el último switch

def build_forward_flow(switch, in_port, out_port, flow_id):
    return {
        "switch": switch,
        "name": flow_id,
        "priority": "40000",
        "eth_type": "0x0800",
        "ip_proto": "6",
        "ipv4_src": src_ip,
        "ipv4_dst": dst_ip,
        "tcp_dst": str(dst_port),
        "in_port": str(in_port),
        "active": "true",
        "actions": f"output={out_port}"
    }

def build_reverse_flow(switch, in_port, out_port, flow_id):
    return {
        "switch": switch,
        "name": flow_id,
        "priority": "40000",
        "eth_type": "0x0800",
        "ip_proto": "6",
        "ipv4_src": dst_ip,
        "ipv4_dst": src_ip,
        "tcp_src": str(dst_port),
        "in_port": str(in_port),
        "active": "true",
        "actions": f"output={out_port}"
    }

def build_arp_flow(switch):
    return {
        "switch": switch,
        "name": f"allow_arp_{switch[-2:]}",
        "priority": "40000",
        "eth_type": "0x0806",
        "active": "true",
        "actions": "output=flood"
    }

def push_flow(flow):
    try:
        res = requests.post(PUSH_URL, json=flow)
        res.raise_for_status()
        print(f"[OK] Flow inserted on switch {flow['switch']} ({flow['name']})")
    except Exception as e:
        print(f"[ERR] Failed to insert flow on switch {flow['switch']} ({flow['name']}): {e}")

def main():
    for i in range(len(route)):
        sw = route[i]["dpid"]

        # Entradas y salidas
        in_port = host_in_port if i == 0 else route[i - 1]["out_port"]
        out_port = server_out_port if i == len(route) - 1 else route[i]["out_port"]

        # Forward flow
        forward_flow = build_forward_flow(sw, in_port, out_port, f"tcp_to_server_{i}")
        push_flow(forward_flow)

        # Reverse flow
        reverse_flow = build_reverse_flow(sw, out_port, in_port, f"tcp_from_server_{i}")
        push_flow(reverse_flow)

        # ARP flood
        arp_flow = build_arp_flow(sw)
        push_flow(arp_flow)

if __name__ == "__main__":
    main()
