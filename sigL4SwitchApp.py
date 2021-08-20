from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller import dpset
from ryu.controller.handler import CONFIG_DISPATCHER
from ryu.controller.handler import MAIN_DISPATCHER
from ryu.controller.handler import DEAD_DISPATCHER
from ryu.controller.handler import HANDSHAKE_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import packet_base
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types

from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import icmp
from ryu.lib.packet import tcp
from ryu.lib.packet import udp

from ryu.topology import event
from ryu.topology.api import get_all_switch, get_all_link, get_all_host

from ryu.lib import snortlib
import logging
import json
import array
import re
import time
from time import strftime, localtime, sleep
from logging.handlers import WatchedFileHandler

class sigL4switchApp(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'snortlib': snortlib.SnortLib}

    logname = 'flwmgr'
    logfile = 'flwmgr.log'
    tmplogname = 'sigapp'
    tmplogfile = 'sigapp.log'
    snortlogname = 'snortalert'
    snortlogfile = 'snortalert.log'

    def __init__(self, *args, **kwargs):
        super(sigL4switchApp, self).__init__(*args, **kwargs)
        self.mac_to_port = {}
        self.datapaths = {}
        self.alert_counter = {}

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

    def get_logger(self, logname, logfile, loglevel, propagate):
        """Create and return a logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='a')
        log_fmt = '%(asctime)s\t%(levelname)-8s\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%d-%b-%y %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_tmplogger(self, logname, logfile, loglevel, propagate):
        """Create and return a logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='w')
        log_fmt = '%(asctime)s\t%(levelname)-6s\t[line %(lineno)d]\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%d-%b-%y %H:%M:%S'))
        logger.addHandler(logger_handler)
        logger.propagate = propagate
        logger.setLevel(loglevel)
        return logger

    def get_snort_logger(self, logname, logfile, loglevel, propagate):
        """Create and return a snort logger object."""
        logger = logging.getLogger(logname)
        logger_handler = WatchedFileHandler(logfile, mode='w')
        log_fmt = '%(asctime)s\t%(levelname)-8s\t%(message)s'
        logger_handler.setFormatter(
            logging.Formatter(log_fmt, '%d-%b-%y %H:%M:%S'))
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

        try:
            _ipv4 = pkt.get_protocols(ipv4.ipv4)
            # self.logger.info(_ipv4)
            try:
                _icmp = pkt.get_protocols(icmp.icmp)
                # self.logger.info(_icmp)
            except Exception as error1:
                print(error1)
            try:
                _tcp = pkt.get_protocols(tcp.tcp)
                # self.logger.info(_tcp)
            except Exception as error2:
                print(error2)
            try:
                _udp = pkt.get_protocols(udp.udp)
                # self.logger.info(_udp)
            except Exception as error3:
                print(error3)
        except Exception as error:
            print(error)
        finally:
            return message

        if _ipv4:
            src = _ipv4.src
            dst = _ipv4.dst
            proto = _ipv4.proto
            message += '\n(ip_src={}, ip_dst={}, ip_proto={})'.format(src,dst, proto)
        if _icmp:
            type = _icmp.type
            code = _icmp.code
            message += '\n(icmp_code={}, icmp_type={})'.format(type,code)
        if _tcp:
            sport = _tcp.src_port
            dport = _tcp.dst_port
            message += '\n(tcp_sport={}, tcp_dport={})'.format(sport,dport)
        if _udp:
            sport = _udp.src_port
            dport = _udp.dst_port
            message += '\n(udp_sport={}, udp_dport={})'.format(sport,dport)
        return message

    @set_ev_cls(dpset.EventDP, dpset.DPSET_EV_DISPATCHER)
    def _event_switch_enter_handler(self, ev):
        dp = ev.dp
        if ev.enter == True and (ev.dp.id != 2 or ev.dp.id != 3):
            self.logger.info("Switch Handler\tSwitch connected %s", dp)
            self.loggerlocal.info("switch connected %s", dp)
        elif ev.enter == True and (ev.dp.id == 2 or ev.dp.id == 3):
            self.logger.info("Switch Handler\tPRE Rest Router connected %s", dp)
            self.loggerlocal.info("PRE Rest Router connected %s", dp)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        self.logger.info("Switch Handler\t{}".format(ev.msg.datapath.address))
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

        # ICMP drop flow
        # match = parser.OFPMatch(
        #     eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_ICMP)
        # mod = parser.OFPFlowMod(datapath=datapath, priority=2,
        #                         match=match, table_id=0, idle_timeout=1, hard_timeout=5)
        # datapath.send_msg(mod)

        # TCP drop flow
        # match = parser.OFPMatch(
        #     eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_TCP)
        # mod = parser.OFPFlowMod(datapath=datapath, priority=3,
        #                         match=match, table_id=0, idle_timeout=2, hard_timeout=5)
        # datapath.send_msg(mod)

        # UDP drop flow
        # match = parser.OFPMatch(
        #     eth_type=ether_types.ETH_TYPE_IP, ip_proto=in_proto.IPPROTO_UDP)
        # mod = parser.OFPFlowMod(datapath=datapath, priority=4,
        #                         match=match, table_id=0, idle_timeout=3, hard_timeout=5)
        # datapath.send_msg(mod)

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

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
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

        # self.logger.info(json.dumps(
        #     self.mac_to_port, indent=2, sort_keys=True))
        # print(json.dumps(self.mac_to_port, indent=2, sort_keys=True))

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
                        "PacketIn\tLocal ICMP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s",
                        dpid, in_port, src, dst, srcip, dstip)
                    self.loggerlocal.info(
                        "Local ICMP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s",
                        dpid, in_port, src, dst, srcip, dstip)
                    _match = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol, icmpv4_type=i.type, icmpv4_code=i.code)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = 2
                    _idle_timeout = 1800
                    _hard_timeout = 3000

                # if TCP Protocol
                elif protocol == in_proto.IPPROTO_TCP:
                    t = pkt.get_protocol(tcp.tcp)
                    self.logger.info(
                        "PacketIn\tLocal TCP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s",
                        dpid, in_port, src, dst, srcip, dstip, t.src_port, t.dst_port)
                    self.loggerlocal.info(
                        "Local TCP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s",
                        dpid, in_port, src, dst, srcip, dstip, t.src_port, t.dst_port)
                    _match = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol, tcp_dst=t.dst_port)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = 3
                    _idle_timeout = 1800
                    _hard_timeout = 3000

                # If UDP Protocol
                elif protocol == in_proto.IPPROTO_UDP:
                    u = pkt.get_protocol(udp.udp)
                    self.logger.info(
                        "PacketIn\tLocal UDP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s",
                        dpid, in_port, src, dst, srcip, dstip, u.src_port, u.dst_port)
                    self.loggerlocal.info(
                        "Local UDP Packet Found ;; [DPID : %s , atPort : %s] ;; src : %s >> dst : %s ;; srcip : %s >> dstip : %s ;; sport : %s >> dport : %s",
                        dpid, in_port, src, dst, srcip, dstip, u.src_port, u.dst_port)
                    _match = parser.OFPMatch(in_port=in_port, eth_type=eth.ethertype,
                        eth_dst=dst, eth_src=src,
                        ipv4_dst=dstip, ipv4_src=srcip,
                        ip_proto=protocol, udp_dst=u.dst_port)
                    # _actions = [parser.OFPActionOutput(out_port)]

                    _priority = 4
                    _idle_timeout = 1800
                    _hard_timeout = 3000

                # verify if we have a valid buffer_id, if yes avoid to send both
                # flow_mod & packet_out

                # The reason for packet_in
                reason_msg = {ofproto.OFPR_NO_MATCH: "NO MATCH",
                                ofproto.OFPR_ACTION: "ACTION",
                                ofproto.OFPR_INVALID_TTL: "INVALID TTL"
                            }
                reason = reason_msg.get(msg.reason, 'UNKNOWN')
                now = time.strftime('%b %d %H:%M:%S')
                match = msg.match.items()
                log = list(map(str, [now, 'PacketIn', datapath.id, msg.table_id, reason, match,
                        hex(msg.buffer_id), msg.cookie, self.get_packet_summary_new(msg.data)]))
                self.logger.info("PacketIn\n{}".format(log))
                self.loggerlocal.info(log)

                if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                    self.logger.critical("PacketIn\tWith BufferID : {}".format(msg.buffer_id))
                    # self.loggerlocal.critical("With BufferID")
                    self.add_flow(datapath=datapath, priority=_priority, match=_match, table_id=_table_id,
                                  idle=_idle_timeout, hard=_hard_timeout, actions=_actions, buffer_id=msg.buffer_id)
                    return
                else:
                    self.logger.critical("PacketIn\tWithout BufferID")
                    # self.loggerlocal.critical("Without BufferID")
                    _priority = 1
                    _table_id = 0
                    self.add_flow(datapath=datapath, priority=_priority, match=_match,
                                  table_id=_table_id, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

        data = None
        # _actions = [parser.OFPActionOutput(out_port)]
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        self.logger.critical("PacketIn\tMsg.Actions : {}".format(_actions))
        # self.loggerlocal.critical("Msg.Actions : {}".format(_actions))
        self.logger.critical("PacketIn\tMsg.Data : {}".format(data))
        # self.loggerlocal.critical("Msg.Data : {}".format(data))

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=_actions, data=data)
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
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

    def packet_print(self, pkt):
        pkt = packet.Packet(array.array('B', pkt))
        _eth = pkt.get_protocol(ethernet.ethernet)
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        _icmp = pkt.get_protocol(icmp.icmp)
        _tcp = pkt.get_protocol(tcp.tcp)
        _udp = pkt.get_protocol(udp.udp)
        full_msg = ""

        if _eth:
            full_msg += str(_eth)+str(" ;; ")
        if _ipv4:
            full_msg += str(_ipv4)+str(" ;; ")
        if _icmp:
            full_msg += str(_icmp)
        if _tcp:
            full_msg += str(_tcp)
        if _udp:
            full_msg += str(_udp)

        self.logger.warning("Detail Alert\t{}".format(full_msg))
        self.loggerlocal.warning(full_msg)
        self.snortlogger.info(full_msg)

    @set_ev_cls(snortlib.EventAlert, MAIN_DISPATCHER)
    def _dump_alert(self, ev):
        msg = ev.msg
        alertmsg = msg.alertmsg[0].decode('ascii')
        alert = str(msg.alertmsg)

        pkt = packet.Packet(array.array('B', msg.pkt))
        # protocol_list = dict((p.protocol_name, p) for p in pkt.protocols if isinstance(p, packet_base.PacketBase))

        _eth = pkt.get_protocol(ethernet.ethernet)        
        _ipv4 = pkt.get_protocol(ipv4.ipv4)
        _icmp = pkt.get_protocol(icmp.icmp)
        _tcp = pkt.get_protocol(tcp.tcp)
        _udp = pkt.get_protocol(udp.udp)

        match = re.search("^.{0,200}", alert)
        match1 = re.split(" ", match.group(0))
        _idle_timeout = 1800
        _hard_timeout = 1800
        
        if "SYN_Flood" in match1:
            self.logger.warning("Alert\tSYN Flood Detected")
            self.snortlogger.warning("SYN Flood Detected")
            alert_key = "eth_type={},eth_dst={},eth_src={},ipv4_dst={},ipv4_src={},ip_proto={},tcp_dst={}".format(_eth.ethertype,_eth.dst,_eth.src,_ipv4.dst,_ipv4.src,_ipv4.proto,_tcp.dst_port)
            if str(alert_key.strip()) in self.alert_counter:
                if self.alert_counter[str(alert_key.strip())] > 100:
                    # TODO : os.run(curl block this packet)
                    self.logger.critical("Alert\tSYN_Flood more than 100 >>> DROP IP !")
            for i in range(1,len(self.datapaths)+1):
                if i != 2 :
                    # self.loggerlocal.warning("ignore form datapath {}".format(i))
                    break
                # self.loggerlocal.warning("accept form datapath {}".format(i))
                _datapath = self.datapaths[i]
                _parser = _datapath.ofproto_parser
                
                _match = _parser.OFPMatch(eth_type=_eth.ethertype,
                    eth_dst=_eth.dst, eth_src=_eth.src,
                    ipv4_dst=_ipv4.dst,ipv4_src=_ipv4.src,
                    ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port)
                _actions = []
                _priority = 5000
                _table_id = 0
                self.add_flow(datapath=_datapath, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)
                self.add_flow(datapath=_datapath-1, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

                if alert_key not in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] = 1
                elif alert_key in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] += 1
                self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, indent=2, sort_keys=True)))
                self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))

        elif "UDP_Flood" in match1:
            self.logger.warning("Alert\tUDP Flood Detected")
            self.snortlogger.warning("UDP Flood Detected")
            alert_key = "eth_type={},eth_dst={},eth_src={},ipv4_dst={},ipv4_src={},ip_proto={},udp_dst={}".format(_eth.ethertype,_eth.dst,_eth.src,_ipv4.dst,_ipv4.src,_ipv4.proto,_udp.dst_port)
            if str(alert_key.strip()) in self.alert_counter:
                if self.alert_counter[str(alert_key.strip())] > 100:
                    # TODO : os.run(curl block this packet)
                    # self.logger.critical("Alert\tUDP_Flood more than 100 >>>> DROP IP !")
            for i in range(1,len(self.datapaths)+1):
                if i != 2 :
                    # self.loggerlocal.warning("ignore form datapath {}".format(i))
                    break
                # self.loggerlocal.warning("accept form datapath {}".format(i))
                _datapath = self.datapaths[i]
                _parser = _datapath.ofproto_parser

                _match = _parser.OFPMatch(eth_type=_eth.ethertype,
                    eth_dst=_eth.dst, eth_src=_eth.src,
                    ipv4_dst=_ipv4.dst, ipv4_src=_ipv4.src,
                    ip_proto=_ipv4.proto, udp_dst=_udp.dst_port)
                _actions = []
                _priority = 5000
                _table_id = 0
                self.add_flow(datapath=_datapath, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)
                self.add_flow(datapath=_datapath-1, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

                if alert_key not in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] = 1
                elif alert_key in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] += 1
                self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, indent=2, sort_keys=True)))
                self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))

        elif "HTTP_Flood" in match1:
            self.logger.warning("Alert\tHTTP Flood Detected")
            self.snortlogger.warning("HTTP Flood Detected")
            alert_key = "eth_type={},eth_dst={},eth_src={},ipv4_dst={},ipv4_src={},ip_proto={},tcp_dst={}".format(_eth.ethertype,_eth.dst,_eth.src,_ipv4.dst,_ipv4.src,_ipv4.proto,_tcp.dst_port)
            if str(alert_key.strip()) in self.alert_counter:
                if self.alert_counter[str(alert_key.strip())] > 100:
                    # TODO : os.run(curl block this packet)
                    # self.logger.critical("Alert\tHTTP_Flood more than 100 >>> DROP IP !")
            for i in range(1,len(self.datapaths)+1):
                if i != 2 :
                    # self.loggerlocal.warning("ignore form datapath {}".format(i))
                    break
                # self.loggerlocal.warning("accept form datapath {}".format(i))
                _datapath = self.datapaths[i]
                _parser = _datapath.ofproto_parser

                _match = _parser.OFPMatch(eth_type=_eth.ethertype,
                    eth_dst=_eth.dst, eth_src=_eth.src,
                    ipv4_dst=_ipv4.dst, ipv4_src=_ipv4.src,
                    ip_proto=_ipv4.proto, tcp_dst=_tcp.dst_port)
                _actions = []
                _priority = 5000
                _table_id = 0
                self.add_flow(datapath=_datapath, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)
                self.add_flow(datapath=_datapath-1, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

                if alert_key not in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] = 1
                elif alert_key in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] += 1
                self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, indent=2, sort_keys=True)))
                self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))

        elif "ICMP_Flood" in match1:
            self.logger.warning("Alert\tICMP Flood Detected")
            self.snortlogger.warning("ICMP Flood Detected")
            alert_key = "eth_type={},eth_dst={},eth_src={},ipv4_dst={},ipv4_src={},ip_proto={},icmpv4_type={},icmpv4_code={}".format(_eth.ethertype,_eth.dst,_eth.src,_ipv4.dst,_ipv4.src,_ipv4.proto,_icmp.type,_icmp.code)
            if str(alert_key.strip()) in self.alert_counter:
                if self.alert_counter[str(alert_key.strip())] > 100:
                    # TODO : os.run(curl block this packet)
                    # self.logger.critical("Alert\tICMP_Flood more than 100 >>> DROP IP !")
            for i in range(1,len(self.datapaths)+1):
                if i != 2  :
                    # self.loggerlocal.warning("ignore form datapath {}".format(i))
                    break
                # self.loggerlocal.warning("accept form datapath {}".format(i))
                _datapath = self.datapaths[i]
                _parser = _datapath.ofproto_parser

                _match = _parser.OFPMatch(eth_type=_eth.ethertype,
                    eth_dst=_eth.dst, eth_src=_eth.src,
                    ipv4_dst=_ipv4.dst, ipv4_src=_ipv4.src,
                    ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
                _actions = []
                _priority = 5000
                _table_id = 0
                self.add_flow(datapath=_datapath, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)
                self.add_flow(datapath=_datapath-1, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

                if alert_key not in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] = 1
                elif alert_key in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] += 1
                self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, indent=2, sort_keys=True)))
                self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))

        elif "PingOfDeath" in match1:
            self.logger.warning("Alert\tPOD Flood Detected")
            self.snortlogger.warning("POD Flood Detected")
            alert_key = "eth_type={},eth_dst={},eth_src={},ipv4_dst={},ipv4_src={},ip_proto={},icmpv4_type={},icmpv4_code={}".format(_eth.ethertype,_eth.dst,_eth.src,_ipv4.dst,_ipv4.src,_ipv4.proto,_icmp.type,_icmp.code)
            if str(alert_key.strip()) in self.alert_counter:
                if self.alert_counter[str(alert_key.strip())] > 100:
                    # TODO : os.run(curl block this packet)
                    # self.logger.critical("Alert\t POD more than 100 >>> DROP IP !")
            for i in range(1,len(self.datapaths)+1):
                if i != 2:
                    # self.loggerlocal.warning("ignore form datapath {}".format(i))
                    break
                # self.loggerlocal.warning("accept form datapath {}".format(i))
                _datapath = self.datapaths[i]
                _parser = _datapath.ofproto_parser

                _match = _parser.OFPMatch(eth_type=_eth.ethertype,
                    eth_dst=_eth.dst, eth_src=_eth.src,
                    ipv4_dst=_ipv4.dst, ipv4_src=_ipv4.src,
                    ip_proto=_ipv4.proto, icmpv4_type=_icmp.type, icmpv4_code=_icmp.code)
                _actions = []
                _priority = 5000
                _table_id = 0
                self.add_flow(datapath=_datapath, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)
                self.add_flow(datapath=_datapath-1, priority=_priority, match=_match,
                    table_id=0, idle=_idle_timeout, hard=_hard_timeout, actions=_actions)

                if alert_key not in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] = 1
                elif alert_key in self.alert_counter:
                    self.alert_counter[str(alert_key.strip())] += 1
                self.logger.info("Alert\t{}".format(json.dumps(self.alert_counter, indent=2, sort_keys=True)))
                self.loggerlocal.info(json.dumps(self.alert_counter, indent=2, sort_keys=True))

        self.logger.warning('Alert\talertmsg: %s' % ''.join(str(alertmsg)))
        self.snortlogger.info('alertmsg: %s' % ''.join(str(alertmsg)))
        self.loggerlocal.info('alertmsg: %s' % ''.join(str(alertmsg)))
        self.packet_print(msg.pkt)

        now = time.strftime('%b %d %H:%M:%S')
        snortlog = list(map(str, [now, 'Info', str(alertmsg)]))
        self.logger.info("Alert\t{}".format(snortlog))
        self.loggerlocal.info(snortlog)
