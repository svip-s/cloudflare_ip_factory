import requests
import re
import os
import boto3  # 需要在 yml 里加上这个依赖
from botocore.client import Config

# --- 配置 ---
SOURCE_FILE = "sources.txt"
OUTPUT_FILE = "ips.txt"

def upload_to_r2():
    """
    将结果同步到 Cloudflare R2
    """
    account_id = os.environ.get("R2_ACCOUNT_ID")
    access_key = os.environ.get("R2_ACCESS_KEY")
    secret_key = os.environ.get("R2_SECRET_KEY")
    bucket_name = os.environ.get("R2_BUCKET_NAME")
    
    if not all([account_id, access_key, secret_key, bucket_name]):
        return "❌ R2 密钥未配置"

    try:
        s3 = boto3.client('s3',
            endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version='s3v4'))
        
        s3.upload_file(OUTPUT_FILE, bucket_name, OUTPUT_FILE, 
                       ExtraArgs={'ContentType': 'text/plain'})
        return "✅ R2 同步成功"
    except Exception as e:
        return f"❌ R2 同步失败: {str(e)}"

def send_to_tg(message):
    token = os.environ.get("TG_BOT_TOKEN")
    chat_id = os.environ.get("TG_CHAT_ID")
    if token and chat_id:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
        requests.post(url, data=payload, timeout=10)

def main():
    all_ips = set()
    if not os.path.exists(SOURCE_FILE):
        send_to_tg("❌ 错误：找不到 sources.txt")
        return

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    for url in urls:
        try:
            res = requests.get(url, timeout=20)
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+#?\S*', res.text)
            if found: all_ips.update(found)
        except: continue

    final_list = sorted(list(all_ips))
    if final_list:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_list))
        
        # --- 同步到 R2 ---
        r2_status = upload_to_r2()
        
        # --- 组织战报 ---
        msg = (f"🚀 *IP 工厂生产完毕*\n"
               f"----------------------------\n"
               f"📦 *入库数量*: `{len(final_list)}` 个\n"
               f"☁️ *R2 存储状态*: {r2_status}\n"
               f"⏰ *完成时间*: {os.popen('date').read().strip()}\n"
               f"----------------------------\n"
               f"✨ _GitHub 仓库也已同步保存_")
        send_to_tg(msg)
    else:
        send_to_tg("⚠️ 今日份搬运失败：没抓到有效 IP。")

if __name__ == "__main__":
    main()
