import ipaddress
import random
import socket
import concurrent.futures
from datetime import datetime

# --- 极简大抽样配置 ---
# 格式: (网段, 抽样数, 标签)
TARGET_NETWORKS = [
    # 核心高权重区
    ("162.159.0.0/16", 6000, "HK"),      # 明星港段，加大力度
    ("172.64.0.0/13", 6000, "US"),       # 美国大池子
    ("104.16.0.0/12", 10000, "US"),      # 暴力抽样，保量
    
    # 亚洲重点区
    ("103.21.244.0/22", 1500, "JP"),     # 日本
    ("103.22.200.0/22", 1500, "SG"),     # 新加坡
    ("103.31.4.0/22", 1000, "KR"),       # 韩国
    ("45.64.64.0/22", 800, "HK"),        # 香港
    ("103.23.244.0/24", 500, "TW"),      # 台湾
    
    # 全球补充区（保证总量突破一万六）
    ("162.158.0.0/15", 5000, "US"),      # 很多美西
    ("198.41.128.0/17", 4000, "US"),
    ("141.101.64.0/18", 2000, "EU"),     # 欧洲
    ("188.114.96.0/20", 2000, "EU"),
    ("173.245.48.0/20", 1500, "Global"),
    ("108.162.192.0/18", 2000, "US"),
]

def check_port(ip, label):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.6) # 稍微收紧超时，只要最稳的
            if s.connect_ex((str(ip), 443)) == 0:
                return f"{ip}:443#{label}"
    except:
        pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []

    print(f"🚀 启动全量生产: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            hosts_count = net.num_addresses - 2
            sample_size = min(hosts_count, count)
            
            # 使用更高效的随机算法
            sampled_indices = random.sample(range(1, hosts_count + 1), sample_size)
            for idx in sampled_indices:
                all_candidates.append((net[idx], label))
                
            print(f"已抽样: {cidr} ({label}) -> {sample_size}个")
        except Exception as e:
            print(f"处理 {cidr} 出错: {e}")

    print(f"🔥 总待测池: {len(all_candidates)}。开启 2000 并发轰炸...")

    final_results = []
    # 满速全开
    with concurrent.futures.ThreadPoolExecutor(max_workers=2000) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_results.append(res)

    # 写入文件
    with open("all.txt", "w") as f:
        f.write("\n".join(final_results))

    print(f"✨ 任务结束! 最终捕获存活 IP: {len(final_results)} 个")
    print(f"总耗时: {datetime.now() - start_time}")

if __name__ == "__main__":
    main()
