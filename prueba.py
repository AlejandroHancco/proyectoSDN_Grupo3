import requests

CONTROLLER = "http://localhost:8080"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

# IPs y puerto TCP
src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# Ruta de switches (ordenados) y puertos de salida
route = [
    {"dpid": "00:00:72:e0:80:7e:85:4c", "out_port": 3},
    {"dpid": "00:00:aa:51:aa:ba:72:41", "out_port": 5},
    {"dpid": "00:00:5e:c7:6e:c6:11:4c", "out_port": 3},
]

# Puertos conectados a hosts
host1_in_port = 2   # h1 hacia su switch
host3_out_port = 3  # desde el último switch hacia h3

# --------------------- Funciones de construcción de flows ---------------------

def build_tcp_flow(switch, in_port, out_port, ip_src, ip_dst, tcp_port, flow_id, reverse=False):
    flow = {
        "switch": switch,
        "name": flow_id,
        "priority": 30000,             # ✅ entero
        "eth_type": 2048,              # ✅ 0x0800 decimal
        "ip_proto": 6,                 # ✅ TCP
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

# --------------------- Push y envío ---------------------

def push_flow(flow):
    res = requests.post(PUSH_URL, json=flow)
    if res.status_code == 200:
        print(f"[OK] Inserted {flow['name']} on {flow['switch']}")
    else:
        print(f"[ERR] Failed on {flow['switch']}: {res.text}")

# --------------------- Ejecución principal ---------------------

def main():
    for i, hop in enumerate(route):
        sw = hop["dpid"]
        out_port = hop["out_port"]

        if i == 0:
            in_port = host1_in_port
        else:
            in_port = route[i - 1]["out_port"]

        # TCP hacia el servidor
        flow_fwd = build_tcp_flow(sw, in_port, out_port, src_ip, dst_ip, dst_port, f"fwd_tcp_{i}")
        push_flow(flow_fwd)

        # TCP respuesta desde servidor
        flow_rev = build_tcp_flow(sw, out_port, in_port, src_ip, dst_ip, dst_port, f"rev_tcp_{i}", reverse=True)
        push_flow(flow_rev)

        # ARP permitido en ambas direcciones
        arp1 = build_arp_flow(sw, out_port)
        arp2 = build_arp_flow(sw, in_port)
        push_flow(arp1)
        push_flow(arp2)

if __name__ == "__main__":
    main()
