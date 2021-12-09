# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at Vrije 
# Universiteit Amsterdam.

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at

#   http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# !/usr/bin/env python3
import copy

import netaddr
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet, icmp
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

import re
import topo


class SPRouter(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = topo.Fattree(4)
        # used for IP to Switch-DPID mapping
        self.ip_to_switch_dpid_table = {}
        # used for switch to host port mapping at switch (for outward action)
        self.switch_host_in_port = {}
        self.switch_dpid_to_dp = {}
        # store a pair of links to servers for each switch
        self.switch_to_other_switch_ports_list = []
        # Holds the topology data and structure
        self.topo_raw_switches = []
        self.topo_raw_links = []

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        switch_list = [switch.dp.id for switch in switches]
        for switch in switches:
            self.switch_dpid_to_dp[switch.dp.id] = switch.dp
        self.topo_raw_switches = switches
        links = get_link(self, None)
        link_list = [(link.src.dpid, link.dst.dpid, {'port': link.src.port_no}) for link in links]
        for link in links:
            if (link.src.dpid, link.src.port_no) not in self.switch_to_other_switch_ports_list:
                self.switch_to_other_switch_ports_list.append((link.src.dpid, link.src.port_no))
        # print("Switch-links to each other = ", *self.switch_to_other_switch_ports_list)
        self.topo_raw_links = links

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Install entry-miss flow entry
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    # Add a flow entry to the flow-table
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # Construct flow_mod message and send it
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                match=match, instructions=inst)
        datapath.send_msg(mod)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        dpid = datapath.id
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        source_add = None
        destination_add = None
        # TODO: handle new packets at the controller
        # analyse the incoming packets
        read_packet = packet.Packet(msg.data)

        # read the in_port number from packet_in message and learn/store
        in_port = msg.match['in_port']

        pkt_ip = read_packet.get_protocol(ipv4.ipv4)
        if pkt_ip:
            destination_add = pkt_ip.dst
            source_add = pkt_ip.src
            print("IP Packet from %s for %s!" % (source_add, destination_add))
            actions = [
                parser.OFPActionOutput(port=self.switch_host_in_port[self.ip_to_switch_dpid_table[destination_add]])]
            match = parser.OFPMatch(in_port=in_port, eth_dst=destination_add)
            self.add_flow(datapath, 1, match, actions)
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=in_port,
                                      actions=actions,
                                      data=read_packet.data)
            datapath.send_msg(out)

        pkt_eth = read_packet.get_protocol(ethernet.ethernet)
        if pkt_eth:
            # print("Ethernet Packet Found!")
            pass
        if not pkt_eth:
            print("Not an Ethernet packet!")
            # return

        pkt_icmp = read_packet.get_protocol(icmp.icmp)
        if pkt_icmp:
            destination_add = pkt_icmp.dst
            source_add = pkt_icmp.src
            print("ICMP Packet from %s for %s!" % (source_add, destination_add))
            actions = [
                parser.OFPActionOutput(port=self.switch_host_in_port[self.ip_to_switch_dpid_table[destination_add]])]
            match = parser.OFPMatch(in_port=in_port, eth_dst=destination_add)
            self.add_flow(datapath, 1, match, actions)
            out = parser.OFPPacketOut(datapath=datapath,
                                      buffer_id=ofproto.OFP_NO_BUFFER,
                                      in_port=in_port,
                                      actions=actions,
                                      data=read_packet.data)
            datapath.send_msg(out)

        pkt_arp = read_packet.get_protocol(arp.arp)
        if pkt_arp:
            destination_add = pkt_arp.dst_ip
            source_add = pkt_arp.src_ip
            print("ARP packet from %s for %s" % (source_add, destination_add))
            self.logger.info(
                "Packet in switch %s at port %s from %s for %s" % (dpid, in_port, source_add, destination_add))
            # learn the IP-address connected to switch
            self.ip_to_switch_dpid_table[source_add] = dpid
            self.switch_host_in_port[dpid] = in_port
            if destination_add in self.ip_to_switch_dpid_table:
                actions = [
                    parser.OFPActionOutput(
                        port=self.switch_host_in_port[self.ip_to_switch_dpid_table[destination_add]])]
                match = parser.OFPMatch(in_port=in_port, eth_dst=pkt_arp.dst_mac)
                self.add_flow(datapath, 1, match, actions)
                out = parser.OFPPacketOut(datapath=datapath,
                                          buffer_id=ofproto.OFP_NO_BUFFER,
                                          in_port=in_port,
                                          actions=actions,
                                          data=read_packet.data)
                datapath.send_msg(out)
            else:
                # print("Something")
                # for link in self.topo_raw_links:
                #     print(" \t" + "Current Links:")
                #     temp_string = str(link)
                #     switch_dpid1 = re.search('(?<=dpid=)(\w+)', temp_string).group(1)
                #     switch_dpid2 = re.search('(?<=dpid=)(\w+)', temp_string).group(2)
                #     switch_dpid1_link = re.search('(?<=port_no=)(\w+)', temp_string).group(1)
                #     switch_dpid2_link = re.search('(?<=port_no=)(\w+)', temp_string).group(2)
                #     # out_port = ofproto.OFPP_FLOOD
                #     if (switch_dpid1, switch_dpid1_link) not in self.switch_to_other_switch_ports_list:
                #         self.switch_to_other_switch_ports_list.append((switch_dpid1, switch_dpid1_link))
                #     if (switch_dpid2, switch_dpid2_link) not in self.switch_to_other_switch_ports_list:
                #         self.switch_to_other_switch_ports_list.append((switch_dpid2, switch_dpid2_link))
                # # for iterator in range(len(self.switch_to_other_switch_ports_list)):
                # #     print(self.switch_to_other_switch_ports_list[iterator])
                # counter = 0
                for switch in self.topo_raw_switches:
                #     # print(" \t" + "Current Switches:")
                #     temp_string = str(switch)
                #     switch_dpid = re.search('(?<=dpid=)(\w+)', temp_string).group(1)
                #     self.switch_dpid_to_dp['s' + str(counter)] = switch_dpid
                #     counter += 1
                    for iterator in range(1, 5):  # since there could only be 4 ports in a switch
                        if (switch.dp.id, iterator) not in self.switch_to_other_switch_ports_list:
                            out_port = iterator
                            print("Sending flood packet on switch %s on port %s" % (switch.dp.id, iterator))
                            actions = [parser.OFPPacketOut(out_port)]
                            out = parser.OFPPacketOut(datapath=switch.dp,
                                                      in_port=in_port,
                                                      actions=actions,
                                                      buffer_id=datapath.ofproto.OFP_NO_BUFFER,
                                                      data=msg.data)
                            datapath.send_msg(out)
                    # print(" \t" + "controlled flooding being done!")

    @set_ev_cls(event.EventSwitchEnter)
    def handler_switch_enter(self, ev):
        # # The Function get_switch(self, None) outputs the list of switches.
        # self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        # self.topo_raw_links = copy.copy(get_link(self, None))

        """
        We are now having the links and switches of the topo saved 
        """
        #
        # print(" \t" + "Current Links:")
        # for link in self.topo_raw_links:
        #     print(" \t\t" + str(link))
        #
        # print(" \t" + "Current Switches:")
        # for switch in self.topo_raw_switches:
        #     print(" \t\t" + str(switch))

    """
    This event is fired when a switch leaves the topo. i.e. fails.
    """

    @set_ev_cls(event.EventSwitchLeave, [MAIN_DISPATCHER, CONFIG_DISPATCHER, DEAD_DISPATCHER])
    def handler_switch_leave(self, ev):
        self.logger.info("Not tracking Switches, switch leaved.")
