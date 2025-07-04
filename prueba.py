import requests

CONTROLLER = "http://localhost:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

# IPs y puerto TCP
src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta de switches y puertos de salida hacia el siguiente salto
route = [
    {"dpid": "00:00:f2:20:f9:45:4c:4e", "out_port": 3},  # sw3 → sw4
    {"dpid": "00:00:5e:c7:6e:c6:11:4c", "out_port": 8},  # sw4 → sw5
    {"dpid": "00:00:1a:74:72:3f:ef:44", "out_port": 2},  # sw5 → h3
]

# Puerto desde h1 hacia sw3
host1_in_port = 2  # h1 → sw3

# ------------------- Funciones para construir flows -------------------

def build_tcp_flow(switch, in_port, out_port, ip_src, ip_dst, tcp_port, flow_id, reverse=False):
    flow = {
        "switch": switch,
        "name": flow_id,
        "priority": 30000,
        "eth_type": 2048,  # 0x0800
        "ip_proto": 6,     # TCP
        "in_port": int(in_port),
        "active": True,
        "actions": f"output={out_port}"
    }

    if not reverse:
        flow["ipv4_src"] = ip_src
        flow["ipv4_dst"] = ip_dst
        flow["tcp_dst"] = int(tcp_port)
    else:
        flow["ipv4_src"] = ip_dst
        flow["ipv4_dst"] = ip_src
        flow["tcp_src"] = int(tcp_port)

    return flow

def build_arp_flow(switch, out_port):
    return {
        "switch": switch,
        "name": f"allow_arp_{switch[-2:]}_{out_port}",
        "priority": 30000,
        "eth_type": 2054,  # 0x0806
        "active": True,
        "actions": f"output={out_port}"
    }

# ------------------- Enviar flows -------------------

def push_flow(flow):
    res = requests.post(PUSH_URL, json=flow)
    if res.status_code == 200:
        print(f"[OK] {flow['name']} -> {flow['switch']}")
    else:
        print(f"[ERR] {flow['name']} -> {flow['switch']}: {res.text}")

# ------------------- Lógica principal -------------------

def main():
    for i, hop in enumerate(route):
        sw = hop["dpid"]
        out_port = hop["out_port"]
        in_port = host1_in_port if i == 0 else route[i - 1]["out_port"]

        # TCP: flujo ida
        fwd = build_tcp_flow(sw, in_port, out_port, src_ip, dst_ip, dst_port, f"fwd_tcp_{i}")
        push_flow(fwd)

        # TCP: flujo retorno
        rev = build_tcp_flow(sw, out_port, in_port, src_ip, dst_ip, dst_port, f"rev_tcp_{i}", reverse=True)
        push_flow(rev)

        # ARP: permitir ambos sentidos
        push_flow(build_arp_flow(sw, out_port))
        push_flow(build_arp_flow(sw, in_port))

if __name__ == "__main__":
    main()
