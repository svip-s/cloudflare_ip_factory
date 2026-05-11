import ipaddress
import random
import socket
import concurrent.futures
from datetime import datetime

# --- 核心配置：网段、抽样量与国家标签 ---
# 这里的标签你可以根据需要继续扩充
TARGET_NETWORKS = [
    # 格式: (网段, 抽样数, 国家/地区标签)
    ("104.16.0.0/13", 2000, "US"),      # CF 大网-美国
    ("104.24.0.0/14", 1000, "US"),
    ("172.64.0.0/13", 2000, "Global"),  # 混编精品段
    ("162.159.0.0/16", 1500, "HK-SG"),  # 经常出香港/新加坡的段
    ("108.162.192.0/18", 1000, "US"),
    ("141.101.64.0/18", 800, "EU"),     # 欧洲段
    ("45.64.64.0/22", 500, "HK"),       # 纯香港段(示例)
    ("103.21.244.0/22", 500, "JP-SG"),  # 亚洲段
    ("103.22.200.0/22", 500, "AS"),
    ("103.31.4.0/22", 500, "AS"),
    ("188.114.96.0/20", 800, "EU"),
    ("190.93.240.0/20", 500, "LA"),     # 拉美
]

def check_port(ip, label):
    """探测 443 端口并打标"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.8)
            if s.connect_ex((str(ip), 443)) == 0:
                # 产出格式符合你本地脚本要求：IP:端口#地区编号
                return f"{ip}:443#{label}"
    except:
        pass
    return None

def main():
    start_time = datetime.now()
    all_candidates = []

    print(f"🚀 开始硬核生产任务: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # 1. 抽样逻辑：根据预设列表直接分类
    for cidr, count, label in TARGET_NETWORKS:
        try:
            net = ipaddress.ip_network(cidr)
            hosts = list(net.hosts())
            sample_size = min(len(hosts), count)
            sampled_ips = random.sample(hosts, sample_size)
            all_candidates.extend([(ip, label) for ip in sampled_ips])
            print(f"已从 {cidr} 抽取 {sample_size} 个样本 -> 标签: {label}")
        except Exception as e:
            print(f"处理 {cidr} 出错: {e}")

    print(f"🔎 抽样完成，总计待测 IP: {len(all_candidates)}。开始并发筛选...")

    # 2. 高并发扫描 (1500 并发)
    final_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=1500) as executor:
        futures = [executor.submit(check_port, ip, label) for ip, label in all_candidates]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res:
                final_results.append(res)

    # 3. 写入文件
    with open("all.txt", "w") as f:
        f.write("\n".join(final_results))

    end_time = datetime.now()
    print(f"✨ 任务结束! 最终捕获存活且带标 IP: {len(final_results)} 个")
    print(f"总耗时: {end_time - start_time}")

if __name__ == "__main__":
    main()
