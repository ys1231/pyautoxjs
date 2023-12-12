import asyncio
import json
import os
import subprocess
import time
from loguru import logger
import websockets
import aiofiles
import yaml

logger.add("./logs/websocket.log", level="INFO", encoding="utf-8")

resultHello = {"message_id": f"{int(time.time())}_0.3289509833670963", "data": "ok", "version": "1.109.0",
               "debug": False, "type": "hello"}
closeMsg = {"message_id": f"{int(time.time())}_0.23965024608523922", "data": "close", "debug": False, "type": "close"}

script = {"type": "command", "message_id": f"{int(time.time())}_0.5780436812759773",
     "data": {"id": "main.js",
              "name": "main.js",
              "script": "",
              "command": "run"}
     }


def commad(cmd):
    result = subprocess.run(cmd, stdout=subprocess.PIPE)
    output = result.stdout.decode('utf-8')
    logger.debug(output[:-1])
    return int(output[:-1])


async def readScript(path):
    async with aiofiles.open(path, 'r') as f:
        data = str( await f.read())
        return data


async def recvMsg(websocket):
    sendData = None
    logger.debug("[1] recv msg")
    result = 0
    while True:
        recvData = await websocket.recv()
        jsonData = json.loads(recvData)
        if jsonData['type'] == 'hello':
            logger.info(f'recv [hello] msg: {jsonData["data"]}')
            sendData = json.dumps(resultHello)
            await websocket.send(sendData)
        elif jsonData['type'] == 'ping':
            # logger.debug(f'recv ping msg: {jsonData["data"]}')
            jsonData['type'] = 'pong'
            sendData = json.dumps(jsonData)
        elif jsonData['type'] == 'log':
            scriptLog = str(jsonData["data"]).split(":")[-1]
            logger.debug(f'[log] {scriptLog}')
            if 'autoxjs' in scriptLog:
                msg = scriptLog.split("]")[-1][:-2]
                logger.info(f'autoxjs: {msg}')
                result = int(msg.split(" ")[-1])
            elif '运行结束' in scriptLog:
                logger.info(scriptLog)
                return result
            sendData = None

        if sendData:
            await websocket.send(sendData)


async def main():
    with open('./res/config.yaml', 'r', encoding='utf-8') as f:
        deviceip = yaml.safe_load(f)['deviceip']
        adbpath = yaml.safe_load(f)['adbpath']
    os.system(f'{adbpath} connect {deviceip}')
    os.system(f'{adbpath} forward --remove-all ')
    port = commad([adbpath, 'forward', 'tcp:0', 'tcp:9317'])
    async with websockets.connect(f'ws://localhost:{port}') as websocket:
        name = json.dumps(resultHello)
        await websocket.send(name)
        script['data']['script'] = await readScript('./script.js')
        sendData = json.dumps(script)
        await websocket.send(sendData)
        result = await recvMsg(websocket)
        logger.debug(f"[4] recv msg {result}")
        return result


if __name__ == '__main__':
    asyncio.run(main())

