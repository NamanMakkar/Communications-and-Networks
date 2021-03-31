from scapy.utils import RawPcapReader
from scapy.layers.l2 import Ether
from scapy.layers.inet import IP, TCP
from scapy.layers.inet6 import IPv6
from ipaddress import ip_address, IPv6Address
from socket import IPPROTO_TCP
import sys
import matplotlib.pyplot as plt

class Flow(object):
    def __init__(self, data):
        self.pkts = 0
        self.flows = 0
        self.ft = {}
        for pkt, metadata in RawPcapReader(data):
            self.pkts += 1
            ether = Ether(pkt)
            if ether.type == 0x86dd:
                ip = ether[IPv6]
                if ip.nh != 6:
                    self.pkts -= 1
                    continue
            elif ether.type == 0x0800:
                ip = ether[IP]
                if ip.proto != 6:
                    self.pkts -= 1
                    continue

            tcp = ip[TCP]
            src = int(ip_address(ip.src))
            dst = int(ip_address(ip.dst))
            sport = tcp.sport
            dport = tcp.dport

            if ether.type == 0x86dd:
                value = ip.plen
            elif ether.type == 0x0800:
                value = ip.len - (4*ip.ihl)
            
            key = (src,dst,sport,dport)
            reverse = (dst,src,dport,sport)
            if key in self.ft:
                self.ft[key] += value 
            elif reverse in self.ft:
                self.ft[reverse] += value 
            else:
                self.ft[key] = value

    def Plot(self):
        topn = 100
        data = [i/1000 for i in list(self.ft.values())]
        data.sort()
        data = data[-topn:]
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        ax.hist(data, bins=20, log=True)
        ax.set_ylabel('# of flows')
        ax.set_xlabel('Data sent [KB]')
        ax.set_title('Top {} TCP flow size distribution.'.format(topn))
        plt.savefig(sys.argv[1] + '.flows.pdf', bbox_inches='tight')
        plt.close()
    def Print(self):
        print(len(self.ft))

if __name__ == '__main__':
    d = Flow(sys.argv[1])
    d.Plot()
