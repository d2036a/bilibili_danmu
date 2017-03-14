# -*- coding: utf-8 -*-
import httplib
import socket
import random
import json
from struct import *
import json
import config
import re
import time

class bilibiliClient():
    def __init__(self):
        self._CIDInfoUrl = '/api/player?id=cid:'
        self._roomId = 0
        self._ChatPort = 788
        self._protocolversion = 1
        self._socket = 0
        self.connected = False
        self._UserCount = 0
        self._ChatHost = 'livecmt-1.bilibili.com'

        self._roomId = input(u'请输入房间号：'.encode("utf8"))
        self._roomId = int(self._roomId)

    def connectServer(self):
        print (u'正在进入房间。。。。。')
        s = httplib.HTTPConnection("live.bilibili.com")
        s.request("GET", "/" + (str(self._roomId)))
        html = s.getresponse().read()
        m = re.findall(r'ROOMID\s=\s(\d+)', html)
        ROOMID = m[0]
        self._roomId = int(ROOMID)

        s.request("GET", self._CIDInfoUrl + ROOMID)
        xml_string = s.getresponse().read().decode('utf8')
        m = re.search("<server>(?P<host>.*)<\/server>", xml_string)
        self._ChatHost = m.group('host')
        s.close()


        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.connect((self._ChatHost, self._ChatPort))
        print (u'链接弹幕中。。。。。')
        if (self.SendJoinChannel(self._roomId) == True):
            self.connected = True
            print (u'进入房间成功。。。。。')
            print (u'链接弹幕成功。。。。。')
            self.ReceiveMessageLoop()

    def HeartbeatLoop(self):
        while self.connected == False:
            time.sleep(0.5)

        while self.connected == True:
            self.SendSocketData(0, 16, self._protocolversion, 2, 1, "")
            time.sleep(30)


    def SendJoinChannel(self, channelId):
        self._uid = (int)(100000000000000.0 + 200000000000000.0*random.random())
        body = '{"roomid":%s,"uid":%s}' % (channelId, self._uid)
        self.SendSocketData(0, 16, self._protocolversion, 7, 1, body)
        return True


    def SendSocketData(self, packetlength, magic, ver, action, param, body):
        bytearr = body.encode('utf-8')
        if packetlength == 0:
            packetlength = len(bytearr) + 16
        sendbytes = pack('!IHHII', packetlength, magic, ver, action, param)
        if len(bytearr) != 0:
            sendbytes = sendbytes + bytearr
        self._socket.send(sendbytes)


    def ReceiveMessageLoop(self):
        while self.connected == True:
            tmp = self._socket.recv(4)
            if(len(tmp) < 4):
                continue
            expr, = unpack('!i', tmp)
            tmp = self._socket.recv(2)
            tmp = self._socket.recv(2)
            tmp = self._socket.recv(4)
            num, = unpack('!i', tmp)
            tmp = self._socket.recv(4)
            num2 = expr - 16

            if num2 > 0:
                num -= 1
                if num==0 or num==1 or num==2:
                    tmp = self._socket.recv(4)
                    num3, = unpack('!I', tmp)
                    print (u'房间人数为 %s' % num3)
                    self._UserCount = num3
                    continue
                elif num==3 or num==4:
                    tmp = self._socket.recv(num2)
                    # strbytes, = unpack('!s', tmp)
                    try: # 为什么还会出现 utf-8 decode error??????
                        messages = tmp.decode('utf-8')
                    except:
                        continue
                    self.parseDanMu(messages)
                    continue
                elif num==5 or num==6 or num==7:
                    tmp = self._socket.recv(num2)
                    continue
                else:
                    if num != 16:
                        tmp = self._socket.recv(num2)
                    else:
                        continue

    def parseDanMu(self, messages):
        try:
            dic = json.loads(messages)
        except: # 有些情况会 jsondecode 失败，未细究，可能平台导致
            return
        cmd = dic['cmd']
        if cmd == 'LIVE':
            print (u'直播开始。。。')
            return
        if cmd == 'PREPARING':
            print (u'房主准备中。。。')
            return
        if cmd == 'DANMU_MSG':
            commentText = dic['info'][1]
            commentUser = dic['info'][2][1]
            isAdmin = dic['info'][2][2] == '1'
            isVIP = dic['info'][2][3] == '1'
            if isAdmin:
                commentUser = u'管理员 ' + commentUser
            if isVIP:
                commentUser = 'VIP ' + commentUser
            try:
                print (commentUser + ' say: ' + commentText)
            except:
                pass
            return
        if cmd == 'SEND_GIFT' and config.TURN_GIFT == 1:
            GiftName = dic['data']['giftName']
            GiftUser = dic['data']['uname']
            Giftrcost = dic['data']['rcost']
            GiftNum = dic['data']['num']
            try:
                print(GiftUser + u' 送出了 ' + str(GiftNum) + u' 个 ' + GiftName)
            except:
                pass
            return
        if cmd == 'WELCOME' and config.TURN_WELCOME == 1:
            commentUser = dic['data']['uname']
            try:
                print (u'欢迎 ' + commentUser + u' 进入房间。。。。')
            except:
                pass
            return
        return
