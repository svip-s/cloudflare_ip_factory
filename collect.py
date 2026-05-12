import requests
import re
import socket
import ipaddress
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 深度定制配置 ---
SOURCES = ["https://zip.cm.edu.kg/all.txt"]
TEST_URL = "http://www.gstatic.com/generate_204" 
TIMEOUT = 5        # 给一点容错空间，防止误杀好IP
MAX_THREADS = 20   # 20线程，既高效又安全，符合GitHub Actions的生存法则

def check_ip_quality(ip_port_label):
    """
    业务级质检：先探大门（TCP），再测真连（HTTP）
    """
    parts = ip_port_label.split('#')
    addr = parts[0]
    label = parts[1] if len(parts) > 1 else "Unknown"
    
    try:
        # 1. 极速初筛：TCP 端口连通性
        ip, port = addr.split(':')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((ip, int(port)))
        s.close()

        # 2. 深度质检：模拟真实代理请求
        # 这一步能彻底过滤掉那些“有速度没网”的干扰项
        proxies = {"http": f"http://{addr}", "https": f"http://{addr}"}
        start = time.time()
        
        # 模拟真实行为，稍微加一点随机抖动
        time.sleep(random.uniform(0.1, 0.3))
        
        res = requests.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, verify=False)
        
        if res.status_code == 204 or res.status_code == 200:
            delay = int((time.time() - start) * 1000)
            return f"{addr}#{label}_{delay}ms", delay
    except:
        pass
    return None, None

def main():
    raw_candidates = set()

    # --- 阶段一：源数据获取 ---
    for url in SOURCES:
        try:
            print(f"📡 正在获取源数据: {url}")
            res = requests.get(url, timeout=15)
            # 兼容带有 # 标签的 IP:PORT 格式
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+(?:#\S+)?', res.text)
            raw_candidates.update(found)
        except Exception as e:
            print(f"❌ 获取失败: {e}")

    # --- 阶段二：私房采样扫描 ---
    print("🎯 正在执行私房网段采样...")
    try:
        # 确保你仓库里有 ip_list.txt，格式为：CIDR 标签
        with open("ip_list.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2: continue
                cidr, label = parts[0], parts[1]
                net = ipaddress.ip_network(cidr)
                hosts = list(net.hosts())
                # 采样50个，既有代表性又不至于扫太久
                sampled = random.sample(hosts, min(len(hosts), 50))
                for ip in sampled:
                    for port in [443, 8443]:
                        raw_candidates.add(f"{ip}:{port}#{label}")
    except FileNotFoundError:
        print("⚠️ 未发现 ip_list.txt，跳过私房扫描")
    except Exception as e:
        print(f"⚠️ 扫描逻辑异常: {e}")

    # --- 阶段三：并发质检 ---
    print(f"🔥 启动质检引擎 (并发数: {MAX_THREADS})...")
    final_results = []
    
    # 使用线程池加速，20线程是兼顾性能与安全的黄金分割点
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(check_ip_quality, item): item for item in raw_candidates}
        for future in as_completed(futures):
            result, delay = future.result()
            if result:
                final_results.append((result, delay))
                print(f"✅ 精锐入库: {result}")

    # --- 阶段四：排序保存 ---
    # 按响应速度从快到慢排序，第一行永远是最强的
    final_results.sort(key=lambda x: x[1])
    sorted_output = [x[0] for x in final_results]

    with open("ips.txt", "w") as f:
        f.write("\n".join(sorted_output))
        
    print("-" * 30)
    print(f"🎉 任务完成！共捕获 {len(sorted_output)} 个真活 IP。")
    if sorted_output:
        print(f"🚀 冠军 IP 延迟: {final_results[0][1]}ms")

if __name__ == "__main__":
    # 屏蔽不安全请求的警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    main()
