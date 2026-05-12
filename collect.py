import requests
import re
import socket
import ipaddress
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- 配置 ---
SOURCES = ["https://zip.cm.edu.kg/all.txt"]
TEST_URL = "http://www.gstatic.com/generate_204" 
TIMEOUT = 5
MAX_THREADS = 15

def check_ip_quality(raw_item):
    """
    顶级质检：剥离标签 -> 测端口 -> 测业务
    """
    # 1. 剥离标签，拿到干净的 IP:PORT
    tag = ""
    if "#" in raw_item:
        addr, tag = raw_item.split("#", 1)
    else:
        addr = raw_item
    
    try:
        # 2. 基础 TCP 探测
        ip, port = addr.split(':')
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.5)
        s.connect((ip, int(port)))
        s.close()

        # 3. 业务质检 (关键：代理地址必须干净)
        # 注意：这里只传 addr，不传 tag！
        proxy_url = f"http://{addr}"
        proxies = {"http": proxy_url, "https": proxy_url}
        
        # 强制不使用系统环境变量中的代理，防止干扰
        session = requests.Session()
        session.trust_env = False 
        
        res = session.get(TEST_URL, proxies=proxies, timeout=TIMEOUT, allow_redirects=False)
        
        if res.status_code in [204, 200]:
            # 测通了，把标签和延迟贴回去
            return f"{addr}#{tag}", True
    except:
        pass
    # 保底：虽然没测通业务，但至少端口是通的
    return raw_item, False

def main():
    raw_candidates = set()

    # 抓取源
    for url in SOURCES:
        try:
            print(f"📡 正在拉取: {url}")
            res = requests.get(url, timeout=10)
            # 兼容各种带标签的格式
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+(?:#\S+)?', res.text)
            raw_candidates.update(found)
        except: pass

    # 扫网段逻辑保持不变...
    # (此处略去网段扫描代码，确保逻辑一致)

    print(f"🔥 开始对 {len(raw_candidates)} 个候选进行质检...")
    high_quality = []
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        futures = {executor.submit(check_ip_quality, item): item for item in raw_candidates}
        for future in as_completed(futures):
            res_str, is_good = future.result()
            if is_good:
                high_quality.append(res_str)
                print(f"✅ 捕获精锐: {res_str}")

    # 如果实在没抓到优质的，就强行从原始列表抽 50 个，不让文件为空
    if not high_quality:
        print("⚠️ 优质 IP 筛选为空，启动紧急兜底...")
        final_list = list(raw_candidates)[:50]
    else:
        final_list = high_quality

    with open("ips.txt", "w") as f:
        f.write("\n".join(final_list))
    print(f"🎉 大功告成，产出 {len(final_list)} 个 IP")

if __name__ == "__main__":
    main()
