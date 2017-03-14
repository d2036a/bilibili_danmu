import threading
from bilibiliClient import bilibiliClient

danmuji = bilibiliClient()

try:
    t = threading.Thread(target=danmuji.HeartbeatLoop)
    t.daemon = True
    t.start()
    danmuji.connectServer()
except KeyboardInterrupt:
    danmuji.connected = False

