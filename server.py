import asyncio
import websockets
import json
from aiohttp import web

class dotdict(dict):
    """dot.notation access to dictionary attributes"""
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__

connected = {}
connected_by_name = {}


async def sendTo(ws, data):
    if isinstance(ws,str):
        raise Exception("sendTo called with string!")
    try:
        await ws.send(json.dumps(data))
    except Exception as e:
        print(f'Exception in sendTo: {e}')


async def handle_private(ws, data):
    try:
        to = data.to
        me = connected[ws].name
        data.msg = f'({me}): {data.msg}'
        toWs = connected_by_name[to]
        await sendTo(toWs, data)
    except Exception as e:
        print('Exception in handle_private.'+str(e))


async def handle_broadcast(myws, data):
    try:
        me = connected[myws].name
        data.msg = f'({me}): {data.msg}'
        for ws in connected:
            if ws != myws:
                await sendTo(ws, data)
    except Exception as e:
        print('Exception in handle_broadcast.' + str(e))


async def notifyAlreadyInUse(ws, name):
    try:
        msg = {
            'error': f'The name {name} is already in use.  Choose another.',
            'verb': 'error'
        }
        print(msg['error'])
        await sendTo(ws,msg)
    except Exception as e:
        print(f'Exception in notifyAlreadyInUse: {e}')


async def handle_announce(ws, data):

    try:
        name = data.name
        registeredName = connected[ws].name
        print(f'{name}/{registeredName} announced')
        if name in connected_by_name and connected_by_name[name] != ws:
            await notifyAlreadyInUse(ws,name)
            return
        if registeredName != name:
            if registeredName in connected_by_name:
                del connected_by_name[registeredName]
            connected[ws].name = name
            connected_by_name[name] = ws
            print(f'{connected[ws].name} changed their name to {name}')
        await notifyJoin(name)
    except Exception as e:
        print(f'Exception in handle_announce: {e}')


handlers = {
    "announce":handle_announce,
    "private":handle_private,
    "broadcast": handle_broadcast,
}


async def process(ws, dataIn):
    try:
        await handlers[dataIn.verb](ws, dataIn)
    except Exception as e:
        print('Exception in process: ' + str(e))


async def processIncomingConnections(websocket, path):
    connected[websocket] = dotdict()
    print("Client Connected.")
    name = None
    while True:
        try:
            dataIn = await websocket.recv()
            print(f'Data received: {dataIn}')
            d = json.loads(dataIn)
            if 'name' in d:
                name = d['name']
                d = dotdict(d)
                if (d.verb):
                    await process(websocket, d)
        except Exception as e:
            print("Exception: " + str(e))
            if name != None:
                name = connected[websocket].name
                del connected_by_name[name]
                del connected[websocket]
                print(f'{name} disconnected.')
            break

async def notifyJoin(name):
    try:
        print(connected)
        for ws in connected:
             currNotifee = connected[ws].name
             everyoneElse = list(connected_by_name.keys())
             print(everyoneElse)
             if currNotifee in everyoneElse:
                 everyoneElse.remove(currNotifee)
             msg = {
                 'name': 'server',
                 'verb': 'updateConnected',
                 'to': 'Everyone',
                 'connected': everyoneElse
             }
             print('sendingto')
             await sendTo(ws, msg)
    except Exception as e:
        print(f'Exception in notifyJoin: {e}')


async def handler(request):
    path = request.path
    ok_paths = ['/','/comms.css','/view.js']
    if path in ok_paths:
        if path == '/':
            path = '/index.html'
        print(path + " served")
        return web.FileResponse("./web"+path)
    else:
        return  web.Response(status=404,text="Not Found")


async def main():
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 80)
    try:
        await site.start()
        print("======= Serving on http://0.0.0.0:80/ ======")
    except:
        site = web.TCPSite(runner, '0.0.0.0', 8080)
        await site.start()
        print("======= Serving on http://0.0.0.0:8080/ ======")

    # pause here for very long time by serving HTTP requests and
    # waiting for keyboard interruption
    await asyncio.sleep(100*3600)


if  __name__ == "__main__":
    start_server = websockets.serve(processIncomingConnections, "0.0.0.0", 8081)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_until_complete(main())
    asyncio.get_event_loop().run_forever()

