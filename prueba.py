import requests

CONTROLLER = "http://localhost:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

# IPs y puerto TCP
src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta switches con in_port y out_port
# Aquí in_port es el puerto por donde entra el paquete en el switch,
# out_port es hacia dónde debe salir para seguir la ruta
route = [
    {"dpid": "00:00:f2:20:f9:45:4c:4e", "in_port": 2, "out_port": 2},  # sw3: in h1(2), out ens5(2)
    {"dpid": "00:00:aa:51:aa:ba:72:41", "in_port": 2, "out_port": 4},  # sw4: in ens5(2), out ens7(4)
    {"dpid": "00:00:1a:74:72:3f:ef:44", "in_port": 2, "out_port": 3},  # sw5: in ens5(2), out ens6(3)
]

def build_tcp_flow(switch, in_port, out_port, ip_src, ip_dst, tcp_port, flow_id, reverse=False):
    flow = {
        "switch": switch,
        "name": flow_id,
        "priority": 30000,
        "eth_type": 2048,
        "ip_proto": 6,
        "in_port": in_port,
        "active": True,
        "actions": f"output={out_port}"
    }

    if not reverse:
        flow["ipv4_src"] = ip_src
        flow["ipv4_dst"] = ip_dst
        flow["tcp_dst"] = tcp_port
    else:
        flow["ipv4_src"] = ip_dst
        flow["ipv4_dst"] = ip_src
        flow["tcp_src"] = tcp_port

    return flow

def build_arp_flow(switch, in_port, out_port):
    # Para ARP, normalmente dejamos pasar broadcast, aquí saldrá por out_port
    # Pero para simetría, podemos crear flow para in_port y out_port
    return {
        "switch": switch,
        "name": f"allow_arp_{switch[-2:]}_{in_port}_{out_port}",
        "priority": 30000,
        "eth_type": 2054,
        "in_port": in_port,
        "active": True,
        "actions": f"output={out_port}"
    }

def push_flow(flow):
    res = requests.post(PUSH_URL, json=flow)
    if res.status_code == 200:
        print(f"[OK] Inserted {flow['name']} on {flow['switch']}")
    else:
        print(f"[ERR] Failed on {flow['switch']}: {res.text}")

def main():
    for i, hop in enumerate(route):
        sw = hop["dpid"]
        in_port = hop["in_port"]
        out_port = hop["out_port"]

        # TCP forward
        fwd = build_tcp_flow(sw, in_port, out_port, src_ip, dst_ip, dst_port, f"fwd_tcp_{i}")
        push_flow(fwd)

        # TCP reverse
        rev = build_tcp_flow(sw, out_port, in_port, src_ip, dst_ip, dst_port, f"rev_tcp_{i}", reverse=True)
        push_flow(rev)

        # ARP flows (both directions)
        arp1 = build_arp_flow(sw, in_port, out_port)
        arp2 = build_arp_flow(sw, out_port, in_port)
        push_flow(arp1)
        push_flow(arp2)

if __name__ == "__main__":
    main()
