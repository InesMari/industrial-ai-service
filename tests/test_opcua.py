import asyncio
from app.services.opcua_service import OpcUaService

async def main():
    svc = OpcUaService('opc.tcp://localhost:4840/freeopcua/server/')
    await svc.connect()
    await svc.subscribe(['ProductionLine/Temperature', 'ProductionLine/Vibration'])
    print('订阅已建立，等待变化...')
    await asyncio.sleep(10)
    await svc.disconnect()

asyncio.run(main())