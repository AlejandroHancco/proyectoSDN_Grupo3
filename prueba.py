#Este script esta hardcodeado, pero fue utilizado para extraer la idea principal del proyecto. Las funciones en el repository se basan en esto solo que parametrizados.
import requests

CONTROLLER = "http://localhost:8080"
ROUTE_URL = f"{CONTROLLER}/wm/topology/route"
PUSH_URL = f"{CONTROLLER}/wm/staticflowpusher/json"

# Datos IP y puerto TCP
src_ip = "10.0.0.1"
dst_ip = "10.0.0.3"
dst_port = 9000

# DPID y puerto del switch origen y destino
src_dpid = "00:00:f2:20:f9:45:4c:4e"  # sw3
src_port = 3  # puerto conectado al h1
dst_dpid = "00:00:1a:74:72:3f:ef:44"  # sw5
dst_port = 3  # puerto conectado al h3

def get_route():
    url = f"{ROUTE_URL}/{src_dpid}/{src_port}/{dst_dpid}/{dst_port}/json"
    res = requests.get(url)
    data = res.json()

    route = []
    for i in range(0, len(data) - 1, 2):
        sw = data[i]["switch"]
        in_port = data[i]["port"]["portNumber"]
        out_port = data[i+1]["port"]["portNumber"]
        route.append({"dpid": sw, "in_port": in_port, "out_port": out_port})

    return route

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
    route = get_route()
    for i, hop in enumerate(route):
        sw = hop["dpid"]
        in_port = hop["in_port"]
        out_port = hop["out_port"]

        # TCP
        fwd = build_tcp_flow(sw, in_port, out_port, src_ip, dst_ip, dst_port, f"fwd_tcp_{i}")
        rev = build_tcp_flow(sw, out_port, in_port, src_ip, dst_ip, dst_port, f"rev_tcp_{i}", reverse=True)

        # ARP
        arp1 = build_arp_flow(sw, in_port, out_port)
        arp2 = build_arp_flow(sw, out_port, in_port)

        for flow in [fwd, rev, arp1, arp2]:
            push_flow(flow)

if __name__ == "__main__":
    main()
