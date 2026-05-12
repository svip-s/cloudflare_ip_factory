import requests
import re
import os
import sys

# --- 配置 ---
SOURCE_FILE = "sources.txt"
OUTPUT_FILE = "ips.txt"

def send_to_tg(message):
    """
    通过 Secrets 安全发送消息，增加调试打印
    """
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    
    # 调试日志：检查变量是否传进来了（Actions 日志会自动打码，安全）
    print(f"DEBUG: Token 是否存在: {bool(token)}")
    print(f"DEBUG: Chat ID 是否存在: {bool(chat_id)}")
    
    if not token or not chat_id:
        print("⚠️ 报错：环境变量 TG_BOT_TOKEN 或 TG_CHAT_ID 为空，请检查 GitHub Secrets 和 yml 配置！")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": f"🚀 **IP 工厂日报**\n\n{message}",
        "parse_mode": "Markdown"
    }
    
    try:
        # 增加 headers，模拟真实浏览器，防止 TG 屏蔽机房请求
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.post(url, data=payload, timeout=15, headers=headers)
        
        # 打印 TG 返回的真实结果，这是破案的关键
        print(f"DEBUG: TG 接口返回状态码: {response.status_code}")
        print(f"DEBUG: TG 接口返回内容: {response.text}")
        
        if response.status_code == 200:
            print("✅ TG 通知发送成功！")
        else:
            print(f"❌ TG 通知发送异常，请检查 Token 或 ID 是否正确。")
    except Exception as e:
        print(f"❌ 网络请求异常，无法连接到 TG 服务器: {e}")

def main():
    print("--- 任务开始 ---")
    all_ips = set()
    
    if not os.path.exists(SOURCE_FILE):
        err_msg = "❌ 错误：找不到 sources.txt 文件！"
        print(err_msg)
        send_to_tg(err_msg)
        return

    try:
        with open(SOURCE_FILE, "r", encoding="utf-8") as f:
            urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    except Exception as e:
        send_to_tg(f"❌ 读取源文件失败: {e}")
        return

    print(f"🚀 正在拉取源，共计 {len(urls)} 个地址...")
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=20)
            res.encoding = 'utf-8'
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+#?\S*', res.text)
            if found:
                all_ips.update(found)
        except Exception as e:
            print(f"⚠️ 抓取 {url} 时跳过: {e}")
            continue

    final_list = sorted(list(all_ips))
    
    if final_list:
        try:
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write("\n".join(final_list))
            success_msg = f"✅ 搬运完成！\n📦 累计入库: {len(final_list)} 个 IP"
            print(success_msg)
            send_to_tg(success_msg)
        except Exception as e:
            send_to_tg(f"❌ 写入文件失败: {e}")
    else:
        fail_msg = "⚠️ 今日份搬运失败：没抓到任何有效 IP。"
        print(fail_msg)
        send_to_tg(fail_msg)

if __name__ == "__main__":
    main()
