import ipaddress, random, socket, concurrent.futures
from datetime import datetime

# --- 全球精细化打标配置 (ISO 国家代码) ---
TARGET_NETWORKS = [
    # --- 亚洲 (Asia) ---
    ("162.159.0.0/16", 5000, "HK"), ("45.64.64.0/22", 500, "HK"),  # 香港
    ("103.21.244.0/22", 1500, "JP"), ("103.22.200.0/22", 1500, "SG"), # 日本、新加坡
    ("103.31.4.0/22", 1000, "KR"), ("103.23.244.0/24", 500, "TW"),   # 韩国、台湾
    ("103.25.176.0/22", 500, "AU"), ("103.41.68.0/22", 500, "IN"),   # 澳洲、印度
    
    # --- 北美 (North America) ---
    ("104.16.0.0/13", 8000, "US"), ("172.64.0.0/13", 8000, "US"),    # 美国核心
    ("108.162.192.0/18", 2000, "US"), ("198.41.128.0/17", 4000, "US"),
    ("173.245.48.0/20", 1500, "CA"),                                 # 加拿大
    
    # --- 欧洲 (Europe) ---
    ("141.101.64.0/18", 2000, "GB"), ("188.114.96.0/20", 2000, "DE"), # 英国、德国
    ("190.93.240.0/20", 1500, "FR"), ("197.234.240.0/22", 1000, "IT"), # 法国、意大利
    ("162.158.0.0/15", 5000, "EU-Mix"),                              # 欧洲杂鱼
    
    # --- 其他地区 (Others) ---
    ("190.93.240.0/20", 1000, "BR"),  # 巴西 (南美)
    ("141.101.64.0/18", 500, "ZA"),   # 南非 (非洲)
    ("197.234.240.0/22", 500, "AE"),  # 阿联酋 (中东)
]

def check_port(ip, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.6)
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except: pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []
    print(f"🚀 启动【全球多国版】生产: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, count)
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            for idx in sampled_indices:
                all_candidates.append((net[idx], label))
            print(f"抽样: {cidr} ({label}) -> {sample_size}个")
        except: continue

    print(f"🔥 总待测池: {len(all_candidates)}。开启 2000 并发扫射...")
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2000) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: final_results.append(res)

    with open("all.txt", "w") as f: f.write("\n".join(final_results))
    print(f"✨ 任务结束! 最终捕获存活 IP: {len(final_results)} 个")
    print(f"总耗时: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
