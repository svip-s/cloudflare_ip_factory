import requests
import re
import os

# --- 配置 ---
SOURCE_FILE = "sources.txt"
OUTPUT_FILE = "ips.txt"

def send_to_tg(message):
    """
    通过 Secrets 安全发送消息
    """
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    
    if not token or not chat_id:
        print("⚠️ 未配置 TG 密钥，跳过通知")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": f"🚀 **IP 工厂日报**\n\n{message}",
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, data=payload, timeout=10)
        print("✅ TG 通知已发送")
    except Exception as e:
        print(f"❌ TG 通知失败: {e}")

def main():
    all_ips = set()
    
    if not os.path.exists(SOURCE_FILE):
        send_to_tg("❌ 错误：找不到 sources.txt 文件！")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    print(f"🚀 开始采集，源数量: {len(urls)}")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            res.encoding = 'utf-8'
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+#?\S*', res.text)
            if found:
                all_ips.update(found)
        except:
            continue

    final_list = sorted(list(all_ips))
    
    if final_list:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_list))
        # 任务成功，给 TG 发个喜报
        msg = f"✅ 搬运完成！\n📦 累计入库: {len(final_list)} 个 IP\n⏰ 时间: {os.popen('date').read().strip()}"
        send_to_tg(msg)
    else:
        send_to_tg("⚠️ 今日份搬运失败，没抓到任何 IP，请检查源地址。")

if __name__ == "__main__":
    main()
