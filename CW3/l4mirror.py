from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_4
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import in_proto
from ryu.lib.packet import ipv4
from ryu.lib.packet import tcp
from ryu.lib.packet.ether_types import ETH_TYPE_IP

class L4Mirror14(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_4.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(L4Mirror14, self).__init__(*args, **kwargs)
        self.ht = {}

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def features_handler(self, ev):
        dp = ev.msg.datapath
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        acts = [psr.OFPActionOutput(ofp.OFPP_CONTROLLER, ofp.OFPCML_NO_BUFFER)]
        self.add_flow(dp, 0, psr.OFPMatch(), acts)

    def add_flow(self, dp, prio, match, acts, buffer_id=None):
        ofp, psr = (dp.ofproto, dp.ofproto_parser)
        bid = buffer_id if buffer_id is not None else ofp.OFP_NO_BUFFER
        ins = [psr.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, acts)]
        mod = psr.OFPFlowMod(datapath=dp, buffer_id=bid, priority=prio,
                                match=match, instructions=ins)
        dp.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        in_port, pkt = (msg.match['in_port'], packet.Packet(msg.data))
        dp = msg.datapath
        ofp, psr, did = (dp.ofproto, dp.ofproto_parser, format(dp.id, '016d'))
        eth = pkt.get_protocols(ethernet.ethernet)[0]
        iph = pkt.get_protocols(ipv4.ipv4)
        tcph = pkt.get_protocols(tcp.tcp)

        out_port = 2 if in_port == 1 else 1
        acts = [psr.OFPActionOutput(out_port)]
        if tcph is None or iph is None:
            acts=[psr.OFPActionOutput(out_port)]
        elif (len(iph) > 0 and len(tcph) > 0):
            ip_src = iph[0].src
            ip_dst = iph[0].dst
            tcp_src = tcph[0].src_port
            tcp_dst = tcph[0].dst_port
            four_tuple = (ip_src,ip_dst,tcp_src,tcp_dst)
            four_tuple_reverse = (ip_dst,ip_src,tcp_dst,tcp_src)
            if (in_port == 1):
                out_port = 2
                acts=[psr.OFPActionOutput(out_port)]
                match = psr.OFPMatch(in_port=in_port, eth_src = eth.src, eth_dst = eth.dst, eth_type = eth.ethertype, ip_proto = iph[0].proto ,ipv4_dst=iph[0].dst, ipv4_src=iph[0].src, tcp_src = tcph[0].src_port, tcp_dst = tcph[0].dst_port)
                self.add_flow(dp,1,match,acts,msg.buffer_id)
                if msg.buffer_id != ofp.OFPCML_NO_BUFFER:
                    return
            elif(in_port == 2):
                out_port = 1
                if tcph[0].has_flags(tcp.TCP_SYN) and not tcph[0].has_flags(tcp.TCP_ACK):
                    self.ht[four_tuple] = 0
                if four_tuple in self.ht:
                    self.ht[four_tuple] += 1
                    if self.ht[four_tuple] == 10:
                        del self.ht[four_tuple]
                        match = psr.OFPMatch(in_port=in_port, eth_src = eth.src, eth_dst = eth.dst, eth_type = eth.ethertype, ip_proto = iph[0].proto ,ipv4_dst=iph[0].dst, ipv4_src=iph[0].src, tcp_src = tcph[0].src_port, tcp_dst = tcph[0].dst_port)
                        self.add_flow(dp,1,match,acts,msg.buffer_id)
                        if msg.buffer_id != ofp.OFPCML_NO_BUFFER:
                            return
                    acts=[psr.OFPActionOutput(1),psr.OFPActionOutput(3)]
                else:
                    match = psr.OFPMatch(in_port=in_port, eth_src = eth.src, eth_dst = eth.dst, eth_type = eth.ethertype, ip_proto = iph[0].proto ,ipv4_dst=iph[0].dst, ipv4_src=iph[0].src, tcp_src = tcph[0].src_port, tcp_dst = tcph[0].dst_port)
                    self.add_flow(dp,1,match,acts,msg.buffer_id)
                    if msg.buffer_id != ofp.OFPCML_NO_BUFFER:
                        return 

        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        out = psr.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                               in_port=in_port, actions=acts, data=data)
        dp.send_msg(out)
