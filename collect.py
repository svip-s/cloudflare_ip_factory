import requests
import re
import os

# --- 配置 ---
SOURCE_FILE = "sources.txt" # 存放源地址的文件名
OUTPUT_FILE = "ips.txt"     # 输出的文件名

def main():
    all_ips = set()
    
    # 1. 检查源文件是否存在
    if not os.path.exists(SOURCE_FILE):
        print(f"❌ 错误：找不到 {SOURCE_FILE} 文件，请先创建它！")
        return

    # 2. 读取所有源地址
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        # 过滤掉空行和以 # 开头的注释行
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    if not urls:
        print(f"⚠️ 警告：{SOURCE_FILE} 里面是空的，没活干了。")
        return

    print(f"🚀 搬运工启动，共发现 {len(urls)} 个采集源...")

    # 3. 循环搬运
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    for url in urls:
        try:
            print(f"📡 正在拉取: {url}")
            res = requests.get(url, headers=headers, timeout=20)
            res.encoding = 'utf-8' # 强制编码，防止中文标签乱码
            
            # 正则抓取 IP:PORT#标签 格式
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+#?\S*', res.text)
            
            if found:
                all_ips.update(found)
                print(f"✅ 成功捕获 {len(found)} 个候选者")
            else:
                print(f"⚠️ 该源未发现有效 IP 格式")
        except Exception as e:
            print(f"❌ 访问 {url} 失败: {e}")

    # 4. 汇总保存
    final_list = sorted(list(all_ips))
    
    if final_list:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_list))
        print("-" * 30)
        print(f"🎉 大功告成！今日共汇聚 {len(final_list)} 个 IP 到 {OUTPUT_FILE}")
    else:
        print("🛑 最终结果为空，请检查源地址内容。")

if __name__ == "__main__":
    main()
