import asyncio
from pymodbus.client import AsyncModbusTcpClient


async def main():
    client = AsyncModbusTcpClient("localhost", port=5020)
    await client.connect()
    if not client.connected:
        print("连接失败")
        return

    # 往地址 100 写入值 250（代表 25.0°C）
    result = await client.write_register(address=100, value=250, slave=1)
    if result.isError():
        print(f"写入失败: {result}")
    else:
        print("写入成功: 地址 100 = 250")

    client.close()


asyncio.run(main())