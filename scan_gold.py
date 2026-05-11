import asyncio
import ipaddress
import random

# 定义扫描的目标端口，涵盖你列表中的非标端口
PORTS = [443, 8443, 2053, 2096]
TIMEOUT = 1.0  # 云端探测，超时可以稍微宽容一点

async def check_ip(ip, port):
    """探测 IP 的特定端口是否开放"""
    try:
        conn = asyncio.open_connection(str(ip), port)
        reader, writer = await asyncio.wait_for(conn, timeout=TIMEOUT)
        writer.close()
        await writer.wait_closed()
        return f"{ip}:{port}"
    except:
        return None

async def worker(queue, results):
    while True:
        task = await queue.get()
        if task is None:
            break
        ip, port = task
        res = await check_ip(ip, port)
        if res:
            results.append(res)
            print(f"✨ 发现金矿: {res}")
        queue.task_done()

async def main():
    # 1. 加载网段
    targets = []
    with open("ip_list.txt", "r") as f:
        for line in f:
            net = ipaddress.ip_network(line.strip())
            # 每个网段随机抽样，保证覆盖面
            hosts = list(net.hosts())
            sample_size = min(len(hosts), 500) 
            targets.extend(random.sample(hosts, sample_size))

    # 2. 建立任务队列
    queue = asyncio.Queue()
    results = []
    for ip in targets:
        for port in PORTS:
            await queue.put((ip, port))

    # 3. 开启并发任务
    tasks = []
    for _ in range(200): # 200 个并发协程
        tasks.append(asyncio.create_task(worker(queue, results)))

    await queue.join()

    # 停止 worker
    for _ in range(200):
        await queue.put(None)
    await asyncio.gather(*tasks)

    # 4. 保存结果
    with open("all.txt", "w") as f:
        f.write("\n".join(results))
    print(f"✅ 扫描完成，共捕获 {len(results)} 个活跃 IP")

if __name__ == "__main__":
    asyncio.run(main())
