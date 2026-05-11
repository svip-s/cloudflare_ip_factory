import ipaddress
import random
import socket
import concurrent.futures
from datetime import datetime

# --- 精细化打标配置 ---
# 这里的逻辑是：从小段到大段，越精准的段权重越高
TARGET_NETWORKS = [
    # --- 亚洲精品区 (陕西移动首选) ---
    ("162.159.0.0/16", 4000, "HK-CM"),      # 移动神段，极大概率香港
    ("103.21.244.0/22", 800, "JP-TYO"),     # 东京
    ("103.22.200.0/22", 800, "SG-SIN"),     # 新加坡
    ("103.31.4.0/22", 800, "KR-SEL"),       # 首尔
    ("45.64.64.0/22", 500, "HK-GIA"),       # 直连香港
    
    # --- 美西直连区 (延迟虽高但带宽大) ---
    ("172.64.0.0/17", 1500, "US-LAX"),      # 洛杉矶
    ("172.64.128.0/17", 1500, "US-SJC"),    # 圣何塞
    ("104.16.0.0/14", 2000, "US-West"),     # 美西通用
    ("108.162.192.0/18", 1500, "US-VIP"),   # 优质美西
    
    # --- 欧洲与全球覆盖 ---
    ("141.101.64.0/18", 1000, "EU-Zone"),   # 欧洲
    ("188.114.96.0/20", 1000, "EU-Central"),
    ("190.93.240.0/20", 500, "Global-LA"),  # 拉美
    
    # --- 剩余大段填充 (保证基数) ---
    ("198.41.128.0/17", 2000, "Global-ANY"),
    ("162.158.0.0/15", 4000, "Global-Mix"),
    ("173.245.48.0/20", 1000, "Global-Old"),
]

def check_port(ip, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.7)
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except:
        pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []

    print(f"🚀 启动精细化生产: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            # 排除掉网络号和广播地址
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, count)
            
            # 使用索引抽样，内存友好
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            for idx in sampled_indices:
                all_candidates.append((net[idx], label))
                
            print(f"抽样完成: {cidr} [{label}] -> {sample_size}个")
        except Exception as e:
            print(f"处理 {cidr} 出错: {e}")

    print(f"🔥 待测池: {len(all_candidates)} IP。开启 2000 并发初筛...")

    final_results = []
    # GitHub 性能猛，直接拉满
    with concurrent.futures.ThreadPoolExecutor(max_workers=2000) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_results.append(res)

    with open("all.txt", "w") as f:
        f.write("\n".join(final_results))

    print(f"✨ 生产结束! 捕获 IP: {len(final_results)} 个")
    print(f"总耗时: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
