import requests
import re
import socket
import ipaddress
import random

# 1. 进货摊位（在这里添加你想白嫖的源）
SOURCES = [
    "https://zip.cm.edu.kg/all.txt",
    "https://raw.githubusercontent.com/ymyuuu/IPDB/main/cloudflare.txt",
    "https://raw.githubusercontent.com/vfarid/cf-ip-ips/main/ips.txt"
]

def check_port(ip, port):
    """简单的端口存活检测"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect((str(ip), port))
        s.close()
        return True
    except:
        return False

def main():
    all_ips = set()

    # --- 动作一：白嫖全网现成的 IP ---
    for url in SOURCES:
        try:
            print(f"正在从 {url} 采购...")
            res = requests.get(url, timeout=15)
            # 匹配 IP:PORT 或者 IP:PORT#TAG
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+(?:#\S+)?', res.text)
            all_ips.update(found)
        except:
            print(f"源 {url} 访问失败")

    # --- 动作二：定向扫射自己的网段 ---
    print("正在扫射私房网段...")
    try:
        with open("ip_list.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2: continue
                cidr, label = parts[0], parts[1]
                net = ipaddress.ip_network(cidr)
                # 每个网段随机抽 20 个 IP 试试运气
                hosts = list(net.hosts())
                sampled = random.sample(hosts, min(len(hosts), 20))
                for ip in sampled:
                    for port in [443, 8443]:
                        if check_port(ip, port):
                            all_ips.add(f"{ip}:{port}#{label}")
    except Exception as e:
        print(f"扫射出错: {e}")

    # --- 动作三：保存战果 ---
    with open("all.txt", "w") as f:
        f.write("\n".join(list(all_ips)))
    print(f"✅ 搞定！共捕获 {len(all_ips)} 个精英考生")

if __name__ == "__main__":
    main()
