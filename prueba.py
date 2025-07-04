import requests

CONTROLLER = "http://localhost:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta intermedia
route = [
    {"dpid": "00:00:72:e0:80:7e:85:4c", "out_port": 3},
    {"dpid": "00:00:aa:51:aa:ba:72:41", "out_port": 5},
    {"dpid": "00:00:5e:c7:6e:c6:11:4c", "out_port": 3},
]

# Puertos hacia los hosts
host1_in_port = 2  # h1 hacia el primer switch
host3_out_port = 3  # desde último switch hacia h3

def build_tcp_flow(switch, in_port, out_port, ip_src, ip_dst, tcp_port, flow_id, reverse=False):
    match = {
        "switch": switch,
        "name": flow_id,
        "priority": 40000,
        "eth_type": "0x0800",
        "ip_proto": "6",  # TCP
        "in_port": str(in_port),
        "active": "true",
        "actions": f"output={out_port}"
    }

    if not reverse:
        match["ipv4_src"] = ip_src
        match["ipv4_dst"] = ip_dst
        match["tcp_dst"] = str(tcp_port)
    else:
        match["ipv4_src"] = ip_dst
        match["ipv4_dst"] = ip_src
        match["tcp_src"] = str(tcp_port)

    return match

def build_arp_flow(switch, out_port):
    return {
        "switch": switch,
        "name": f"allow_arp_{switch[-2:]}",
        "priority": 30000,
        "eth_type": "0x0806",
        "active": "true",
        "actions": f"output={out_port}"
    }

def push_flow(flow):
    res = requests.post(PUSH_URL, json=flow)
    if res.status_code == 200:
        print(f"[OK] Inserted {flow['name']} on {flow['switch']}")
    else:
        print(f"[ERR] Failed on {flow['switch']}: {res.text}")

def main():
    for i in range(len(route)):
        sw = route[i]["dpid"]
        out_port = route[i]["out_port"]

        if i == 0:
            in_port = host1_in_port
        else:
            in_port = route[i - 1]["out_port"]

        # TCP hacia servidor
        flow = build_tcp_flow(sw, in_port, out_port, src_ip, dst_ip, dst_port, f"fwd_tcp_{i}")
        push_flow(flow)

        # TCP respuesta
        rev_flow = build_tcp_flow(sw, out_port, in_port, src_ip, dst_ip, dst_port, f"rev_tcp_{i}", reverse=True)
        push_flow(rev_flow)

        # ARP broadcast
        arp_fwd = build_arp_flow(sw, out_port)
        push_flow(arp_fwd)

        arp_rev = build_arp_flow(sw, in_port)
        push_flow(arp_rev)

if __name__ == "__main__":
    main()
