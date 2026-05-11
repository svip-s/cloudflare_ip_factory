import requests
import re

# 你的进货摊位列表
MARKET_URLS = [
    "https://zip.cm.edu.kg/all.txt",
    "https://raw.githubusercontent.com/ymyuuu/IPDB/main/cloudflare.txt",
    "https://raw.githubusercontent.com/vfarid/cf-ip-ips/main/ips.txt"
]

def get_market_ips():
    final_ips = set()
    for url in MARKET_URLS:
        try:
            print(f"正在从 {url} 采购...")
            res = requests.get(url, timeout=10)
            # 兼容 IP:PORT#TAG 和 纯 IP:PORT 格式
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+(?:#\S+)?', res.text)
            final_ips.update(found)
        except:
            print(f"摊位 {url} 暂时没出摊")
            continue
    
    # 存进你的私房菜库
    with open("all.txt", "w") as f:
        f.write("\n".join(list(final_ips)))
    print(f"✅ 采购完成，共进货 {len(final_ips)} 个 IP")

if __name__ == "__main__":
    get_market_ips()
