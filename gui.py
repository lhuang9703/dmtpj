#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018-05-31 23:40 下午
# @Author  : HuangLi
# @Contact : lhuang9703@gmail.com
# @Site    : 
# @File    : gui.py
# @Software: PyCharm Community Edition

import sys
from socket import *
from time import sleep
import json
import _thread as thread
import time
import threading
import struct
import pickle
import zlib

from win32api import GetSystemMetrics
import wx
import cv2
import pyaudio

SCREEN_WIDTH = GetSystemMetrics(0)
SCREEN_HEIGHT = GetSystemMetrics(1)


def get_config():
    """
    获取配置信息
    :return: [dict] 配置文件的数据
    """
    with open('./config.json') as configfile:
        config = json.load(configfile)
    return config

HOST = get_config()['client']['server_ip']
PORT = get_config()['client']['text_port']
PORT2 = get_config()['client']['video_port']
PORT3 = get_config()['client']['audio_port']
CHUNK = get_config()['audio_parameters']['CHUNK']
FORMAT = pyaudio.paInt16
CHANNELS = get_config()['audio_parameters']['CHANNELS']
RATE = get_config()['audio_parameters']['RATE']
RECORD_SECONDS = get_config()['audio_parameters']['RECORD_SECONDS']


class AudioClient():
    """
    音频客户端类，捕获声卡数据，向音频服务器发送音频数据
    从音频服务器接收对方音频数据
    """

    __slots__ = ['py_audio', 'stream1', 'stream2', 'sock', 'client', 'server']

    def __init__(self, host, port):
        """
        音频客户端类的初始化：连接音频服务器，分配两个线程分别用于发送数据和接收数据
        :param host: [string] 音频服务器IP地址
        :param port: [int] 音频服务器端口号
        """
        super(AudioClient, self).__init__()
        self.py_audio = pyaudio.PyAudio()
        self.stream1 = None
        self.stream2 = None
        self.sock = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                self.sock.connect((host, port))
                break
            except:
                time.sleep(2)
                continue
        print("connection with server success")
        client = threading.Thread(target=self.send_audio_data)
        server = threading.Thread(target=self.show_audio_data)
        client.start()
        server.start()

    def __del__(self):
        """
        音频客户端类的析构，关闭连接，释放声卡
        :return:
        """
        if self.stream1 is not None:
            try:
                self.stream1.stop_stream()
                self.stream1.close()
            except:
                pass
        if self.stream2 is not None:
            try:
                self.stream2.stop_stream()
                self.stream2.close()
            except:
                pass
        if self.py_audio is not None:
            self.py_audio.terminate()
        if self.sock is not None:
            self.sock.close()

    def send_audio_data(self):
        """
        捕获声卡数据并发送给音频服务器
        :return:
        """
        # 通过声卡捕获音频
        try:
            self.stream1 = self.py_audio.open(format=FORMAT,
                                             channels=CHANNELS,
                                             rate=RATE,
                                             input=True,
                                             frames_per_buffer=CHUNK)
        except:
            print('请检查声卡是否可用')
        while self.stream1.is_active():
            frame = []
            for i in range(0, int(RATE/CHUNK*RECORD_SECONDS)):
                data = self.stream1.read(CHUNK)
                frame.append(data)
            data = pickle.dumps(frame)
            zdata = zlib.compress(data, zlib.Z_BEST_COMPRESSION)

            try:
                self.sock.sendall(struct.pack("L", len(zdata)) + zdata)
            except Exception:
                continue

    def show_audio_data(self):
        """
        接收音频服务器发过来的数据并播放出来
        :return:
        """
        data = "".encode("utf-8")
        size = struct.calcsize("L")
        self.stream2 = self.py_audio.open(format=FORMAT,
                                         channels=CHANNELS,
                                         rate=RATE,
                                         output=True,
                                         frames_per_buffer=CHUNK)
        while True:
            while len(data) < size:
                data1 = self.sock.recv(81920)
                data = data + data1
            packed_size = data[:size]
            data = data[size:]
            msg_size = struct.unpack("L", packed_size)[0]
            while len(data) < msg_size:
                data = data + self.sock.recv(81920)

            zframe_data = data[:msg_size]
            data = data[msg_size:]
            frame_data = zlib.decompress(zframe_data)
            frame = pickle.loads(frame_data)

            for j in frame:
                self.stream2.write(j, CHUNK)


class VideoClient():
    """
    视频客户端类，捕获并展示摄像头数据，向视频服务器发送视频数据
    从视频服务器接收对方视频数据并展示
    """

    __slots__ = ['cap', 'sock', 'client', 'server']

    def __init__(self, host, port):
        """
        视频客户端类的初始化：连接视频服务器，分配两个线程分别用于发送数据和接收数据
        :param host: [string] 视频服务器IP地址
        :param port: [int] 视频服务器端口号
        """
        super(VideoClient, self).__init__()
        self.cap = None
        self.sock = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                self.sock.connect((host, port))
                break
            except:
                time.sleep(2)
                continue
        print("connection with server success")
        client = threading.Thread(target=self.send_video_data)
        server = threading.Thread(target=self.show_video_data)
        client.start()
        server.start()

    def __del__(self):
        """
        视频客户端类的析构，关闭连接，释放摄像头，关闭所有视频窗口
        :return:
        """
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        if self.sock is not None:
            self.sock.close()

    def send_video_data(self):
        """
        捕获摄像头数据并发送给视频服务器
        :return:
        """
        # 通过摄像头捕获视频
        try:
            self.cap = cv2.VideoCapture(0)
            # self.cap = cv2.VideoCapture(r"D:\\360data\重要数据\桌面\杂\《小王》.mp4")
        except:
            print('请检查摄像头是否可用')
        # 展示己方视频
        show_self = 1
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if show_self:
                cv2.namedWindow('Me', cv2.WINDOW_NORMAL)
                cv2.resizeWindow('Me', 200, 190)
                cv2.moveWindow('Me', int(SCREEN_WIDTH / 2) + 230, int(SCREEN_HEIGHT / 2)-5)
                cv2.imshow('Me', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    show_self = 0
                    cv2.destroyWindow('Me')
            frame = cv2.resize(frame, (0, 0), fx=0.2, fy=0.2)
            data = pickle.dumps(frame)
            zdata = zlib.compress(data, zlib.Z_BEST_COMPRESSION)

            try:
                self.sock.sendall(struct.pack("L", len(zdata)) + zdata)
            except Exception:
                continue

            for i in range(4):
                self.cap.read()

    def show_video_data(self):
        """
        接收视频服务器发过来的数据并显示出来
        :return:
        """
        data = "".encode("utf-8")
        size = struct.calcsize("L")
        cv2.namedWindow('Friend', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('Friend', 200, 190)
        cv2.moveWindow('Friend', int(SCREEN_WIDTH/2)+230, int(SCREEN_HEIGHT/2)-225)
        im = cv2.imread('./1.png')
        flag = 0
        while True:
            while len(data) < size:
                data1 = self.sock.recv(81920)
                # data_err = data1.decode()
                # if data_err == '00000000':
                #     flag = 1
                #     break
                # else:
                #     flag = 0
                data = data + data1
            # if flag == 1:
            #     cv2.imshow('Friend', im)
            #     if cv2.waitKey(1) & 0xFF == ord('q'):
            #         cv2.destroyWindow('Friend')
            #         break
            #     continue
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
                cv2.imshow('Friend', frame)
            except:
                cv2.imshow('Friend', im)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                cv2.destroyWindow('Friend')
                break


class LoginWindow(wx.Frame):
    """
    登录窗口类
    """

    __slots__ = ['sock', 'UserNameLabel',
                 'UserName', 'PassWordLabel',
                 'PassWord', 'LoginButton',
                 'QuitButton']

    def __init__(self, parent, id, title, size):
        """
        登录窗口类的初始化，添加控件并绑定事件
        :param parent: [int] 父窗口id
        :param id: [int] 窗口id
        :param title: [string] 窗口标题
        :param size: [tuple] 窗口大小
        """
        wx.Frame.__init__(self, parent, id, title)
        self.sock = None
        self.SetSize(size)
        self.Center()
        # 添加控件
        self.UserNameLabel = wx.StaticText(self, label="UserName", pos=(10, 35), size=(120, 25))
        self.UserName = wx.TextCtrl(self, pos=(120, 35), size=(150, 25))
        self.PassWordLabel = wx.StaticText(self, label="PassWord", pos=(10, 65), size=(120, 25))
        self.PassWord = wx.TextCtrl(self, pos=(120, 65), size=(150, 25), style=wx.TE_PASSWORD)
        self.LoginButton = wx.Button(self, label='Login', pos=(20, 125), size=(120, 30))
        self.QuitButton = wx.Button(self, label='Quit', pos=(160, 125), size=(120, 30))
        # 绑定按钮方法
        self.QuitButton.Bind(wx.EVT_BUTTON, self.quit)
        self.LoginButton.Bind(wx.EVT_BUTTON, self.login)
        self.Show()

    def quit(self, event):
        """
        退出登录框
        :param event:[string] 事件（鼠标点击）
        :return:
        """
        self.Close()

    def login(self, event):
        """
        登录，向服务器发出连接请求
        :param event: [string] 事件（鼠标点击）
        :return:
        """
        self.sock = socket(AF_INET, SOCK_STREAM)
        while True:
            try:
                self.sock.connect((HOST, PORT))
                break
            except:
                time.sleep(2)
                continue
        self.sock.send((str(self.UserName.GetLineText(0))).encode())
        response = self.sock.recv(1024).decode()
        if response != '200':
            self.show_dialog('Error from Server', response, (200, 100))
            self.sock.close()
            return
        else:
            self.Close()
            ChatWindow(None, 2, title='网上聊天                        '
                                      + str(self.UserName.GetLineText(0)), size=(500, 450), sock=self.sock)

    def show_dialog(self, title, content, size):
        """
        显示错误信息提示对话框
        :param title: [string] 对话框标题
        :param content: [string] 要显示的错误信息
        :param size: [tuple] 对话框大小
        :return:
        """
        dialog = wx.Dialog(self, title=title, size=size)
        dialog.Center()
        wx.StaticText(dialog, label=content)
        dialog.ShowModal()


class ChatWindow(wx.Frame):
    """
    聊天框类
    """

    __slots__ = ['sock', 'ChatWindow',
                 'MyMsgWindow', 'EnterButton',
                 'NoVideoButton', 'VideoButton',
                 'Video']

    def __init__(self, parent, id, title, size, sock):
        """
        聊天框类的初始化
        :param parent: [int] 父窗口id
        :param id: [int] 窗口id
        :param title: [string] 窗口标题
        :param size: [tuple] 窗口大小
        :param sock: [class] 与服务器的连接
        """
        wx.Frame.__init__(self, parent, id, title)
        self.sock = sock
        self.Video = None
        self.SetSize(size)
        self.Center()
        self.ShopWindow = wx.TextCtrl(self, pos=(30, 5), size=(425, 310), style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.MyMsgWindow = wx.TextCtrl(self, pos=(30, 325), size=(350, 50), style=wx.TE_MULTILINE)
        self.EnterButton = wx.Button(self, label="Enter", pos=(385, 325), size=(70, 50))
        # self.VideoButton = wx.Button(self, label="Video", pos=(30, 380), size=(80, 25))
        # self.NoVideoButton = wx.Button(self, label="No Video", pos=(115, 380), size=(80, 25))
        # 发送按钮绑定发送消息方法
        self.EnterButton.Bind(wx.EVT_BUTTON, self.send_msg)
        # self.NoVideoButton.Bind(wx.EVT_BUTTON, self.no_video)
        # self.VideoButton.Bind(wx.EVT_BUTTON, self.video)
        thread.start_new_thread(self.receive, ())
        self.Bind(wx.EVT_CLOSE, self.close)
        VideoClient(HOST, PORT2)
        AudioClient(HOST, PORT3)
        self.Show()

    def send_msg(self, event):
        """
        与Enter按钮绑定，向文字服务器发送文字数据并清空发送框中输入的信息
        :param event: [string] 事件（鼠标点击）
        :return:
        """
        while True:
            try:
                self.sock.send((str(self.MyMsgWindow.GetValue())).encode())
                self.MyMsgWindow.Clear()
                break
            except:
                time.sleep(2)
                continue

    def no_video(self, event):
        if self.Video is not None:
            self.Video.__del__()

    def video(self, event):
        if self.Video is None:
            self.Video = VideoClient(HOST, PORT2)

    def close(self, evt):
        """
        关闭聊天窗口
        :param evt: [class] 事件（鼠标点击）
        :return:
        """
        # self.s.send('/loginout'.encode())
        # self.sock.send('exit'.encode())
        if self.Video is not None:
            self.Video.__del__()
        # self.sock.close()
        # self.sock = None
        self.Close()
        evt.Skip()
        sys.exit()

    def receive(self):
        """
        接受服务端的消息并展示出来
        :param event: [string] 事件（鼠标点击）
        :return:
        """
        while True:
            sleep(0.2)
            result = self.sock.recv(1024).decode()
            if result == '404':
                self.sock.close()
                break
            if result != '' and result != '404':
                self.ShopWindow.AppendText('\n' + result)
        self.Close()
        sys.exit()


if __name__ == '__main__':
    app = wx.App()
    LoginWindow(None, -1, title="Login", size=(320, 250))
    app.MainLoop()
