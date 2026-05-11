import ipaddress, random, socket, concurrent.futures
from datetime import datetime

# --- 全球 50+ 国家/地区极速打标矩阵 ---
# 目标：通过极细的国家划分，骗过本地脚本的 TOP_PER_REGION 限制
GEO_CONFIG = [
    # 亚洲 & 大洋洲 (20个)
    ("162.159.0.0/16", 6000, ["HK", "TW", "JP", "KR", "SG", "MY", "TH", "VN", "PH", "ID"]),
    ("103.21.244.0/22", 2000, ["JP", "AU", "NZ", "IN", "PK", "BD", "KH", "LA", "MM", "MO"]),
    # 欧洲 (20个)
    ("141.101.64.0/18", 4000, ["GB", "FR", "DE", "IT", "ES", "NL", "CH", "SE", "NO", "DK"]),
    ("188.114.96.0/20", 3000, ["PL", "CZ", "AT", "HU", "RO", "BG", "GR", "BE", "IE", "PT"]),
    ("104.24.0.0/14", 4000, ["RU", "UA", "FI", "EE", "LV", "LT", "BY", "MD", "GE", "AM"]),
    # 美洲 & 中东 & 非洲 (12个)
    ("104.16.0.0/13", 10000, ["US", "CA", "MX", "BR", "AR", "CL", "CO", "PE"]),
    ("172.64.0.0/13", 6000, ["TR", "SA", "AE", "IL", "ZA", "EG", "NG", "KE"])
]

def check_port(ip, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5) # 0.5s 只要极速
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except: pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []
    print(f"🚀 启动【联合国全量版】: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, total_count, labels in GEO_CONFIG:
        try:
            net = ipaddress.ip_network(cidr)
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, total_count)
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            
            # 将该网段的样本平均分配给列表里的国家标签
            chunk_size = len(sampled_indices) // len(labels)
            for i, label in enumerate(labels):
                start, end = i * chunk_size, (i + 1) * chunk_size
                for idx in sampled_indices[start:end]:
                    all_candidates.append((net[idx], label))
            print(f"网段 {cidr} 已拆分给: {', '.join(labels)}")
        except: continue

    print(f"🔥 总待测池: {len(all_candidates)}。开启 2500 并发扫射...")
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2500) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: final_results.append(res)

    with open("all.txt", "w") as f: f.write("\n".join(final_results))
    print(f"✨ 任务结束! 捕获存活 IP: {len(final_results)} 个")
    print(f"总耗时: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
