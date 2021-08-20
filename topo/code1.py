from mininet.topo import Topo
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.log import setLogLevel, info
from mininet.node import OVSKernelSwitch, RemoteController, Host
from mininet.util import dumpNodeConnections, dumpNetConnections, dumpPorts
from time import sleep
from datetime import datetime
from random import randrange, choice, randint
import json

class MyTopo( Topo ):

    def build( self ):

        s1 = self.addSwitch( 's1', cls=OVSKernelSwitch, protocols='OpenFlow13' ) # Switch Server

        h1 = self.addHost( 'h1', cls=Host, mac="00:00:00:00:00:01", ip="10.0.0.1/24", defaultRoute='via 10.0.0.10')
        h2 = self.addHost( 'h2', cls=Host, mac="00:00:00:00:00:02", ip="10.0.0.2/24", defaultRoute='via 10.0.0.10')

        s2 = self.addSwitch( 's2', cls=OVSKernelSwitch, protocols='OpenFlow13', 
        defaultRoute='via 192.168.0.1' ) # Router Server

        s3 = self.addSwitch( 's3', cls=OVSKernelSwitch, protocols='OpenFlow13', 
        defaultRoute='via 192.168.0.2' ) # Router Client

        s4 = self.addSwitch( 's4', cls=OVSKernelSwitch, protocols='OpenFlow13', failMode='standalone') # Switch Client-1

        h3 = self.addHost( 'h3', cls=Host, mac="00:00:00:00:00:03", ip="172.16.0.1/24", defaultRoute='via 172.16.0.10')
        h4 = self.addHost( 'h4', cls=Host, mac="00:00:00:00:00:04", ip="172.16.0.2/24", defaultRoute='via 172.16.0.10')
        h5 = self.addHost( 'h5', cls=Host, mac="00:00:00:00:00:05", ip="172.16.0.3/24", defaultRoute='via 172.16.0.10')
        h6 = self.addHost( 'h6', cls=Host, mac="00:00:00:00:00:06", ip="172.16.0.4/24", defaultRoute='via 172.16.0.10')

        s5 = self.addSwitch( 's5', cls=OVSKernelSwitch, protocols='OpenFlow13', failMode='standalone') # Switch Client-2

        h7 = self.addHost( 'h7', cls=Host, mac="00:00:00:00:00:07", ip="172.16.10.1/24", defaultRoute='via 172.16.10.10')
        h8 = self.addHost( 'h8', cls=Host, mac="00:00:00:00:00:08", ip="172.16.10.2/24", defaultRoute='via 172.16.10.10')
        h9 = self.addHost( 'h9', cls=Host, mac="00:00:00:00:00:09", ip="172.16.10.3/24", defaultRoute='via 172.16.10.10')
        h10 = self.addHost( 'h10', cls=Host, mac="00:00:00:00:00:0A", ip="172.16.10.4/24", defaultRoute='via 172.16.10.10')
        h11 = self.addHost( 'h11', cls=Host, mac="00:00:00:00:00:0B", ip="172.16.10.5/24", defaultRoute='via 172.16.10.10')
        h12 = self.addHost( 'h12', cls=Host, mac="00:00:00:00:00:0C", ip="172.16.10.6/24", defaultRoute='via 172.16.10.10')

        # Add links

        # Switch to Switch
        self.addLink( s1, s2, port1=1, port2=1, cls=TCLink, bw=10, 
            params2={'ip': '10.0.0.10/24' } )
        self.addLink( s2, s3, port1=2, port2=1, cls=TCLink, bw=10, 
            params1={'ip': '192.168.0.1/30'}, params2={ 'ip': '192.168.0.2/30' } )
        self.addLink( s3, s4, port1=2, port2=1, cls=TCLink, bw=10, 
            params1={'ip': '172.16.0.10/24'} )
        self.addLink( s3, s5, port1=3, port2=1, cls=TCLink, bw=10, 
            params1={'ip': '172.16.10.10/24'} )

        # Host to Switch
        self.addLink( h1, s1, port1=1, port2=2, cls=TCLink, bw=10 )
        self.addLink( h2, s1, port1=1, port2=3, cls=TCLink, bw=10 )

        self.addLink( h3, s4, port1=1, port2=2, cls=TCLink, bw=10 )
        self.addLink( h4, s4, port1=1, port2=3, cls=TCLink, bw=10 )
        self.addLink( h5, s4, port1=1, port2=4, cls=TCLink, bw=10 )
        self.addLink( h6, s4, port1=1, port2=5, cls=TCLink, bw=10 )

        self.addLink( h7, s5, port1=1, port2=2, cls=TCLink, bw=10 )
        self.addLink( h8, s5, port1=1, port2=3, cls=TCLink, bw=10 )
        self.addLink( h9, s5, port1=1, port2=4, cls=TCLink, bw=10 )
        self.addLink( h10, s5, port1=1, port2=5, cls=TCLink, bw=10 )
        self.addLink( h11, s5, port1=1, port2=6, cls=TCLink, bw=10 )
        self.addLink( h12, s5, port1=1, port2=7, cls=TCLink, bw=10 )

def ip_generator_L():
    ipL = ".".join(["172","16","0",str(randrange(1,5))])
    return ipL

def ip_generator_R():
    ipR = ".".join(["172","16","10",str(randrange(1,7))])
    return ipR

def start_as_server(host,ip,w1,w2,w3,iperfTCP,iperfUDP,sockTCP,sockUDP):
    if ip == '10.0.0.1':
        host.cmdPrint('cd /home/guest/flowmanager/topo/server1;pwd;')#ifconfig -a;route -n;')
    else:
        # cp ./pysum_x/index.html .;cp ./pysum_x/text1.txt .;cp ./pysum_x/text2.txt .;cp ./pysum_x/text3.txt .;cp ./pysum_x/text4.txt .;cp ./pysum_x/txt.zip .;
        host.cmdPrint('cd /home/guest/flowmanager/topo/server2;pwd;')#ifconfig -a;route -n;')
    host.cmdPrint('python2 -m SimpleHTTPServer {} &'.format(w1))
    host.cmdPrint('python2 -m SimpleHTTPServer {} &'.format(w2))
    host.cmdPrint('python2 -m SimpleHTTPServer {} &'.format(w3))
    host.cmdPrint('iperf -s -p {} &'.format(iperfTCP))
    host.cmdPrint('iperf -s -u -p {} &'.format(iperfUDP))
    host.cmdPrint('python3 tcpsocket-server.py {} {} &'.format(ip,sockTCP))
    if ip == '10.0.0.1':
        host.cmdPrint('python3 server.py -H {} -p {} -u ./pysum_1 &'.format(ip,sockUDP))
    else:
        host.cmdPrint('python3 server.py -H {} -p {} -u ./pysum_2 &'.format(ip,sockUDP))
    host.cmdPrint("ls -alh;")

    # sleep(10)
    return
    # host.cmdPrint('python3 client.py {} {} -g 01.txt &'.format(ip,sockUDP)) # Untuk Testing
    # host.cmdPrint('python3 client.py {} {} -p ~/.bashrc &'.format(ip,sockUDP)) # Untuk Testing

COUNTER_w1 = 1
def do_wget_1(host,target):
    host.cmdPrint('wget http://{}:80/index.html;'.format(target))
    host.cmdPrint('wget http://{}:443/text1.txt;'.format(target))
    host.cmdPrint('wget http://{}:443/text2.txt;'.format(target))
    host.cmdPrint('wget http://{}:443/text3.txt;'.format(target))
    host.cmdPrint('wget http://{}:443/text4.txt;'.format(target))
    host.cmdPrint('wget http://{}:8000/txt.zip;'.format(target))
    host.cmdPrint("ls -alh;")
    sleep(5)
    return

COUNTER_w2 = 1
def do_wget_2(host,target):
    host.cmdPrint('wget http://{}:81/index.html;'.format(target))
    host.cmdPrint('wget http://{}:444/text1.txt;'.format(target))
    host.cmdPrint('wget http://{}:444/text2.txt;'.format(target))
    host.cmdPrint('wget http://{}:444/text3.txt;'.format(target))
    host.cmdPrint('wget http://{}:444/text4.txt;'.format(target))
    host.cmdPrint('wget http://{}:8001/txt.zip;'.format(target))
    host.cmdPrint("ls -alh;")
    sleep(5)
    return

def scapy(host,target,port):
    # print("None")
    # return
    # host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "1-5" true;date;'.format(target,port))
    host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "1-5" false;date;'.format(target,port))
    # host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "2-5" true;date;'.format(target,port))
    host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "2-5" false;date;'.format(target,port))
    # host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "3-5" true;date;'.format(target,port))
    host.cmdPrint('date;python3 ../attackscapy.py 2 "{}:{}" "3-5" false;date;'.format(target,port))
    return

def startNetwork():

    topo = MyTopo()
    con = RemoteController('c0', ip='192.168.56.111', port=6653)
    # net = Mininet(topo=topo, link=TCLink, controller=con, cleanup=True, waitConnected=True)
    net = Mininet(topo=topo, controller=con, cleanup=True, waitConnected=True, xterms=False, build=True,
        autoSetMacs = False,autoStaticArp = False)

    net.start()

    c0 = net.get('c0')
    # s2 = net.get('s2')
    # s3 = net.get('s3')

    #===========================================================
    c0.cmdPrint('echo 0 > /proc/sys/net/ipv4/ip_forward;arp -a')
    sleep(10)
    c0.cmdPrint('echo 1 > /proc/sys/net/ipv4/ip_forward;')
    c0.cmdPrint('curl -X GET http://localhost:8080/router/all;')

    c0.cmdPrint('curl -X POST -d \'{"address":"10.0.0.10/24"}\' http://localhost:8080/router/0000000000000002;') # s2-eth1
    c0.cmdPrint('curl -X POST -d \'{"address":"192.168.0.1/30"}\' http://localhost:8080/router/0000000000000002;') # s2-eth2

    c0.cmdPrint('curl -X POST -d \'{"address":"192.168.0.2/30"}\' http://localhost:8080/router/0000000000000003;') # s3-eth1
    c0.cmdPrint('curl -X POST -d \'{"address":"172.16.0.10/24"}\' http://localhost:8080/router/0000000000000003;')  # s3-eth2
    c0.cmdPrint('curl -X POST -d \'{"address":"172.16.10.10/24"}\' http://localhost:8080/router/0000000000000003;') # s3-eth3

    c0.cmdPrint('curl -X POST -d \'{"gateway": "192.168.0.2"}\' http://localhost:8080/router/0000000000000002;') # Default Route
    c0.cmdPrint('curl -X POST -d \'{"gateway": "192.168.0.1"}\' http://localhost:8080/router/0000000000000003;') # Default Route
    
    c0.cmdPrint('curl -X POST -d \'{"destination": "172.16.0.0/24", "gateway": "192.168.0.2"}\' http://localhost:8080/router/0000000000000002;') # Static Route 1
    c0.cmdPrint('curl -X POST -d \'{"destination": "172.16.10.0/24", "gateway": "192.168.0.2"}\' http://localhost:8080/router/0000000000000002;') # Static Route 2

    c0.cmdPrint('curl -X POST -d \'{"destination": "10.0.0.0/24", "gateway": "192.168.0.1"}\' http://localhost:8080/router/0000000000000003;') # Static Route 1

    c0.cmdPrint('curl -X GET http://localhost:8080/router/all;')

    # s2.cmdPrint('pwd;route -n;arp -a')
    # s3.cmdPrint('pwd;route -n;arp -a')
    #===========================================================

    info( "\nDumping host connections\n" )
    dumpNodeConnections(net.hosts)

    info( "\nDumping Net connections\n" )
    dumpNetConnections(net)

    info( "\nDumping switch Ports\n" )
    dumpPorts(net.switches)
    # sleep(2)

    info("\n\n--------------------------------------------------\n")
    info("Capture Network Traffic ...\n")
    c0.cmdPrint('cd /home/guest/flowmanager/topo/;pwd;')#ifconfig -a;route -n;')
    c0.cmdPrint('tcpdump -vv -XX -tttt -nne -i s2-eth2 -w zMininet_Traffic_s2e2.pcap &')
    c0.cmdPrint('tcpdump -vv -XX -tttt -nne -i s4-eth1 -w zMininet_Traffic_s4e1.pcap &')
    c0.cmdPrint('tcpdump -vv -XX -tttt -nne -i s5-eth1 -w zMininet_Traffic_s5e1.pcap &')
    sleep(5)

    # info("\n\n--------------------------------------------------\n")
    # info("Starting Snort-IDS ...\n")
    # s3.cmdPrint('cd /home/guest/flowmanager/topo/;pwd;ifconfig -a;route -n;')
    # s3.cmdPrint('snort -i s3-eth1 -A unsock -c /etc/snort/snort.conf -l /tmp  &')
    # sleep(10)

    #===========================================================

    info( "\nPingAll switch\n" )
    # net.pingAll()

    info( "\n\nPingAllFull switch\n" )
    # net.pingAllFull()

    info("\n\ngetAllHost\n")
    # info(net.hosts)

    info("\n\ngetAllSwitch\n")
    # info(net.switches)

    info("\n\ngetAllController\n")
    # info(net.controller)
    info("\n")

    # sleep(5)
    #===========================================================
    
    h1 = net.get('h1') # Server-1
    h2 = net.get('h2') # Server-2
    
    h3 = net.get('h3') # LClient-1
    h4 = net.get('h4') # LClient-2
    h5 = net.get('h5') # LClient-3
    h6 = net.get('h6') # LClient-4
    
    h7 = net.get('h7') # RClient-1
    h8 = net.get('h8') # RClient-2
    h9 = net.get('h9') # RClient-3
    h10 = net.get('h10') # RClient-4
    h11 = net.get('h11') # RClient-5
    h12 = net.get('h12') # RClient-6
    
    server = [h1, h2]
    hostsL = [h3, h4, h5, h6]
    hostsR = [h7, h8, h9, h10, h11, h12]

    info("\n--------------------------------------------------\n")
    info("Starting Server Services ...\n")
    start_as_server(server[0],'10.0.0.1',80,443,8000,5050,5051,8888,69)
    start_as_server(server[1],'10.0.0.2',81,444,8001,6060,6061,9999,70)
    sleep(5)

    #info("\n--------------------------------------------------\n")
    #info("Starting Firefox Browser ...\n")
    #c0.cmdPrint('firefox http://localhost:8080/home/index.html')
    #c0.cmdPrint('firefox http://localhost:8080/home/messages.html')
    #c0.cmdPrint('firefox http://localhost:8080/home/messages_snort.html')

    # sleep(5)
    ii = jj = 1
    _ii = 3
    _jj = 7
    dictFolder = {}
    for h in hostsL:
        h.cmdPrint('cd /home/guest/flowmanager/topo/;pwd;ifconfig -a;route -n;mkdir hL{}/;cd hL{};pwd;ls -a;'.format( str(ii),str(ii) ) )
        dictFolder['h'+str(_ii)] = 'hL'+str(ii)
        ii += 1
        _ii += 1
    for h in hostsR:
        h.cmdPrint('cd /home/guest/flowmanager/topo/;pwd;ifconfig -a;route -n;mkdir hR{}/;cd hR{};pwd;ls -a;'.format( str(jj),str(jj) ) )
        dictFolder['h'+str(_jj)] = 'hR'+str(jj)
        jj += 1
        _jj += 1


    # print(json.dumps(dictFolder,indent=2,sort_keys=True))
    info("\n\n--------------------------------------------------\n")
    info("Generating traffic ...\n")

    for i in range(5):
        # break
        info("--------------------------------------------------\n")
        info("Iteration n {} ...\n".format(i+1))
        info("--------------------------------------------------\n") 
        
        for j in range(5):
            tmp = randint(0,1)
            if tmp == 0:
                selected_subnet = hostsL
                dst = ip_generator_L()
            else :
                selected_subnet = hostsR
                dst = ip_generator_R()
            src = choice(selected_subnet)
            folder = dictFolder[src.name]
            
            if j < 4:
                # info("generating ICMP traffic between %s and h%s and \nTCP/UDP traffic between %s and h1\n" % (src,((dst.split('.'))[3]),src))
                src.cmdPrint("ping {} -f -c 30".format(dst))
                # src.cmdPrint("iperf -p 5050 -c 10.0.0.1 -t 5")
                # src.cmdPrint("iperf -p 5051 -u -c 10.0.0.1 -t 5")
                src.cmdPrint("echo 'POD';timeout 5s hping3 -1 -d 512 10.0.0.1 --faster &> /dev/null")
                # src.cmdPrint("echo 'POD';timeout 30s hping3 -1 -d 999 {} --faster &".format(dst))

                src.cmdPrint("echo 'ICMP_faster';timeout 5s hping3 -1 10.0.0.1 --faster &> /dev/null")
                # src.cmdPrint("echo 'ICMP_faster';timeout 30s hping3 -1 {} --faster".format(dst))

                src.cmdPrint("echo 'UDP_faster';timeout 5s hping3 -2 -p 1 -d 512 10.0.0.1 --faster &> /dev/null")
                # src.cmdPrint("echo 'ICMP_faster';timeout 30s hping3 -2 -p 1 -d 512 {} --faster &".format(dst))

                src.cmdPrint("echo 'SYN_faster';timeout 5s hping3 -S -p 443 -d 512 -w 64 10.0.0.1 --faster &> /dev/null")
                # src.cmdPrint("timeout 30s hping3 -S -p 443 -d 999 -w 64 {} --faster &".format(dst))
                
                # do_tcp(src,'10.0.0.1',8888)
                # sleep(2)
                # do_tftp_get(src,'10.0.0.1',69)

                sleep(5)
                # break


                src.cmdPrint("ping {} -f -c 30".format(dst))
                # src.cmdPrint("iperf -p 6060 -c 10.0.0.2 -t 5")
                # src.cmdPrint("iperf -p 6061 -u -c 10.0.0.2 -t 5")
                
                src.cmdPrint("timeout 5s hping3 -1 -d 999 10.0.0.2 --faster &> /dev/null")
                src.cmdPrint("timeout 5s hping3 -1 -d 999 {} --faster &> /dev/null &".format(dst))
                
                src.cmdPrint("timeout 5s hping3 -2 -p 1 -d 512 10.0.0.2 --faster &> /dev/null")
                src.cmdPrint("timeout 5s hping3 -2 -p 1 -d 512 {} --faster &> /dev/null &".format(dst))
                
                src.cmdPrint("timeout 5s hping3 -S -p 443 -d 999 -w 64 10.0.0.2 --faster &> /dev/null")
                src.cmdPrint("timeout 5s hping3 -S -p 443 -d 999 -w 64 {} --faster &> /dev/null &".format(dst))
                # do_tcp(src,'10.0.0.2',9999)
                # sleep(2)
                # do_tftp_get(src,'10.0.0.2',70)

            else:
                info("generating ICMP traffic between %s and h%s and \nTCP/UDP traffic between %s and h2\n" % (src,((dst.split('.'))[3]),src))
                # src.cmdPrint("ping {} -f -c 10".format(dst))
                # src.cmdPrint("iperf -p 5050 -c 10.0.0.1 -t 10")
                # src.cmdPrint("iperf -p 5051 -u -c 10.0.0.1 -t 10")
                src.cmdPrint("timeout 10s hping3 -1 -d 999 10.0.0.1 --faster")
                src.cmdPrint("timeout 10s hping3 -1 -d 999 {} --faster &".format(dst))
                src.cmdPrint("timeout 10s hping3 -2 -p 1 -d 512 10.0.0.1 --faster")
                src.cmdPrint("timeout 10s hping3 -2 -p 1 -d 512 {} --faster &".format(dst))
                src.cmdPrint("timeout 10s hping3 -S -p 443 -d 999 -w 64 10.0.0.1 --faster")
                src.cmdPrint("timeout 10s hping3 -S -p 443 -d 999 -w 64 {} --faster &".format(dst))
                # do_tcp(src,'10.0.0.1',8888)
                # sleep(2)
                # do_tftp_get(src,'10.0.0.1',69)

                # sleep(3)

                # src.cmdPrint("ping {} -f -c 10".format(dst))
                # src.cmdPrint("iperf -p 6060 -c 10.0.0.2 -t 10")
                # src.cmdPrint("iperf -p 6061 -u -c 10.0.0.2 -t 10")
                
                src.cmdPrint("timeout 10s hping3 -1 -d 999 10.0.0.2 --faster")
                src.cmdPrint("timeout 10s hping3 -1 -d 999 {} --faster &".format(dst))
                
                src.cmdPrint("timeout 10s hping3 -2 -p 1 -d 512 10.0.0.2 --faster")
                src.cmdPrint("timeout 10s hping3 -2 -p 1 -d 512 {} --faster &".format(dst))
                
                src.cmdPrint("timeout 10s hping3 -S -p 443 -d 999 -w 64 10.0.0.2 --faster")
                src.cmdPrint("timeout 10s hping3 -S -p 443 -d 999 -w 64 {} --faster & ".format(dst))
                # do_tcp(src,'10.0.0.2',9999)
                # sleep(2)
                # do_tftp_get(src,'10.0.0.2',70)

            do_wget_1(src,'10.0.0.1')
            # deleteFile(h1)
            # sleep(2)
            # do_tftp_put(src,'10.0.0.1',69,folder)
            # h1.cmdPrint('cp ./pysum_1/index.html .;cp ./pysum_1/text1.txt .;cp ./pysum_1/text2.txt .;cp ./pysum_1/text3.txt .;cp ./pysum_1/text4.txt .;cp ./pysum_1/txt.zip .;ls -alh')
            # sleep(2)
            # scapy(src,'10.0.0.1',1)

            sleep(5)

            do_wget_2(src,'10.0.0.2')
            # deleteFile(h2)
            # sleep(2)
            # do_tftp_put(src,'10.0.0.2',70,folder)
            # h2.cmdPrint('cp ./pysum_2/index.html .;cp ./pysum_2/text1.txt .;cp ./pysum_2/text2.txt .;cp ./pysum_2/text3.txt .;cp ./pysum_2/text4.txt .;cp ./pysum_2/txt.zip .;ls -alh')
            # sleep(2)
            # scapy(src,'10.0.0.2',1)

            info("--------------------------------------------------\n")
            info("Progress n {} ...\n".format(j+1))
            info("--------------------------------------------------\n")
            break
        break

    h3.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hL1")
    h4.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hL2")
    h5.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hL3")
    h6.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hL4")
    
    h7.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR1")
    h8.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR2")
    h9.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR3")
    h10.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR4")
    h11.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR5")
    h12.cmdPrint("cd;rmdir --ignore-fail-on-non-empty -v /home/guest/flowmanager/topo/hR6")
        
    info("---------------------------------------------------------\n\n")
    # sleep(30)
    
    CLI(net)
    net.stop()

if __name__ == '__main__':
    
    start = datetime.now()
    
    setLogLevel( 'info' )
    startNetwork()
    
    end = datetime.now()
    
    info(end-start)
    print()