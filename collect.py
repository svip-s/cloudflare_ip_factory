import requests
import re
import os
import boto3  # 需要在 yml 里加上这个依赖
from botocore.client import Config
import ipaddress

# --- 配置 ---
SOURCE_FILE = "sources.txt"
OUTPUT_FILE = "ips.txt"

def get_cloudflare_ips():
    """
    🛡️ 从官方获取最新的 Cloudflare IPv4 CIDR 资产白名单
    若官方请求失败，则使用硬编码兜底，确保绝对不会放过非 CF 的内鬼
    """
    print("📡 [安检舱] 正在同步 Cloudflare 官方资产白名单...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get("https://www.cloudflare.com/ips-v4", headers=headers, timeout=10)
        res.raise_for_status()
        cf_nets = [ipaddress.ip_network(net.strip()) for net in res.text.split() if net.strip()]
        print(f"    └─ ✅ 成功从官网上线同步了 {len(cf_nets)} 个官方网段。")
        return cf_nets
    except Exception as e:
        print(f"    ⚠️ 警告: 官方白名单同步失败 ({str(e)})，触发本地硬编码防线兜底...")
        default_ips = [
            "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22", "103.31.4.0/22",
            "141.101.64.0/18", "108.162.192.0/18", "190.93.240.0/20", "188.114.96.0/20",
            "197.234.240.0/22", "198.41.128.0/17", "162.158.0.0/15", "104.16.0.0/13",
            "104.24.0.0/14", "172.64.0.0/13", "131.0.72.0/22"
        ]
        return [ipaddress.ip_network(net) for net in default_ips]

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
        try:
            requests.post(url, data=payload, timeout=10)
        except:
            pass

def main():
    all_ips = set()
    failed_sources = []

    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        urls = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]

    for url in urls:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
            res = requests.get(url, headers=headers, timeout=20)
            res.raise_for_status()
            
            found = re.findall(r'\d+\.\d+\.\d+\.\d+:\d+#?\S*', res.text)
            if found: 
                all_ips.update(found)
            else:
                failed_sources.append(url)
        except Exception as e:
            failed_sources.append(f"{url} ({str(e)})")
            continue

    # 🛡️ 深度融合：启动 CF 官方血统净化过滤
    cf_networks = get_cloudflare_ips()
    purified_ips = set()
    spy_count = 0  # 统计抓到了多少个反代假 IP

    print("🧼 [安检舱] 正在进行工业级高精度范围碰撞过滤...")
    for ip_entry in all_ips:
        try:
            # 剥离出纯净的 IPv4 地址（砍掉 :端口 和 #备注）
            pure_ip = ip_entry.split(':')[0].split('#')[0]
            ip_obj = ipaddress.ip_address(pure_ip)
            
            # 核心碰撞检查
            if any(ip_obj in net for net in cf_networks):
                purified_ips.add(ip_entry)
            else:
                spy_count += 1
        except:
            pass
            
    print(f"    └─ 🧼 清洗完成！成功拦截并击杀内鬼节点: {spy_count} 个")

    final_list = sorted(list(purified_ips))
    
    # 检查是否有实质性更新
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            old_data = f.read().splitlines()
        if set(old_data) == purified_ips:
            print("数据未变化（清洗后内容一致），跳过推送")
            return

    if final_list:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(final_list))
        
        r2_status = upload_to_r2()
        
        error_info = f"❌ *失败源*: `{len(failed_sources)}` 个" if failed_sources else "✅ *源抓取全通*"
        spy_info = f"🚨 *击杀内鬼*: `{spy_count}` 个" if spy_count > 0 else "🧬 *血统纯正*"
        
        msg = (f"🚀 *IP 工厂纯净版生产完毕*\n"
               f"----------------------------\n"
               f"📦 *入库数量*: `{len(final_list)}` 个\n"
               f"🪪 *防线审计*: {spy_info}\n"
               f"📡 *抓取状态*: {error_info}\n"
               f"☁️ *R2 状态*: {r2_status}\n"
               f"⏰ *北京时间*: {os.popen('date').read().strip()}\n"
               f"----------------------------")
        send_to_tg(msg)
    else:
        send_to_tg("⚠️ 今日份搬运失败：没抓到属于 CF 官方的有效 IP。")

if __name__ == "__main__":
    main()
