import asyncio
import ipaddress
import random

PORTS = [443, 8443, 2053, 2096]
TIMEOUT = 1.0 

async def check_ip(ip, port, label):
    """探测 IP 并携带标签"""
    try:
        # 尝试建立连接
        conn = asyncio.open_connection(str(ip), port)
        reader, writer = await asyncio.wait_for(conn, timeout=TIMEOUT)
        writer.close()
        await writer.wait_closed()
        # 按照你本地脚本喜欢的格式输出：IP:端口#标签
        return f"{ip}:{port}#{label}"
    except:
        return None

async def worker(queue, results):
    while True:
        task = await queue.get()
        if task is None: break
        ip, port, label = task
        res = await check_ip(ip, port, label)
        if res:
            results.append(res)
            print(f"✨ 发现金矿: {res}")
        queue.task_done()

async def main():
    # 1. 加载网段和对应的标签
    targets = []
    try:
        with open("ip_list.txt", "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 2: continue
                cidr, label = parts[0], parts[1]
                
                net = ipaddress.ip_network(cidr)
                hosts = list(net.hosts())
                # 稍微加大抽样，增加出金率
                sample_size = min(len(hosts), 800) 
                sampled_hosts = random.sample(hosts, sample_size)
                
                for ip in sampled_hosts:
                    targets.append((ip, label))
    except FileNotFoundError:
        print("❌ 没找到 ip_list.txt")
        return

    # 2. 建立任务队列
    queue = asyncio.Queue()
    results = []
    for ip, label in targets:
        for port in PORTS:
            await queue.put((ip, port, label))

    # 3. 开启并发任务
    tasks = []
    concurrency = 300 # GitHub Actions 性能不错，可以开到 300
    for _ in range(concurrency):
        tasks.append(asyncio.create_task(worker(queue, results)))

    await queue.join()

    # 停止 worker
    for _ in range(concurrency):
        await queue.put(None)
    await asyncio.gather(*tasks)

    # 4. 保存结果
    with open("all.txt", "w") as f:
        f.write("\n".join(results))
    print(f"✅ 扫描完成，捕获 {len(results)} 个带标签的有效节点！")

if __name__ == "__main__":
    asyncio.run(main())
