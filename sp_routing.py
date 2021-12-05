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

#!/usr/bin/env python3
import importlib

from gi._gi import source_new
from ryu.base import app_manager
from ryu.controller import mac_to_port
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.mac import haddr_to_bin
from ryu.lib.packet import packet, ethernet
from ryu.lib.packet import ipv4
from ryu.lib.packet import arp

from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from ryu.app.wsgi import ControllerBase

from queue import PriorityQueue
import copy

#topo = importlib.import_module("fat-tree")
import fattreetopology

# class GraphLab:
#     # This will construct the topology of the graph by creating linked nodes
#     def __init__(self, num_vertices):
#         self.vertices = num_vertices  # number of vertices in the graph
#         self.edges = [[-1 for iterator in range(num_vertices)]
#                       for nested_iterator in range(num_vertices)]
#         self.visited = []  # visited vertices set
#
#     def construct_edge(self, from_vertex, to_vertex):
#         self.edges[from_vertex][to_vertex] = 1
#         self.edges[to_vertex][from_vertex] = 1
#
#     def Dijkstra(self, start_vertex):
#         distance_list = {vertex: float('inf') for vertex in range(self.vertices)}
#         distance_list[start_vertex] = 0
#
#         priority_queue = PriorityQueue()
#         priority_queue.put((0, start_vertex))
#
#         while not priority_queue.empty():
#             distance, current_vertex = priority_queue.get()
#             self.visited.append(current_vertex)
#
#             for neighbouring_vertex in range(self.vertices):
#                 if self.edges[current_vertex][neighbouring_vertex] != -1:
#                     distance = self.edges[current_vertex][neighbouring_vertex]
#                     if neighbouring_vertex not in self.visited:
#                         current_cost = distance_list[neighbouring_vertex]
#                         revised_cost = distance_list[current_vertex] + distance
#                         if revised_cost < current_cost:
#                             priority_queue.put((revised_cost, neighbouring_vertex))
#                             distance_list[neighbouring_vertex] = revised_cost
#         # print("Resetting visited to [] for next iteration of Dijkstra!")
#         self.visited = []
#         return distance_list
#
#         # def test(self):
#         #     fat_graph = Graph(fattree.)
#         #     for edge_value in ft_topo.fat_edge_set:
#         #         # print("Constructing Graph: ", map_hosts_switches_ft[edge_value[0]], edge_value[0],
#         #         # map_hosts_switches_ft[edge_value[1]], edge_value[1])
#         #         fat_graph.construct_edge(map_hosts_switches_ft[edge_value[0]], map_hosts_switches_ft[edge_value[1]])
#         #     for dijkstra_iterator in range(host_iterator_counter):
#         #         # print("Inside executing")
#         #
#         #         distance = fat_graph.Dijkstra(dijkstra_iterator)
#         #         # distance_result.append(distance) -- for calculating all node costs including switches
#         #         for vertex in range(dijkstra_iterator + 1, host_iterator_counter):
#         #             # print("Distance from vertex", dijkstra_iterator, "to vertex", vertex, "is", distance[vertex])
#         #             # print("Distance from vertex", dijkstra_iterator, "to vertex", vertex, "is", distance[vertex])
#         #             ft_distance_result.append(distance[vertex])

class SPRouter(app_manager.RyuApp):

    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(SPRouter, self).__init__(*args, **kwargs)
        self.topo_net = fattreetopology.FattreeNet(4)
        # source - https://github.com/Ehsan70/RyuApps/blob/master/TopoDiscoveryInRyu.md
        # defining mac address table as dictionary for lookup
        self.mac_to_port_table = {}
        # for holding topology data structure
        self.topo_raw_switches = []
        self.topo_raw_links = []

    # Topology discovery
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):

        # Switches and links in the network
        switches = get_switch(self, None)
        links = get_link(self, None)


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

        # analyse the incoming packets
        read_packet = packet.Packet(msg.data)
        ethernet_packet = read_packet.get_protocol(ethernet.ethernet)
        destination_add = ethernet_packet.dst
        source_add = ethernet_packet.src

        # read the in_port number from packet_in message and learn/store
        in_port = msg.match['in_port']

        # TODO: handle new packets at the controller
        self.mac_to_port_table.setdefault(dpid, {})

        self.logger.info("\tPacket in %s %s %s %s", dpid, source_add, destination_add, in_port)

        # learn a mac address to avoid FLOOD next time.
        self.mac_to_port_table[dpid][source_add] = in_port

        if destination_add in self.mac_to_port_table[dpid]:
            out_port = self.mac_to_port[dpid][destination_add]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        # install a flow to avoid packet_in next time
        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=destination_add)
            # verify if we have a valid buffer_id, if yes avoid to send both
            # flow_mod & packet_out
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

    """
    The event EventSwitchEnter will trigger the activation of get_topology_data().
    """

    @set_ev_cls(event.EventSwitchEnter)
    def handler_switch_enter(self, ev):
        # The Function get_switch(self, None) outputs the list of switches.
        self.topo_raw_switches = copy.copy(get_switch(self, None))
        # The Function get_link(self, None) outputs the list of links.
        self.topo_raw_links = copy.copy(get_link(self, None))

        """
        We are now having the links and switches of the topo saved 
        """

        print(" \t" + "Current Links:")
        for link in self.topo_raw_links:
            print(" \t\t" + str(link))

        print(" \t" + "Current Switches:")
        for switch in self.topo_raw_switches:
            print(" \t\t" + str(switch))

    """
    This event is fired when a switch leaves the topo. i.e. fails.
    """
    @set_ev_cls(event.EventSwitchLeave, [MAIN_DISPATCHER, CONFIG_DISPATCHER, DEAD_DISPATCHER])
    def handler_switch_leave(self, ev):
        self.logger.info("Not tracking Switches, switch leaved.")
