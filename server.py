#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018-05-30 19:22 下午
# @Author  : HuangLi
# @Contact : lhuang9703@gmail.com
# @Site    :
# @File    : server.py
# @Software: PyCharm Community Edition

from __future__ import absolute_import
from __future__ import print_function

import sys
from time import sleep
from socket import *
import json
import threading
from concurrent.futures import ThreadPoolExecutor


def get_config():
    """
    获取配置信息
    :return: [dict] 配置文件的数据
    """
    with open('./config.json') as configfile:
        config = json.load(configfile)
    return config

HOST = get_config()['server']['bind_ip']
# 文字服务器监听端口
PORT1 = get_config()['server']['text_port']
# 视频服务器监听端口
PORT2 = get_config()['server']['video_port']

# 实现从连接con到用户的映射字典，用于判断每个连接当前登入的用户
con2user = {}


class Server(object):
    """
    文字服务器类，客户端彼此发送的文字数据需经过该服务器转发
    """

    __slots__ = ['address1', 'sock1']

    def __init__(self, port):
        """
        Server类的初始化：绑定并监听端口，等待客户端连接
        :param port: [int] 文字服务器监听端口号
        """
        self.address1 = ("", port)
        self.sock1 = socket(AF_INET, SOCK_STREAM)
        self.sock1.bind(self.address1)
        self.sock1.listen(10)
        print("text server start at:{},waiting for connection...".format(port))
        self.run_server()

    def __del__(self):
        """
        Server类的析构，关闭套接字
        """
        if self.sock1 is not None:
            self.sock1.close()

    def run_server(self):
        """
        运行服务器：创建线程池pool，为每个客户端分配一个处理线程，
        线程使用self.tcp_link函数处理客户端数据
        :return:
        """
        pool = ThreadPoolExecutor(100)
        while True:
            try:
                con1, addr1 = self.sock1.accept()
            except:
                sleep(2)
                continue
            pool.submit(self.tcp_link, con1, addr1)

    def tcp_link(self, con, addr):
        """
        处理客户端发来的文字数据，将文字数据转发给所有客户端
        :param con: [class] 发来文字数据的客户端连接类
        :param addr: [string] 发来文字数据的客户端地址
        :return:
        """
        print("connected by {}".format(addr))

        data = con.recv(1024).decode()
        # 在con2user字典中注册该用户并发送‘200’成功连接状态码
        con2user[con] = data
        con.send('200'.encode())

        while True:
            data = con.recv(1024).decode()
            if data == b"":
                print('close')
                break
            if data == 'exit':
                con.send('404'.encode())
                break
            for user in con2user:
                user.send((con2user[con] + ":\n" + ' '*4 + data + "\n").encode())
        con.close()


if __name__ == '__main__':
    connection1 = Server(PORT1)
