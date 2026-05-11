import ipaddress
import random
import socket
import concurrent.futures
from datetime import datetime

# --- 配置区：黄金网段定向爆破 ---
# 这些网段涵盖了 AS13335 的核心部分和传说中的 AS209242 优化段
TARGET_NETWORKS = {
    "AS209242_Mobile": [
        "162.159.0.0/16", 
        "172.64.0.0/13"
    ],
    "AS13335_Core": [
        "104.16.0.0/12",
        "108.162.192.0/18",
        "141.101.64.0/18",
        "162.158.0.0/15",
        "198.41.128.0/17"
    ],
    "CF_Others": [
        "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
        "103.31.4.0/22", "190.93.240.0/20", "188.114.96.0/20",
        "197.234.240.0/22", "131.0.72.0/22"
    ]
}

# 每个大分类下的抽样数量
SAMPLE_COUNTS = {
    "AS209242_Mobile": 2000, # 重点关照
    "AS13335_Core": 5000,   # 核心资产
    "CF_Others": 3000       # 兼顾多样性
}

def check_port(ip, label):
    """探测 443 端口存活"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.8) # 云端带宽快，0.8秒足够了
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except:
        pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []

    print(f"开始生产任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 抽样逻辑
    for category, networks in TARGET_NETWORKS.items():
        category_candidates = []
        total_ips_in_cat = sum(ipaddress.ip_network(n).num_addresses for n in networks)
        print(f"正在从 {category} 抽取样本 (包含 {total_ips_in_cat} 个 IP)...")
        
        # 均匀分配抽样额度到该分类下的每个网段
        per_net_count = SAMPLE_COUNTS[category] // len(networks)
        
        for cidr in networks:
            net = ipaddress.ip_network(cidr)
            hosts = list(net.hosts())
            sample_size = min(len(hosts), per_net_count)
            category_candidates.extend([(ip, category) for ip in random.sample(hosts, sample_size)])
        
        all_candidates.extend(category_candidates)

    print(f"抽样完成，总计待测 IP: {len(all_candidates)}。开始并发初筛...")

    # 2. 并发扫描 (GitHub Actions 机器可以开很高并发)
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1000) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_results.append(res)

    # 3. 写入文件
    with open("all.txt", "w") as f:
        f.write("\n".join(final_results))

    end_time = datetime.now()
    print(f"✨ 任务结束! 捕获存活 IP: {len(final_results)} 个")
    print(f"总耗时: {end_time - start_time}")

if __name__ == "__main__":
    main()
