#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018-05-30 20:00 下午
# @Author  : HuangLi
# @Contact : lhuang9703@gmail.com
# @Site    : 
# @File    : client.py
# @Software: PyCharm Community Edition

import sys
import time
from socket import *
import threading
import struct
import pickle
import zlib
import numpy as np

import cv2

HOST = "127.0.0.1"
PORT1 = 6666
PORT2 = 9999

class VideoClient():
    def __init__(self):
        super(VideoClient, self).__init__()
        self.sock = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                self.sock.connect((HOST, PORT1))
                break
            except:
                time.sleep(2)
                continue
        print("connection with server success")
        client = threading.Thread(target=self.senddata)
        server = threading.Thread(target=self.showdata)
        client.start()
        server.start()

    def senddata(self):
        print("in senddata")
        data = "".encode("utf-8")
        size = struct.calcsize("L")
        # self.cap = cv2.VideoCapture(0)
        self.cap = cv2.VideoCapture(r"D:\\360data\重要数据\桌面\杂\《小王》.mp4")
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # cv2.imshow('frame', gray)
            frame = cv2.resize(frame, (0,0), fx=1, fy=1)
            data = pickle.dumps(frame)
            zdata = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
            try:
                # msg = input()

                self.sock.sendall(struct.pack("L", len(zdata)) + zdata)
                # print("send ", len(zdata))
            except:
                print('exception')
                break
            for i in range(0):
                self.cap.read()

    def showdata(self):
        data = "".encode("utf-8")
        size = struct.calcsize("L")
        cv2.namedWindow('remote', cv2.WINDOW_GUI_NORMAL)
        cv2.resizeWindow('remote', 320, 240)
        while True:
            while len(data) < size:
                data = data + self.sock.recv(81920)
            packed_size = data[:size]
            data = data[size:]
            msg_size = struct.unpack("L", packed_size)[0]
            while len(data) < msg_size:
                data = data + self.sock.recv(81920)
            zframe_data = data[:msg_size]
            data = data[msg_size:]
            frame_data = zlib.decompress(zframe_data)
            frame = pickle.loads(frame_data)
            try:
                cv2.imshow('remote', frame)
                if cv2.waitKey(100) & 0xFF == ord('q'):
                    break
            except:
                pass
            # print('server said:' + '\n' + data)
        self.cap.release()
        cv2.destroyAllWindows()


class TextClient():
    def __init__(self):
        super(TextClient, self).__init__()
        self.sock = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                self.sock.connect((HOST, PORT1))
                break
            except:
                time.sleep(2)
                continue
        print("connection with server success")
        client = threading.Thread(target=self.senddata)
        server = threading.Thread(target=self.showdata)
        client.start()
        server.start()

    def senddata(self):
        print("in sendtext")
        while True:
            msg = input()
            msg = '000' + msg
            self.sock.send(msg.encode())

    def showdata(self):
        while True:
            data = self.sock.recv(1024).decode()
            print('server said:' + '\n' + data)


if __name__ == '__main__':
    VideoClient()
    TextClient()