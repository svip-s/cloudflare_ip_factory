import ipaddress, random, socket, concurrent.futures
from datetime import datetime

# --- 全球精准打标 + 移动权重增强 ---
GEO_CONFIG = [
    # 【移动精品矿区】 - 强制高频抽样，给足 HK/TW/SG/JP
    ("162.159.0.0/16", 8000, ["HK", "TW", "SG", "JP", "KR", "MO"]),
    ("45.64.64.0/22", 1000, ["HK", "SG"]),
    
    # 【美西/大网核心】 - 陕西移动走美西延迟也稳，主供 US/CA
    ("172.64.0.0/13", 8000, ["US", "CA", "MX", "BR", "AU", "NZ"]),
    ("104.16.0.0/13", 10000, ["US", "CA", "US", "CA"]), # 双倍 US 权重
    
    # 【欧洲/中东全量】 - 负责解锁地区，标签打细
    ("141.101.64.0/18", 4000, ["GB", "FR", "DE", "IT", "ES", "NL", "CH", "SE", "NO", "DK"]),
    ("188.114.96.0/20", 4000, ["PL", "CZ", "AT", "HU", "RO", "BG", "GR", "BE", "IE", "PT"]),
    ("104.24.0.0/14", 4000, ["RU", "UA", "FI", "EE", "LV", "LT", "BY", "MD", "TR", "IL"]),
    
    # 【全量混编段】 - 补充剩下的小众国家
    ("162.158.0.0/15", 6000, ["ZA", "AE", "SA", "IN", "PK", "ID", "MY", "TH", "VN", "PH"]),
]

def check_port(ip, label):
    """
    不再只选快的！
    将超时放宽到 1.2s，避免 GitHub 只选它家门口的 IP
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1.2) 
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except: pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []
    print(f"🚀 启动【反自嗨·高质量版】: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, total_count, labels in GEO_CONFIG:
        try:
            net = ipaddress.ip_network(cidr)
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, total_count)
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            
            # 均匀打标
            chunk_size = len(sampled_indices) // len(labels)
            for i, label in enumerate(labels):
                start, end = i * chunk_size, (i + 1) * chunk_size
                for idx in sampled_indices[start:end]:
                    all_candidates.append((net[idx], label))
        except: continue

    print(f"🔥 总待测池: {len(all_candidates)}。开启 2500 并发扫射...")
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2500) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: final_results.append(res)

    with open("all.txt", "w") as f: f.write("\n".join(final_results))
    print(f"✨ 任务结束! 最终捕获 IP: {len(final_results)} 个")
    print(f"总耗时: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
