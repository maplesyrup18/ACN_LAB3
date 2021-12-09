# Copyright 2021 Lin Wang

# This code is part of the Advanced Computer Networks course at VU 
# Amsterdam.

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

# A dirty workaround to import topo.py from lab2

import os
import subprocess
import time

import mininet
import mininet.clean
from mininet.net import Mininet
from mininet.cli import CLI
from mininet.log import lg, info
from mininet.link import TCLink
from mininet.node import Node, OVSKernelSwitch, RemoteController
from mininet.topo import Topo
from mininet.util import waitListening, custom


# import topo

class Edge:
    def __init__(self):
        self.lnode = None
        self.rnode = None

    def remove(self):
        self.lnode.edges.remove(self)
        self.rnode.edges.remove(self)
        self.lnode = None
        self.rnode = None


# Class for a node in the graph
class NodeLab:
    def __init__(self, id, type):
        self.edges = []
        self.id = id
        self.type = type

    # Add an edge connected to another node
    def add_edge(self, node):
        edge = Edge()
        edge.lnode = self
        edge.rnode = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge


    # Remove an edge from the node
    def remove_edge(self, edge):
        self.edges.remove(edge)


    # Decide if another node is a neighbor
    def is_neighbor(self, node):
        for edge in self.edges:
            if edge.lnode == node or edge.rnode == node:
                return True
        return False


class FattreeNet(Topo):
    """
    Create a fat-tree network in Mininet
    """

    def __init__(self, given_ports):
        Topo.__init__(self)
        self.servers = []
        self.switches_lab = []
        self.num_ports = given_ports
        self.edge_switch_list = {}
        self.aggregation_switch_list = {}
        self.core_switch_list = {}
        self.edge_topo = {}
        self.aggregation_topo = {}
        self.core_topo = {}
        self.host_topo = {}
        self.switch_topo = {}
        self.server_list = {}
        self.fat_edge_set = set()


        # TODO: please complete the network generation logic here
        # k = self.num_ports
        info("--------------------------------------------------")
        #self.num_ports = 2
        pod_count = self.num_ports
        each_type_switches_in_pod = self.num_ports // 2
        core_layer_switch_count = (self.num_ports // 2) ** 2
        info("\nTotal core switches used in this topology: ", core_layer_switch_count)
        aggregation_layer_switch_count = self.num_ports * (self.num_ports // 2)
        info("\nTotal aggregation switches used in this topology: ", aggregation_layer_switch_count)
        edge_layer_switch_count = self.num_ports * (self.num_ports // 2)
        info("\nTotal edge switches used in this topology: ", edge_layer_switch_count)
        total_servers_count = self.num_ports * ((self.num_ports // 2) ** 2)
        info("\nTotal number of hosts used in this topology: ", total_servers_count)
        total_switch_count = core_layer_switch_count + aggregation_layer_switch_count + edge_layer_switch_count
        info("\nTotal switches used in this topology: ", total_switch_count)
        info("\n--------------------------------------------------")
        # self.edge_switch_list = self.aggregation_switch_list = self.core_switch_list = self.server_list = {}
        # creating dictionary above for storing mapping
        current_switch_count = 0
        current_server_count = 0

        # few interesting properties to consider
        # Each edge switch connects to (k/2) nodes and k/2 aggregation switches within same pod
        # Each aggregation switch connects to (k/2) edge switches from same pod, and k/2 core switches
        # Each core switch connects to only one aggregation switch (randomly, first for simplicity) in a given pod

        i = 0  # pod-count
        j = 0  # switch-count
        # creating edge switches
        for iterator in range(edge_layer_switch_count):
            # self.edge_switch_list.append("s" + str(iterator))
            self.switches_lab.append("s" + str(current_switch_count))
            if ((iterator % (self.num_ports // 2)) == 0 and iterator != 0):
                i += 1
                j = 0
            elif iterator != 0:
                j += 1
            self.edge_switch_list.update({"edge" + str(iterator): NodeLab("s" + str(current_switch_count),
                                                                       "10." + str(i) + "." + str(j) + ".1")})
            self.switch_topo.update({"edge" + str(iterator): self.addSwitch("s" + str(current_switch_count),dpid=str(current_switch_count+1))})
            #self.edge_topo.update({"edge" + str(iterator): self.switch_topo["edge" + str(iterator)]})
            info("\nEdge switch", current_switch_count,
                 "; IP-Address = ", self.edge_switch_list["edge" + str(iterator)].type)

            current_switch_count += 1

        i = 0  # pod-count
        j = 0  # switch-count
        # creating aggregation switches
        for iterator in range(aggregation_layer_switch_count):
            # self.edge_switch_list.append("s" + str(iterator))
            self.switches_lab.append("s" + str(current_switch_count))
            if ((iterator % (self.num_ports // 2)) == 0 and iterator != 0):
                i += 1
                j = (self.num_ports // 2)
            elif iterator != 0:
                j += 1
            else:
                j = (self.num_ports // 2)
            self.aggregation_switch_list.update(
                {"aggregator" + str(iterator): NodeLab("s" + str(current_switch_count),
                                                    "10." + str(i) + "." + str(j) + ".1")})
            self.switch_topo.update({"aggregator" + str(iterator): self.addSwitch("s" + str(current_switch_count),dpid=str(current_switch_count+1))})
            #self.aggregation_topo.update({"aggregator" + str(iterator):self.switch_topo["aggregator" + str(iterator)]})
            info("\nAggregator switch ", current_switch_count,
                 "; IP-Address = ", self.aggregation_switch_list["aggregator" + str(iterator)].type)
            current_switch_count += 1

        i = 0  # core's ith position for ip-address
        j = 1  # core's jth position for ip-address
        # creating core switches
        for iterator in range(0, core_layer_switch_count):
            # self.core_switch_list.append("s" + str(iterator))
            self.switches_lab.append("s" + str(current_switch_count))
            if ((iterator) % (self.num_ports // 2) == 0):
                i += 1
                j = 1
            self.core_switch_list.update({"core" + str(iterator): NodeLab("s" + str(current_switch_count),
                                                                       "10." + str(self.num_ports) + "." + str(
                                                                           i) + "." + str(j))})
            self.switch_topo.update({"core" + str(iterator): self.addSwitch("s" + str(current_switch_count),dpid=str(current_switch_count+1))})
            #self.core_topo.update({"core" + str(iterator): self.switch_topo["core" + str(iterator)]})
            info("\nCore switch ", current_switch_count, "; IP-Address = ",
                 self.core_switch_list["core" + str(iterator)].type)

            j += 1
            current_switch_count += 1

        i = 0  # pod-count
        j = 0  # switch-count
        k = 2  # host-count, always start with 2 (as ip-octet value 1 is occupied by switch)
        # creating hosts
        for host_iterator in range(total_servers_count):
            if (host_iterator % self.num_ports == 0 and host_iterator != 0):
                i += 1
                j = 0
                k = 2
            elif ((host_iterator % (self.num_ports // 2)) == 0 and host_iterator != 0):
                j += 1
                k = 2

            self.server_list.update({"host" + str(host_iterator): NodeLab("h" + str(current_switch_count),
                                                                       "10." + str(i) + "." + str(j) + "." + str(k))})
            self.servers.append("h" + str(current_server_count))
            self.host_topo.update({"host" + str(host_iterator): self.addHost("h" + str(current_server_count),
                                                                             ip="10." + str(i) + "." + str(
                                                                                 j) + "." + str(k))})
            info("\nHost ", current_server_count, "; IP-Address = ", self.server_list["host" + str(host_iterator)].type)
            k += 1
            current_server_count += 1

        current_server_count = 0
        host_switch_linkopts = dict(bw=15, delay='5ms')

        # iterating the edge switches and adding link with hosts first
        for iterator in range(0, edge_layer_switch_count):

            for host_iterator in range(current_server_count, current_server_count + (self.num_ports // 2)):
                temp_edge = self.edge_switch_list["edge" + str(iterator)].add_edge(
                    self.server_list["host" + str(host_iterator)])
                self.edge_switch_list["edge" + str(iterator)].edges.append(temp_edge)
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                info("\nConnected edge switch ", self.switch_topo["edge" + str(iterator)], "to the host ",
                       self.host_topo["host" + str(host_iterator)])
                self.addLink(self.host_topo["host" + str(host_iterator)], self.switch_topo["edge" + str(iterator)],
                             **host_switch_linkopts)
                current_server_count += 1

        current_pod = 0
        # print("Switch Count ", current_switch_count)

        # iterating the aggregator switches and adding links with edge switches and core switches
        for iterator in range(0, aggregation_layer_switch_count):

            self.aggregation_switch_list.update(
                {"aggregator" + str(iterator): NodeLab("s" + str(current_switch_count), "aggregator")})

            # print("POD ", current_pod)
            if iterator % (self.num_ports // 2) == 0 and iterator != 0:
                current_pod += 1
                #print("\nPOD ", current_pod)

            # link edge switches
            for edge_iterator in range(current_pod * (self.num_ports // 2),
                                       (current_pod * (self.num_ports // 2)) + (self.num_ports // 2)):
                temp_edge = self.aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                    self.edge_switch_list["edge" + str(edge_iterator)])
                self.aggregation_switch_list["aggregator" + str(iterator)].edges.append(temp_edge)
                # print("\nConnected aggregator switch ", self.aggregation_topo["aggregator" + str(iterator)],
                #        "to the edge switch ",
                #        self.edge_topo["edge" + str(edge_iterator)])
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                self.addLink(self.switch_topo["aggregator" + str(iterator)],
                             self.switch_topo["edge" + str(edge_iterator)],
                             **host_switch_linkopts)

            # link core switches
            core_aggregate_connection = 0  # checks for the k/2 connections between core and aggregator
            for core_iterator in range((iterator * self.num_ports // 2) % core_layer_switch_count,
                                       core_layer_switch_count):
                # ((iterator) * (self.num_ports // 2)) % (core_layer_switch_count)):
                temp_edge = self.aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                    self.core_switch_list["core" + str(core_iterator)])
                self.aggregation_switch_list["aggregator" + str(iterator)].edges.append(temp_edge)
                # print("\nConnected aggregator switch ", self.aggregation_topo["aggregator" + str(iterator)],
                #       "to the core switch ",
                #       self.core_topo["core" + str(core_iterator)])
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                core_aggregate_connection += 1
                self.addLink(self.switch_topo["core" + str(core_iterator)],
                             self.switch_topo["aggregator" + str(iterator)],
                             **host_switch_linkopts)
                if core_aggregate_connection == self.num_ports // 2:
                    break


def make_mininet_instance(graph_topo):
    #net_topo = FattreeNet(graph_topo)
    net = Mininet(topo=graph_topo, controller=None, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip="127.0.0.1", port=6653)
    return net


def run(graph_topo):
    # Run the Mininet CLI with a given topology
    lg.setLogLevel('info')
    mininet.clean.cleanup()
    net = make_mininet_instance(graph_topo)

    info('*** Starting network ***\n')
    net.start()
    info('*** Running CLI ***\n')
    CLI(net)
    info('*** Stopping network ***\n')
    net.stop()


ft_topo = FattreeNet(4)
run(ft_topo)
