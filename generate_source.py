import ipaddress
import random
import socket
import concurrent.futures
from datetime import datetime

# --- 万级全量版配置 ---
# 我们把 CF 所有的官方大段都塞进来，并按照“陕西移动”的实测优劣分权重
TARGET_NETWORKS = [
    # 精品富矿区 (高权重，抽样密度加大)
    ("162.159.0.0/16", 5000, "HK-CM"),
    ("172.64.0.0/13", 5000, "US-West"),
    ("104.16.0.0/12", 8000, "US-CF"),
    ("108.162.192.0/18", 3000, "US-VIP"),
    
    # 亚洲邻居区 (地理优势)
    ("103.21.244.0/22", 1500, "JP"),
    ("103.22.200.0/22", 1500, "SG"),
    ("45.64.64.0/22", 1000, "HK-Direct"),
    
    # 全量海选区 (大基数，保证数量)
    ("162.158.0.0/15", 4000, "Global"),
    ("198.41.128.0/17", 3000, "Global"),
    ("173.245.48.0/20", 1000, "Global"),
    ("103.31.4.0/22", 1000, "Global-AS"),
    ("141.101.64.0/18", 1000, "Global-EU"),
]

def check_port(ip, label):
    """探测 443 端口"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # 云端环境 0.7s 是生死线，扫几万个 IP 不能拖泥带水
            s.settimeout(0.7)
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except:
        pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []

    print(f"开始【万级规模】生产任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            # 这里用生成器节省内存
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, count)
            
            # 高效抽样算法，防止内存爆掉
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            for idx in sampled_indices:
                all_candidates.append((net[idx], label))
                
            print(f"抽样完成: {cidr} -> {sample_size} 个")
        except Exception as e:
            print(f"处理 {cidr} 出错: {e}")

    print(f"🔥 待测池已就绪: {len(all_candidates)} 个 IP。开启高压初筛...")

    # 4. 暴力并发 (GitHub 机器撑得住)
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2000) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_results.append(res)

    # 5. 写入文件
    with open("all.txt", "w") as f:
        f.write("\n".join(final_results))

    end_time = datetime.now()
    print(f"✨ 生产完毕! 捕获存活 IP: {len(final_results)} 个")
    print(f"总耗时: {end_time - start_time}")

if __name__ == "__main__":
    main()
