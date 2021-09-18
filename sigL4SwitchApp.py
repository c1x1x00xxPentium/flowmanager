#!/usr/bin/python3

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls

from ryu.ofproto import ofproto_v1_3
from ryu.lib import ofctl_v1_3
from ryu.lib import ofctl_utils
from ryu import utils

from ryu.lib.packet import packet
from ryu.lib.packet import packet_base
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp

from ryu.lib import snortlib
import logging
import json
import array
import re
import time
import requests
from time import strftime, localtime, sleep
from logging.handlers import WatchedFileHandler

class sigL4switchApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'dpset': dpset.DPSet,'snortlib': snortlib.SnortLib}

    logname = 'flwmgr'
    logfile = 'flwmgr.log'
    tmplogname = 'sigapp'
    tmplogfile = 'sigapp.log'
    snortlogname = 'snortalert'
    snortlogfile = 'snortalert.log'
    mitigatelogname = 'mitigate'
    mitigatelogfile = 'mitigate.log'
    
    count_fin = 0 #1
    count_syn = 0 #2
    count_rst = 0 #4
    count_psh = 0 #8
    count_ack = 0 #16
    count_ackfin = 0 #17
    count_synack = 0 #18
    count_ackpsh = 0 #24
    count_ackpshfin = 0 #25

    count_echo_req = 0 #8,0
    count_echo_reply = 0 #0,0
    count_DU_Network = 0 #3,0
    count_DU_Host = 0 #3,1
    count_DU_Proto = 0 #3,2
    count_DU_Port = 0 #3,3

    custom = {
        'SYN': {
            'Block':{
                'idle': 500,
                'hard': 600,
                'priority': 2000,
            },
            'Drop': {
                'idle': 250,
                'hard': 300,
                'priority': 1900,
            }
        },
        'UDP': {
            'Block':{
                'idle': 500,
                'hard': 600,
                'priority': 2200,
            },
            'Drop': {
                'idle': 250,
                'hard': 300,
                'priority': 2100,
            }
        },
        'HTTP': {
            'Block':{
                'idle': 500,
                'hard': 600,
                'priority': 1800,
            },
            'Drop': {
                'idle': 250,
                'hard': 300,
                'priority': 1700,
            }
        },
        'ICMP': {
            'Block':{
                'idle': 500,
                'hard': 600,
                'priority': 1600,
            },
            'Drop': {
                'idle': 250,
                'hard': 300,
                'priority': 1500,
            }
        },
        # 'POD': {
        #     'Block':{
        #         'idle': 1003,
        #         'hard': 1203,
        #         'priority': 1650,
        #     },
        #     'Drop': {
        #         'idle': 803,
        #         'hard': 1003,
        #         'priority': 1550,
        #     }
        # },
        'Normal': {
            'ICMP': {
                'idle': 300,
                'hard': 600,
                'priority': 2,
            },
            'TCP':{
                'idle': 300,
                'hard': 600,
                'priority': 3,
            },
            'UDP': {
                'idle': 300,
                'hard': 600,
                'priority': 4,
            },
        },
    }

    def __init__(self, *args, **kwargs):
        super(sigL4switchApp, self).__init__(*args, **kwargs)

        self.mac_to_port = {}
        self.datapaths = {}
        self.alert_counter = {}
        self.tmpdata = {}
        
        self.dpset = kwargs['dpset']
        self.waiters = {}
        self.ofctl = ofctl_v1_3

        self.snort = kwargs['snortlib']
        self.snort_port = 3
        socket_config = {'unixsock': True}
        self.snort.set_config(socket_config)
        self.snort.start_socket_server()

        self.logger = self.get_logger(self.logname, self.logfile, 'INFO', 0)
        self.loggerlocal = self.get_tmplogger(
            self.tmplogname, self.tmplogfile, 'INFO', 0)
        self.snortlogger = self.get_snort_logger(
            self.snortlogname, self.snortlogfile, 'INFO', 0)
        self.mitigatelogger = self.get_mitigate_logger(
            self.mitigatelogname, self.mitigatelogfile, 'INFO', 0)

    # ==============================
    #  Utility Method ==============
    # ==============================

    def get_logger(self, logname, logfile, loglevel, propagate):
        """Create and return a logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='a')
        log_fmt = '%(asctime)s.%(msecs)06d\t%(levelname)-6s\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_tmplogger(self, logname, logfile, loglevel, propagate):
        """Create and return a local logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='w')
        log_fmt = '%(asctime)s.%(msecs)06d\t%(levelname)-6s\t[line %(lineno)d]\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_snort_logger(self, logname, logfile, loglevel, propagate):
        """Create and return a snort logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='w')
        log_fmt = '%(asctime)s.%(msecs)06d\t%(levelname)-8s\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_mitigate_logger(self, logname, logfile, loglevel, propagate):
        """Create and return a mitigate logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='w')
        log_fmt = '%(asctime)s.%(msecs)06d\t%(levelname)-8s\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%Y-%m-%d %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_packet_summary_new(self, content):
        pkt = packet.Packet(content)
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        ethtype = eth.ethertype
        dst = eth.dst
        src = eth.src
        message = '(src_mac={}, dst_mac={}, type=0x{:04x})'.format(src, dst, ethtype)
        return message

    def add_flow(self, datapath, priority, match, table_id, idle, hard, actions, buffer_id=None):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    idle_timeout=idle, hard_timeout=hard,
                                    instructions=inst, table_id=table_id)
        else:
            mod = parser.OFPFlowMod(datapath=datapath,
                                    priority=priority, match=match,
                                    idle_timeout=idle, hard_timeout=hard,
                                    instructions=inst, table_id=table_id)
        datapath.send_msg(mod)

    def packet_print(self, pkt):
        pkt = packet.Packet(array.array('B', pkt))

        _eth = pkt.get_protocol(ethernet.ethernet)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        _icmp = pkt.get_protocol(icmp.icmp)
        _tcp = pkt.get_protocol(tcp.tcp)
        _udp = pkt.get_protocol(udp.udp)

        full_msg = ""

        if _eth:
            full_msg += str("ethernet(dst=") + str(_eth.dst) + str(", src=") + str(_eth.src) + str(", ethertype=") + str(_eth.ethertype) + str(") ;;")
        if _ipv4:
            full_msg += str("ipv4(proto=") + str(_ipv4.proto) + str(", dst=") + str(_ipv4.dst) + str(", src=") + str(_ipv4.src) + str(") ;;")
        if _icmp:
            # self.logger.critical("Detail Packet\t%r", _icmp)
            full_msg += str("icmp(type=") + str(_icmp.type) + str(", code=") + str(_icmp.code) + str(")")
        if _tcp:
            # self.logger.critical("Detail Packet\t%r", _tcp)
            full_msg += str("tcp(dst_port=") + str(_tcp.dst_port) + str(", src_port=") + str(_tcp.src_port) + str(", bits=)") + str(_tcp.bits) + str(")")
        if _udp:
            # self.logger.critical("Detail Packet\t%r", _udp)
            full_msg += str("udp(dst_port=") + str(_udp.dst_port) + str(", src_port=") + str(_udp.src_port) + str(")")

        self.logger.info("Detail Alert\t{}".format(full_msg))
        self.loggerlocal.info(full_msg)
        self.snortlogger.critical(full_msg)

    def apply_mitigate(self, alert, msg, pkt, key):
        mode = ""
        if alert != "" and  alert == "Anomaly_Alert":

            # TODO : PERLU ubah jika nanti nilai probabilitas ( code Predict_Proba di DNN_Controller)
            if key not in self.alert_counter:
                self.alert_counter[key] = 1
                mode = "drop"
            elif key in self.alert_counter:
                self.alert_counter[key] += 1
                if self.alert_counter[key] > 500:
                    mode = "block"
                    self.alert_counter[key] = 0
                elif self.alert_counter[str(key.strip())] <= 500:
                    mode = ""

            ip_dst = pkt[3]
            ip_src = pkt[1]
            self.mitigatelogger.critical(str(pkt))

            if pkt[0].lower() == "icmp":
                if mode != "" and mode.lower() == "drop":
                    self.loggerlocal.info("Mitigate\tICMP DROP")
                    self.mitigatelogger.critical("ICMP DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ipv4_src=ip_src,ip_proto=1)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Drop']['idle'], hard=self.custom['ICMP']['Drop']['hard'], actions=_actions)
                    self.loggerlocal.info("Switch Handler\tAdded ICMP DROP RULE")
                    self.mitigatelogger.critical("Added ICMP DROP RULE {}".format(key))
                elif mode != "" and mode.lower() == "block":
                    self.loggerlocal.info("Mitigate\tICMP BLOCK")
                    self.mitigatelogger.critical("ICMP BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ip_proto=1)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Block']['idle'], hard=self.custom['ICMP']['Block']['hard'], actions=_actions)
                    self.loggerlocal.info("Switch Handler\tAdded ICMP BLOCK RULE")
                    self.mitigatelogger.critical("Added ICMP BLOCK RULE {}".format(key))
            elif pkt[0].lower() == "tcp":
                if mode != "" and mode.lower() == "drop":
                    self.loggerlocal.info("Mitigate\tSYN DROP")
                    self.mitigatelogger.critical("SYN DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ipv4_src=ip_src,ip_proto=6,tcp_dst=int(pkt[4]),)# tcp_src=_tcp.src_port, tcp_dst=_tcp.dst_port)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Drop']['idle'], hard=self.custom['SYN']['Drop']['hard'], actions=_actions)

                    self.loggerlocal.info("Switch Handler\tAdded SYN DROP RULE")
                    self.mitigatelogger.critical("Added SYN DROP RULE {}".format(key))
                elif mode != "" and mode.lower() == "block":
                    self.loggerlocal.info("Mitigate\tSYN BLOCK")
                    self.mitigatelogger.critical("SYN BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ip_proto=6,tcp_dst=int(pkt[4]))# tcp_src=_tcp.src_port, tcp_dst=_tcp.dst_port)

                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Block']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Block']['idle'], hard=self.custom['SYN']['Block']['hard'], actions=_actions)

                    self.loggerlocal.info("Switch Handler\tAdded SYN BLOCK RULE")
                    self.mitigatelogger.critical("Added SYN BLOCK RULE {}".format(key))
            elif pkt[0].lower() == "udp":
                if mode != "" and mode.lower() == "drop":
                    self.loggerlocal.info("Mitigate\tUDP DROP")
                    self.mitigatelogger.critical("UDP DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ipv4_src=ip_src,ip_proto=17,udp_dst=int(pkt[4]))# udp_src=_udp.src_port, udp_dst=_udp.dst_port)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Drop']['idle'], hard=self.custom['UDP']['Drop']['hard'], actions=_actions)
                    self.loggerlocal.info("Switch Handler\tAdded UDP DROP RULE")
                    self.mitigatelogger.critical("Added UDP DROP RULE {}".format(key))
                elif mode != "" and mode.lower() == "block":
                    self.loggerlocal.info("Mitigate\tUDP BLOCK")
                    self.mitigatelogger.critical("UDP BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=2048,ipv4_dst=ip_dst,ip_proto=17,udp_dst=int(pkt[4]))# udp_src=_udp.src_port, udp_dst=_udp.dst_port)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Block']['idle'], hard=self.custom['UDP']['Block']['hard'], actions=_actions)

                    self.loggerlocal.info("Switch Handler\tAdded UDP BLOCK RULE")
                    self.mitigatelogger.critical("Added UDP BLOCK RULE {}".format(key))

        elif alert != "" and (alert == "ICMP_Flood" or alert == "SYN_Flood" or alert == "UDP_Flood" or alert == "Destination_Port_Unreachable"):
            _eth = pkt.get_protocol(ethernet.ethernet)
            _ipv4 = pkt.get_protocol(ipv4.ipv4)
            _icmp = pkt.get_protocol(icmp.icmp)
            _tcp = pkt.get_protocol(tcp.tcp)
            _udp = pkt.get_protocol(udp.udp)

            if key not in self.alert_counter:
                self.alert_counter[key] = 1
                # mode = "drop"
            elif key in self.alert_counter:
                self.alert_counter[key] += 1
                # if self.alert_counter[key] > 500:
                #     # mode = "block"
                #     self.alert_counter[key] = 0
                # elif self.alert_counter[str(key.strip())] <= 500:
                #     mode = ""

            self.logger.info("Mitigate\t{}".format(json.dumps(self.alert_counter, sort_keys=True)))
            self.loggerlocal.info("{}".format(json.dumps(self.alert_counter, sort_keys=True)))
            self.mitigatelogger.warning("{}".format(key))

            if alert == "ICMP_Flood" or alert == "Destination_Port_Unreachable":
                if msg.lower() == "drop": 
                    self.logger.info("Mitigate\tICMP DROP")
                    self.loggerlocal.info("Mitigate\tICMP DROP")
                    self.mitigatelogger.warning("ICMP DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Drop']['idle'], hard=self.custom['ICMP']['Drop']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded ICMP DROP RULE")
                    self.loggerlocal.info("Mitigate\tAdded ICMP DROP RULE")
                    self.mitigatelogger.warning("Added ICMP DROP RULE {}".format(key))
                elif msg.lower() == "block": 
                    self.logger.info("Mitigate\tICMP BLOCK")
                    self.loggerlocal.info("Mitigate\tICMP BLOCK")
                    self.mitigatelogger.warning("ICMP BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Block']['idle'], hard=self.custom['ICMP']['Block']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded ICMP BLOCK RULE")
                    self.loggerlocal.info("Mitigate\tAdded ICMP BLOCK RULE")
                    self.mitigatelogger.warning("Added ICMP BLOCK RULE {}".format(key))

            if alert == "SYN_Flood" or alert == "No_ACK" :
                if msg.lower() == "drop": 
                    self.logger.info("Mitigate\tSYN DROP")
                    self.loggerlocal.info("Mitigate\tSYN DROP")
                    self.mitigatelogger.warning("SYN DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port, tcp_flags=_tcp.bits) #tcp_src=_tcp.src_port,
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Drop']['idle'], hard=self.custom['SYN']['Drop']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded SYN DROP RULE")
                    self.loggerlocal.info("Mitigate\tAdded SYN DROP RULE")
                    self.mitigatelogger.warning("Added SYN DROP RULE {}".format(key))
                elif msg.lower() == "block": 
                    self.logger.info("Mitigate\tSYN BLOCK")
                    self.loggerlocal.info("Mitigate\tSYN BLOCK")
                    self.mitigatelogger.warning("SYN BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port, tcp_flags=_tcp.bits) #tcp_src=_tcp.src_port,

                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Block']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Block']['idle'], hard=self.custom['SYN']['Block']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded SYN BLOCK RULE")
                    self.loggerlocal.info("Mitigate\tAdded SYN BLOCK RULE")
                    self.mitigatelogger.warning("Added SYN BLOCK RULE {}".format(key))

            if alert == "UDP_Flood":# or alert == "Destination_Port_Unreachable" :
                if msg.lower() == "drop": 
                    self.logger.info("Mitigate\tUDP DROP")
                    self.loggerlocal.info("Mitigate\tUDP DROP")
                    self.mitigatelogger.warning("UDP DROP")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto,  udp_dst=_udp.dst_port) #udp_src=_udp.src_port,
                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Drop']['idle'], hard=self.custom['UDP']['Drop']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded UDP DROP RULE")
                    self.loggerlocal.info("Mitigate\tAdded UDP DROP RULE")
                    self.mitigatelogger.warning("Added UDP DROP RULE {}".format(key))
                elif msg.lower() == "block": 
                    self.logger.info("Mitigate\tUDP BLOCK")
                    self.loggerlocal.info("Mitigate\tUDP BLOCK")
                    self.mitigatelogger.warning("UDP BLOCK")
                    _datapath = self.datapaths[2]
                    _parser = _datapath.ofproto_parser
                    _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, udp_dst=_udp.dst_port) #udp_src=_udp.src_port,

                    _actions = []

                    self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Block']['idle'], hard=self.custom['UDP']['Block']['hard'], actions=_actions)

                    self.logger.info("Mitigate\tAdded UDP BLOCK RULE")
                    self.loggerlocal.info("Mitigate\tAdded UDP BLOCK RULE")
                    self.mitigatelogger.warning("Added UDP BLOCK RULE {}".format(key))
            
            # ORI
            # if alert == "ICMP_Flood" or alert == "Destination_Port_Unreachable":
            #     if mode != "" and mode.lower() == "drop": 
            #         self.logger.info("Mitigate\tICMP DROP")
            #         self.loggerlocal.info("Mitigate\tICMP DROP")
            #         self.mitigatelogger.warning("ICMP DROP")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Drop']['idle'], hard=self.custom['ICMP']['Drop']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded ICMP DROP RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded ICMP DROP RULE")
            #         self.mitigatelogger.warning("Added ICMP DROP RULE")
            #     elif mode != "" and mode.lower() == "block": 
            #         self.logger.info("Mitigate\tICMP BLOCK")
            #         self.loggerlocal.info("Mitigate\tICMP BLOCK")
            #         self.mitigatelogger.warning("ICMP BLOCK")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['ICMP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['ICMP']['Block']['idle'], hard=self.custom['ICMP']['Block']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded ICMP BLOCK RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded ICMP BLOCK RULE")
            #         self.mitigatelogger.warning("Added ICMP BLOCK RULE")

            # if alert == "SYN_Flood" or alert == "No_ACK" :
            #     if mode != "" and mode.lower() == "drop": 
            #         self.logger.info("Mitigate\tSYN DROP")
            #         self.loggerlocal.info("Mitigate\tSYN DROP")
            #         self.mitigatelogger.warning("SYN DROP")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port, tcp_flags=_tcp.bits) #tcp_src=_tcp.src_port,
            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Drop']['idle'], hard=self.custom['SYN']['Drop']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded SYN DROP RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded SYN DROP RULE")
            #         self.mitigatelogger.warning("Added SYN DROP RULE")
            #     elif mode != "" and mode.lower() == "block": 
            #         self.logger.info("Mitigate\tSYN BLOCK")
            #         self.loggerlocal.info("Mitigate\tSYN BLOCK")
            #         self.mitigatelogger.warning("SYN BLOCK")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port, tcp_flags=_tcp.bits) #tcp_src=_tcp.src_port,

            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['SYN']['Block']['priority'], match=_match,table_id=0, idle=self.custom['SYN']['Block']['idle'], hard=self.custom['SYN']['Block']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded SYN BLOCK RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded SYN BLOCK RULE")
            #         self.mitigatelogger.warning("Added SYN BLOCK RULE")

            # if alert == "UDP_Flood":# or alert == "Destination_Port_Unreachable" :
            #     if mode != "" and mode.lower() == "drop": 
            #         self.logger.info("Mitigate\tUDP DROP")
            #         self.loggerlocal.info("Mitigate\tUDP DROP")
            #         self.mitigatelogger.warning("UDP DROP")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,ip_proto=_ipv4.proto,  udp_dst=_udp.dst_port) #udp_src=_udp.src_port,
            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Drop']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Drop']['idle'], hard=self.custom['UDP']['Drop']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded UDP DROP RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded UDP DROP RULE")
            #         self.mitigatelogger.warning("Added UDP DROP RULE")
            #     elif mode != "" and mode.lower() == "block": 
            #         self.logger.info("Mitigate\tUDP BLOCK")
            #         self.loggerlocal.info("Mitigate\tUDP BLOCK")
            #         self.mitigatelogger.warning("UDP BLOCK")
            #         _datapath = self.datapaths[2]
            #         _parser = _datapath.ofproto_parser
            #         _match = _parser.OFPMatch(eth_type=_eth.ethertype,ipv4_dst=_ipv4.dst,ip_proto=_ipv4.proto, udp_dst=_udp.dst_port) #udp_src=_udp.src_port,

            #         _actions = []

            #         self.add_flow(datapath=_datapath, priority=self.custom['UDP']['Block']['priority'], match=_match,table_id=0, idle=self.custom['UDP']['Block']['idle'], hard=self.custom['UDP']['Block']['hard'], actions=_actions)

            #         self.logger.info("Switch Handler\tAdded UDP BLOCK RULE")
            #         self.loggerlocal.info("Switch Handler\tAdded UDP BLOCK RULE")
            #         self.mitigatelogger.warning("Added UDP BLOCK RULE")
    
    # ==============================
    #  Event Handlers ==============
    # ==============================

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def event_state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER and (ev.datapath.id != 2 or ev.datapath.id != 3):
            if datapath.id == 4 or datapath.id == 5:
                return
            if datapath.id not in self.datapaths:
                self.logger.info(
                    'Switch Handler\tregister datapath: %016x', datapath.id)
                self.loggerlocal.info(
                    'register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.info(
                    'Switch Handler\tunregister datapath: %016x', datapath.id)
                self.loggerlocal.info(
                    'unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def event_switch_enter_handler(self, ev):
        dp = ev.dp
        if ev.enter == True and (ev.dp.id != 2 or ev.dp.id != 3):
            self.logger.info("Switch Handler\tSwitch connected %s", dp)
            self.loggerlocal.info("switch connected %s", dp)
        elif ev.enter == True and (ev.dp.id == 2 or ev.dp.id == 3):
            self.logger.info("Switch Handler\tPRE Rest Router connected %s", dp)
            self.loggerlocal.info("PRE Rest Router connected %s", dp)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def event_switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info("Switch Handler\tGet connection on : {}".format(ev.msg.datapath.address))
        self.loggerlocal.info(ev.msg.datapath.address)

        # install table-miss flow entry especially for datapath.id 4 and 5
        if datapath.id == 4 or datapath.id == 5:
            match = parser.OFPMatch()
            actions = [parser.OFPActionOutput(ofproto.OFPP_NORMAL)]
            self.add_flow(datapath=datapath, priority=1, match=match,
                table_id=0, idle=0, hard=0, actions=actions)

        # install table-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]

        self.add_flow(datapath=datapath, priority=0, match=match,
                      table_id=0, idle=0, hard=0, actions=actions)

        '''
        # ICMP drop flow
        match = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_ICMP)
        mod = parser.OFPFlowMod(datapath=datapath, priority=2,
                                match=match, table_id=0, idle_timeout=1, hard_timeout=5)
        datapath.send_msg(mod)

        # TCP drop flow
        match = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_TCP)
        mod = parser.OFPFlowMod(datapath=datapath, priority=3,
                                match=match, table_id=0, idle_timeout=2, hard_timeout=5)
        datapath.send_msg(mod)

        # UDP drop flow
        match = parser.OFPMatch(
            eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_UDP)
        mod = parser.OFPFlowMod(datapath=datapath, priority=4,
                                match=match, table_id=0, idle_timeout=3, hard_timeout=5)
        datapath.send_msg(mod)
        '''

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def event_packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.info("PacketIn\tpacket truncated: only %s of %s bytes",
                             ev.msg.msg_len, ev.msg.total_len)

        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        if eth.ethertype == ether_types.ETH_TYPE_IPV6:
            # ignore ipv6 packet
            return

        dst = eth.dst
        src = eth.src
        dpid = datapath.id

        self.mac_to_port.setdefault(dpid, {})

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        # _actions = [parser.OFPActionOutput(out_port), parser.OFPActionOutput(self.snort_port)]
        _actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:

            # check IP Protocol and create a match for IP
            if eth.ethertype == ether_types.ETH_TYPE_IP:
                ip = pkt.get_protocol(ipv4.ipv4)
                srcip = ip.src
                dstip = ip.dst
                protocol = ip.proto
                _table_id = 0

                # if ICMP Protocol
                if protocol == in_proto.IPPROTO_ICMP:
                    i = pkt.get_protocol(icmp.icmp)
                    self.logger.info(
                        "PacketIn\tICMP Packet ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s (type : %s , code : %s)",
                        dpid, in_port, src, dst, srcip, dstip, i.type, i.code)
                    ## self.logger.critical("Detail Packet\t%r", i)
                    self.loggerlocal.info(
                        "Local ICMP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s (type : %s , code : %s)",
                        dpid, in_port, src, dst, srcip, dstip, i.type, i.code)
                    _match = parser.OFPMatch(eth_type=eth.ethertype, # in_port=in_port,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol, icmpv4_type=i.type, icmpv4_code=i.code)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = self.custom['Normal']['ICMP']['priority']
                    _idle_timeout = self.custom['Normal']['ICMP']['idle']
                    _hard_timeout = self.custom['Normal']['ICMP']['hard']

                    if i.type == 8 and i.code == 0:
                        self.count_echo_req += 1
                    elif i.type == 0 and i.code == 0:
                        self.count_echo_reply += 1
                    elif i.type == 3 and i.code == 0:
                        self.count_DU_Network += 1
                    elif i.type == 3 and i.code == 1:
                        self.count_DU_Host += 1
                    elif i.type == 3 and i.code == 2:
                        self.count_DU_Proto += 1
                    elif i.type == 3 and i.code == 3:
                        self.count_DU_Port += 1

                    self.logger.info("ICMP\treq : %s ;; reply : %s ;; DU_Network : %s ;; DU_Host : %s ;; DU_Proto : %s ;; DU_Port : %s", self.count_echo_req, self.count_echo_reply, self.count_DU_Network, self.count_DU_Host, self.count_DU_Proto, self.count_DU_Port)

                # if TCP Protocol
                elif protocol == in_proto.IPPROTO_TCP:
                    t = pkt.get_protocol(tcp.tcp)
                    self.logger.info(
                        "PacketIn\tTCP Packet ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s (bits: %s)",
                        dpid, in_port, src, dst, srcip, dstip, t.src_port, t.dst_port, t.bits)
                    ## self.logger.critical("Detail Packet\t%r", t)
                    self.loggerlocal.info(
                        "Local TCP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s (bits: %s)",
                        dpid, in_port, src, dst, srcip, dstip, t.src_port, t.dst_port, t.bits)
                    _match = parser.OFPMatch(eth_type=eth.ethertype,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol, tcp_flags=t.bits)#,tcp_src=t.src_port)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = self.custom['Normal']['TCP']['priority']
                    _idle_timeout = self.custom['Normal']['TCP']['idle']
                    _hard_timeout = self.custom['Normal']['TCP']['hard']

                    if t.bits == 1:
                        self.count_fin += 1
                    elif t.bits == 2:
                        self.count_syn += 1
                    elif t.bits == 4:
                        self.count_rst += 1
                    elif t.bits == 8:
                        self.count_psh += 1
                    elif t.bits == 16:
                        self.count_ack += 1
                    elif t.bits == 17:
                        self.count_ackfin += 1
                    elif t.bits == 18:
                        self.count_synack += 1
                    elif t.bits == 24:
                        self.count_ackpsh += 1
                    elif t.bits == 25:
                        self.count_ackpshfin += 1

                    self.logger.info("TCP\tfin : %s ;; syn : %s ;; rst : %s ;; psh : %s ;; ack : %s ;; ackfin : %s ;; synack : %s ;; ackpsh : %s ;; ackpshfin : %s", self.count_fin, self.count_syn, self.count_rst, self.count_psh, self.count_ack, self.count_ackfin, self.count_synack, self.count_ackpsh, self.count_ackpshfin)

                # If UDP Protocol
                elif protocol == in_proto.IPPROTO_UDP:
                    u = pkt.get_protocol(udp.udp)
                    self.logger.info(
                        "PacketIn\tUDP Packet ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s (total_length : %s)",
                        dpid, in_port, src, dst, srcip, dstip, u.src_port, u.dst_port, u.total_length)
                    ## self.logger.critical("Detail Packet\t%r", u)
                    self.loggerlocal.info(
                        "Local UDP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s (total_length : %s)",
                        dpid, in_port, src, dst, srcip, dstip, u.src_port, u.dst_port, u.total_length)
                    _match = parser.OFPMatch(eth_type=eth.ethertype,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol)#, udp_src=u.src_port)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = self.custom['Normal']['UDP']['priority']
                    _idle_timeout = self.custom['Normal']['UDP']['idle']
                    _hard_timeout = self.custom['Normal']['UDP']['hard']

                # The reason for packet_in
                reason_msg = {ofproto.OFPR_NO_MATCH: "NO MATCH",ofproto.OFPR_ACTION: "ACTION",ofproto.OFPR_INVALID_TTL: "INVALID TTL"}
                reason = reason_msg.get(msg.reason, 'UNKNOWN')
                now = time.strftime('%Y-%m-%d %H:%M:%S')
                match = msg.match.items()
                log = list(map(str, [now, 'PacketIn', datapath.id, msg.table_id, reason, match,
                        hex(msg.buffer_id), msg.cookie, self.get_packet_summary_new(msg.data)]))
                self.loggerlocal.info(log)

                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.add_flow(datapath=datapath, priority=_priority, match=_match, table_id=_table_id,idle=_idle_timeout, hard=_hard_timeout, actions=_actions, buffer_id=msg.buffer_id)
                    return
                else:
                    _table_id = 0
                    self.add_flow(datapath=datapath, priority=_priority, match=_match,table_id=_table_id, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=_actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(snortlib.EventAlert, MAIN_DISPATCHER)
    def event_dump_alert_handler(self, ev):
        msg = ev.msg
        # alertmsg = msg.alertmsg[0].decode('ascii')
        alert = str(msg.alertmsg[0].decode()).rstrip('\x00')
        pkt = packet.Packet(array.array('B', msg.pkt))

        _eth = pkt.get_protocol(ethernet.ethernet)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        _icmp = pkt.get_protocol(icmp.icmp)
        _tcp = pkt.get_protocol(tcp.tcp)
        _udp = pkt.get_protocol(udp.udp)

        self.logger.info('Alert\talertmsg: %s' % ''.join(str(alert)))
        self.snortlogger.critical('alertmsg: %s' % ''.join(str(alert)))
        self.loggerlocal.info('alertmsg: %s' % ''.join(str(alert)))
        self.packet_print(msg.pkt)

        match = re.search("^.{0,300}", alert)
        match1 = re.split(" ", match.group(0))

        if ("1" in match1) :# and ("[dst]" in match1): # Level 1 == DROP
            if ("ICMP_Flood" in match1) or ("Destination_Port_Unreachable" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},icmp_type={},icmp_code={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_icmp.type,_icmp.code)
                self.apply_mitigate("ICMP_Flood","drop",pkt,alert_key)

            if ("SYN_Flood" in match1) or ("No_ACK" in match1) or ("TCP_RST" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},tcp_dst={},bits={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_tcp.dst_port,_tcp.bits)
                self.apply_mitigate("SYN_Flood","drop",pkt,alert_key)

            if ("UDP_Flood" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},udp_dst={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_udp.dst_port)
                self.apply_mitigate("UDP_Flood","drop",pkt,alert_key)
        
        elif ("2" in match1) :# and ("[dst]" in match1): # Level 2 == BLOCK
            if ("ICMP_Flood" in match1) or ("Destination_Port_Unreachable" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},icmp_type={},icmp_code={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_icmp.type,_icmp.code)
                self.apply_mitigate("ICMP_Flood","block",pkt,alert_key)

            if ("SYN_Flood" in match1) or ("No_ACK" in match1) or ("TCP_RST" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},tcp_dst={},bits={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_tcp.dst_port,_tcp.bits)
                self.apply_mitigate("SYN_Flood","block",pkt,alert_key)

            if ("UDP_Flood" in match1):
                alert_key = "eth_type={},ipv4_dst={},ipv4_src={},ip_proto={},udp_dst={}".format(_eth.ethertype,_ipv4.dst,_ipv4.src,_ipv4.proto,_udp.dst_port)
                self.apply_mitigate("UDP_Flood","block",pkt,alert_key)
        
        # if ("ICMP_Flood" in match1) or ("Destination_Port_Unreachable" in match1):
        #     alert_key = "eth_type={},ipv4_dst={},ip_proto={},icmp_type={},icmp_code={}".format(_eth.ethertype,_ipv4.dst,_ipv4.proto,_icmp.type,_icmp.code)
        #     self.apply_mitigate("ICMP_Flood",ev.msg,pkt,alert_key)

        # if ("SYN_Flood" in match1) or ("No_ACK" in match1) or ("TCP_RST" in match1):
        #     alert_key = "eth_type={},ipv4_dst={},ip_proto={},tcp_dst={},bits={}".format(_eth.ethertype,_ipv4.dst,_ipv4.proto,_tcp.dst_port,_tcp.bits)
        #     self.apply_mitigate("SYN_Flood",ev.msg,pkt,alert_key)

        # if ("UDP_Flood" in match1):
        #     alert_key = "eth_type={},ipv4_dst={},ip_proto={},udp_dst={}".format(_eth.ethertype,_ipv4.dst,_ipv4.proto,_udp.dst_port)
        #     self.apply_mitigate("UDP_Flood",ev.msg,pkt,alert_key)
            
        # if ("Network-Unreachable" in match1) or ("Host-Unreachable" in match1) or ("Protocol-Unreachable" in match1) or ("Port-Unreachable" in match1) or ("Destination-Unreachable" in match1):
        #     pass

        # self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, sort_keys=True)))
        # self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))
