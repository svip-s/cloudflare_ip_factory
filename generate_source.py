import ipaddress, random, socket, concurrent.futures
from datetime import datetime

# --- 全球 50+ 国家/地区爆破配置 ---
# 既然要对标，咱们就把能见到的国家代码全塞进去
TARGET_NETWORKS = [
    # 亚洲精品 (高抽样)
    ("162.159.0.0/16", 8000, "HK"), ("103.21.244.0/22", 2000, "JP"), 
    ("103.22.200.0/22", 2000, "SG"), ("103.31.4.0/22", 1500, "KR"),
    ("103.23.244.0/24", 800, "TW"), ("103.41.68.0/22", 1000, "IN"),
    ("103.25.176.0/22", 1000, "AU"), ("43.249.72.0/22", 500, "MY"),
    ("103.244.112.0/22", 500, "VN"), ("202.147.32.0/20", 500, "ID"),
    
    # 欧洲大区 (细化国家，这是增加“候选数”的关键)
    ("141.101.64.0/18", 3000, "GB"), ("188.114.96.0/20", 3000, "DE"),
    ("190.93.240.0/20", 2000, "FR"), ("197.234.240.0/22", 2000, "IT"),
    ("162.158.0.0/15", 4000, "NL"), ("173.245.48.0/20", 2000, "ES"),
    ("104.24.0.0/14", 3000, "RU"),   ("104.28.0.0/14", 2000, "PL"),
    ("108.162.192.0/18", 2000, "CH"), ("172.64.0.0/13", 3000, "AT"),
    
    # 北美/南美/非洲/中东
    ("104.16.0.0/13", 10000, "US"), ("104.20.0.0/14", 5000, "CA"),
    ("190.93.240.0/20", 2000, "BR"), ("198.41.128.0/17", 5000, "MX"),
    ("162.158.0.0/15", 3000, "ZA"), ("103.31.4.0/22", 1000, "AE"),
    ("172.64.0.0/13", 3000, "IL"),   ("108.162.192.0/18", 2000, "TR"),
]

def check_port(ip, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5) # 进一步收紧，只要最好的
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except: pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []
    print(f"🚀 启动【全球全量爆破版】: {start_time}")

    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, count)
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            for idx in sampled_indices:
                all_candidates.append((net[idx], label))
        except: continue

    print(f"🔥 待测池: {len(all_candidates)}。开启 2500 并发...")
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2500) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res: final_results.append(res)

    with open("all.txt", "w") as f: f.write("\n".join(final_results))
    print(f"✨ 最终存活: {len(final_results)} 个")
    print(f"耗时: {datetime.now() - start_time}")

if __name__ == "__main__": main()
