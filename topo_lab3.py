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

import sys
import random
import queue
# import topo
from queue import PriorityQueue
import networkx as nx
import matplotlib.pyplot as plot
import numpy as npy

nodes_jf = []
nodes_ft = []
edges_jf = []
edges_ft = []
ft_topo = None
jf_topo = None
map_hosts_switches_ft = {}
map_hosts_switches_jf = {}
store_hosts_only_for_result_ft = []  # to store the mapped host values
store_hosts_only_for_result_jf = []  # to store the mapped host values
indent_string_to_int = 0  # get count of both hosts and switches

def get_nodes_fattree(ft_topo):
    "Returns the nodes of the graph for fattree topology"
    indent_string_to_int = 0  # get count of both hosts and switches
    total_hosts_fattree = 0
    # map_hosts_switches_ft = {}
    store_hosts_only_for_result_ft.clear()
    for key, value in ft_topo.server_list.items():
        nodes_ft.append(str(value.id))
        # print("Printing Nodes Fattree", value.id)
        map_hosts_switches_ft[str(value.id)] = indent_string_to_int
        store_hosts_only_for_result_ft.append(indent_string_to_int)
        indent_string_to_int += 1
        total_hosts_fattree += 1
    for key, value in ft_topo.edge_switch_list.items():
        nodes_ft.append(str(value.id))
        # print("Printing Nodes Fattree", value.id)
        map_hosts_switches_ft[str(value.id)] = indent_string_to_int
        indent_string_to_int += 1
    for key, value in ft_topo.aggregation_switch_list.items():
        nodes_ft.append(str(value.id))
        # print("Printing Nodes Fattree", value.id)
        map_hosts_switches_ft[str(value.id)] = indent_string_to_int
        indent_string_to_int += 1
    for key, value in ft_topo.core_switch_list.items():
        nodes_ft.append(str(value.id))
        # print("Printing Nodes Fattree", value.id)
        map_hosts_switches_ft[str(value.id)] = indent_string_to_int
        indent_string_to_int += 1

    return len(nodes_ft)


def get_edges_fattree(ft_topo):
    "Returns the edges of the graph for fattree topology"
    for edge_value in ft_topo.fat_edge_set:
        edges_ft.append(edge_value)
        # print("Printing Edges Fattree", edge_value)


def draw_fattree(switch_port):
    "Draws the fattree topology"
    gft = nx.Graph()
    ft_topo = Fattree(switch_port)
    get_nodes_fattree(ft_topo)
    get_edges_fattree(ft_topo)
    for edge_value in ft_topo.fat_edge_set:
        # print("Constructing Graph: ", map_hosts_switches_ft[edge_value[0]], edge_value[0],
        # map_hosts_switches_ft[edge_value[1]], edge_value[1])
        gft.add_edge(map_hosts_switches_ft[edge_value[0]], map_hosts_switches_ft[edge_value[1]])
    nx.draw_spring(gft, with_labels=True)
    plot.savefig("Fattree.png")


def get_nodes_jellyfish(jf_topo):
    "Returns the nodes of the graph for jellyfish topology"
    indent_string_to_int = 0  # get count of both hosts and switches
    # print('Printing count of both hosts and switch in Jellyfish - ',indent_string_to_int)
    total_hosts_jellyfish = 0
    # map_hosts_switches_jf = {}
    store_hosts_only_for_result_jf.clear()
    nodes_jf.clear()
    for key, value in jf_topo.server_dict.items():
        nodes_jf.append(str(value.id))
        # print("Printing Nodes Jellyfish", value.id)
        map_hosts_switches_jf[str(value.id)] = indent_string_to_int
        indent_string_to_int += 1
        store_hosts_only_for_result_jf.append(indent_string_to_int)
        total_hosts_jellyfish += 1
    for key, value in jf_topo.switch_dict.items():
        nodes_jf.append(str(value.id))
        # print("Printing Nodes Jellyfish", value.id)
        map_hosts_switches_jf[str(value.id)] = indent_string_to_int
        indent_string_to_int += 1
    return len(nodes_jf)


def get_edges_jellyfish(jf_topo):
    "Returns the edges of the graph for fattree topology"
    for edge_value in jf_topo.jf_edge_set:
        edges_jf.append(edge_value)
        # print("Printing Edges Jellyfish", edge_value)


def draw_jellyfish(num_servers, num_switches, num_ports):
    "Draws the jellyfish topology"
    gjf = nx.Graph()
    jf_topo = Jellyfish(num_servers, num_switches, num_ports)
    # print map_hosts_switches_jf
    get_nodes_jellyfish(jf_topo)
    get_edges_jellyfish(jf_topo)
    # for edge_value in jf_topo.jf_edge_set:
        # print("Constructing Jellyfish Graph: ", map_hosts_switches_jf[edge_value[0]], edge_value[0],map_hosts_switches_jf[edge_value[1]], edge_value[1])
    for edge_value in jf_topo.jf_edge_set:
        gjf.add_edge(map_hosts_switches_jf[edge_value[0]], map_hosts_switches_jf[edge_value[1]])
    nx.draw_spring(gjf, with_labels=True)
    plot.savefig("Jellyfish.png")


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
class Node:
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


class Jellyfish:

    def __init__(self, num_servers, num_switches, num_ports):
        self.servers = []
        self.switches = []
        self.server_dict = {}
        self.switch_dict = {}
        self.jf_edge_set = set()
        self.generate(num_servers, num_switches, num_ports)

    def generate(self, num_servers, num_switches, num_ports):

        # TODO: code for generating the jellyfish topology

        available_ports = []
        # generating all switches
        for iterator in range(num_switches):
            self.switches.append(Node("s" + str(iterator), "switch"))
            self.switch_dict.update({"s" + str(iterator): Node("s" + str(iterator), "switch")})
            available_ports.append(num_ports)

        # generating all servers
        for iterator in range(num_servers):
            self.servers.append(Node("h" + str(iterator), "server"))
            self.server_dict.update({"h" + str(iterator): Node("h" + str(iterator), "server")})

        server_switch_ratio = num_servers // num_switches
        print("-----------------------------------------")
        print("Total servers count = ", num_servers)
        print("Total switches count = ", num_switches)
        print("Servers to switches ratio: ", server_switch_ratio)
        print("-----------------------------------------")

        # connecting each server with a switch or vice-versa
        if num_switches < num_servers:
            select_join_first = num_switches
        else:
            select_join_first = num_servers
        # servers_iterated = 0
        # link the servers with switches
        for iterator in range(select_join_first):
            temp_edge = self.switch_dict["s" + str(iterator)].add_edge(self.server_dict["h" + str(iterator)])
            self.switch_dict["s" + str(iterator)].edges.append(temp_edge)
            self.jf_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
            print("Connected switch ", self.switch_dict["s" + str(iterator)].id, "to the host ",
                  self.server_dict["h" + str(iterator)].id)
            available_ports[iterator] -= 1
            servers_iterated = iterator
            servers_remaining = num_servers - servers_iterated
            servers_iterated += 1

        # for balancing the server to switch count
        if server_switch_ratio >= 1:
            for iterator in range(server_switch_ratio):
                if servers_remaining > num_switches:
                    check_switch_iteration = num_switches
                else:
                    check_switch_iteration = servers_remaining
                for switch_iterator in range(check_switch_iteration):
                    switch_used_list = []
                    # random_switch_chooser = 0
                    # servers_iterated += 1
                    servers_remaining -= 1
                    # while random_switch_chooser in switch_used_list:
                    #     random_switch_chooser = random.randint(0, num_switches - 1)
                    if servers_remaining != 0 and available_ports[switch_iterator] != 0:
                        temp_edge = self.switch_dict["s" + str(switch_iterator)].add_edge(
                            self.server_dict["h" + str(servers_iterated)])
                        self.switch_dict["s" + str(switch_iterator)].edges.append(temp_edge)
                        self.jf_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                        print("In ramdom: Connected switch ", self.switch_dict["s" + str(switch_iterator)].id, "to the host ",
                            self.server_dict["h" + str(servers_iterated)].id)
                        available_ports[switch_iterator] -= 1
                    # random_switch_chooser += 1
                    servers_iterated += 1
                    # switch_used_list.append(random_switch_chooser)

        # creating a set data-structure for links to avoid duplicates
        joint_links = set()

        # start randomly linking switches in case free-ports are available
        num_of_switches_left = num_switches
        repeated_random_check_failure = 0

        # check if there are 10 hits with similar switches already linked, then exit
        while (num_of_switches_left > 1) and (repeated_random_check_failure < 10):
            switch_left = random.randint(0, num_switches - 1)
            # switch_left = random.randrange(0, num_switches)
            # print("LS - ", switch_left)
            switch_right = random.randint(0, num_switches - 1)
            # print("RS - ", switch_right)
            while switch_left == switch_right:
                switch_right = random.randint(0, num_switches - 1)
            if (switch_left, switch_right) in joint_links:
                repeated_random_check_failure += 1
            else:
                repeated_random_check_failure = 0
                joint_links.add((switch_left, switch_right))
                joint_links.add((switch_right, switch_left))

                # reducing the available ports from both switches by 1
                available_ports[switch_left] -= 1
                available_ports[switch_right] -= 1

                # also reducing the total switches left to be operated if the open ports for any switch is 0
                if (available_ports[switch_left] == 0) or (available_ports[switch_right] == 0):
                    num_of_switches_left -= 1

        if num_of_switches_left > 0:
            for iterator in range(num_switches):
                while available_ports[iterator] > 1:
                    while True:
                        random_link = random.choice(list(joint_links))
                        # if current switch port is already listed in random link, ignore
                        if (iterator, random_link[0]) in joint_links:
                            continue
                        if (iterator, random_link[1]) in joint_links:
                            continue
                        # else, remove the link, and add new link
                        joint_links.remove(random_link)
                        joint_links.remove(random_link[::-1])
                        joint_links.add((iterator, random_link[0]))
                        joint_links.add((random_link[0], iterator))
                        joint_links.add((iterator, random_link[1]))
                        joint_links.add((random_link[1], iterator))
                        available_ports[iterator] -= 2

            for each_link in joint_links:
                if each_link[0] < each_link[1]:
                    temp_edge = self.switch_dict["s" + str(each_link[0])].add_edge(
                        self.switch_dict["s" + str(each_link[1])])
                    self.switch_dict["s" + str(each_link[0])].edges.append(temp_edge)
                    print("Connected switch ", self.switch_dict["s" + str(each_link[0])].id, "to the switch ",
                          self.switch_dict["s" + str(each_link[1])].id)
                    self.jf_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))


class Fattree:

    def __init__(self, num_ports):
        self.servers = []
        self.switches = []
        self.edge_switch_list = {}
        self.aggregation_switch_list = {}
        self.core_switch_list = {}
        self.server_list = {}
        self.fat_edge_set = set()
        self.generate(num_ports)

    def generate(self, num_ports):
        # initialising the various counts in a fattree topology
        # k = num_ports
        print("--------------------------------------------------")
        pod_count = num_ports
        each_type_switches_in_pod = num_ports // 2
        core_layer_switch_count = (num_ports // 2) ** 2
        print("Total core switches used in this topology: ", core_layer_switch_count)
        aggregation_layer_switch_count = num_ports * (num_ports // 2)
        print("Total aggregation switches used in this topology: ", aggregation_layer_switch_count)
        edge_layer_switch_count = num_ports * (num_ports // 2)
        print("Total edge switches used in this topology: ", edge_layer_switch_count)
        total_servers_count = num_ports * ((num_ports // 2) ** 2)
        print("Total number of hosts used in this topology: ", total_servers_count)
        total_switch_count = core_layer_switch_count + aggregation_layer_switch_count + edge_layer_switch_count
        print("Total switches used in this topology: ", total_switch_count)
        print("--------------------------------------------------")
        # self.edge_switch_list = self.aggregation_switch_list = self.core_switch_list = self.server_list = {}
        # creating dictionary above for storing mapping
        current_switch_count = 0
        current_server_count = 0

        # few interesting properties to consider
        # Each edge switch connects to (k/2) nodes and k/2 aggregation switches within same pod
        # Each aggregation switch connects to (k/2) edge switches from same pod, and k/2 core switches
        # Each core switch connects to only one aggregation switch (randomly, first for simplicity) in a given pod

        i = 0 # pod-count
        j = 0 # switch-count
        # creating edge switches
        for iterator in range(edge_layer_switch_count):
            # self.edge_switch_list.append("s" + str(iterator))
            self.switches.append("s" + str(current_switch_count))
            if ((iterator % (num_ports // 2)) == 0 and iterator != 0):
                i += 1
                j = 0
            elif iterator != 0:
                j += 1
            self.edge_switch_list.update({"edge" + str(iterator): Node("s" + str(current_switch_count),
                                                            "10."+str(i)+"."+str(j)+".1")})
            print("Edge switch", current_switch_count,
                  "; IP-Address = ",self.edge_switch_list["edge" + str(iterator)].type)

            current_switch_count += 1

        i = 0  # pod-count
        j = 0  # switch-count
        # creating aggregation switches
        for iterator in range(aggregation_layer_switch_count):
            # self.edge_switch_list.append("s" + str(iterator))
            self.switches.append("s" + str(current_switch_count))
            if ((iterator % (num_ports // 2)) == 0 and iterator != 0):
                i += 1
                j = (num_ports//2)
            elif iterator != 0:
                j += 1
            else:
                j = (num_ports // 2)
            self.aggregation_switch_list.update(
                {"aggregator" + str(iterator): Node("s" + str(current_switch_count),
                                                            "10."+str(i)+"."+str(j)+".1")})
            print("Aggregator switch ", current_switch_count,
                  "; IP-Address = ",self.aggregation_switch_list["aggregator" + str(iterator)].type)
            current_switch_count += 1

        i = 0 # core's ith position for ip-address
        j = 1 # core's jth position for ip-address
        # creating core switches
        for iterator in range(0, core_layer_switch_count):
            # self.core_switch_list.append("s" + str(iterator))
            self.switches.append("s" + str(current_switch_count))
            if ((iterator) % (num_ports // 2) == 0):
                i += 1
                j = 1
            self.core_switch_list.update({"core" + str(iterator): Node("s" + str(current_switch_count),
                                                                       "10."+str(num_ports)+"."+str(i)+"."+str(j))})
            print("Core switch ", current_switch_count, "; IP-Address = ",self.core_switch_list["core" + str(iterator)].type)

            j += 1
            current_switch_count += 1

        i = 0 # pod-count
        j = 0 # switch-count
        k = 2 # host-count, always start with 2 (as ip-octet value 1 is occupied by switch)
        # creating hosts
        for host_iterator in range(total_servers_count):
            if (host_iterator % num_ports == 0 and host_iterator != 0):
                i += 1
                j = 0
                k = 2
            elif ((host_iterator % (num_ports//2)) == 0 and host_iterator != 0):
                j += 1
                k = 2

            self.server_list.update({"host" + str(host_iterator): Node("s" + str(current_switch_count),
                                                 "10."+str(i)+"."+str(j)+"."+str(k))})
            self.servers.append("h" + str(current_server_count))
            print("Host ", current_server_count, "; IP-Address = ",self.server_list["host" + str(host_iterator)].type)
            k += 1
            current_server_count += 1

        current_server_count = 0

        # iterating the edge switches and adding link with hosts first
        for iterator in range(0, edge_layer_switch_count):

            for host_iterator in range(current_server_count, current_server_count + (num_ports // 2)):
                temp_edge = self.edge_switch_list["edge" + str(iterator)].add_edge(
                    self.server_list["host" + str(host_iterator)])
                self.edge_switch_list["edge" + str(iterator)].edges.append(temp_edge)
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                # print("Connected edge switch ", self.edge_switch_list["edge" + str(iterator)].id, "to the host ",
                #       self.server_list["host" + str(host_iterator)].id)
                current_server_count += 1

        current_pod = 0
        # print("Switch Count ", current_switch_count)

        # iterating the aggregator switches and adding links with edge switches and core switches
        for iterator in range(0, aggregation_layer_switch_count):

            self.aggregation_switch_list.update({"aggregator" + str(iterator): Node("s" + str(current_switch_count), "aggregator")})

            # print("POD ", current_pod)
            if iterator % (num_ports // 2) == 0 and iterator != 0:
                current_pod += 1
                print("POD ", current_pod)

            # link edge switches
            for edge_iterator in range(current_pod * (num_ports // 2),
                                       (current_pod * (num_ports // 2)) + (num_ports // 2)):
                temp_edge = self.aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                    self.edge_switch_list["edge" + str(edge_iterator)])
                self.aggregation_switch_list["aggregator" + str(iterator)].edges.append(temp_edge)
                # print("Connected aggregator switch ", self.aggregation_switch_list["aggregator" + str(iterator)].id,
                #       "to the edge switch ",
                #       self.edge_switch_list["edge" + str(edge_iterator)].id)
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))

            # link core switches
            core_aggregate_connection = 0  # checks for the k/2 connections between core and aggregator
            for core_iterator in range((iterator * num_ports // 2) % core_layer_switch_count,
                                       core_layer_switch_count):
                # ((iterator) * (num_ports // 2)) % (core_layer_switch_count)):
                temp_edge = self.aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                    self.core_switch_list["core" + str(core_iterator)])
                self.aggregation_switch_list["aggregator" + str(iterator)].edges.append(temp_edge)
                # print("Connected aggregator switch ", self.aggregation_switch_list["aggregator" + str(iterator)].id,
                #       "to the core switch ",
                #       self.core_switch_list["core" + str(core_iterator)].id)
                self.fat_edge_set.add((temp_edge.lnode.id, temp_edge.rnode.id))
                core_aggregate_connection += 1
                if core_aggregate_connection == num_ports // 2:
                    break;


# https://reproducingnetworkresearch.wordpress.com/2014/06/03/cs244-14-jellyfish-networking-data-centers-randomly/
while (True):
    try:
        switch_port = int(input(
            "Please enter the number of ports of switch for generating the Fattree and Jellyfish topologies (should be even):\n"))
        if (switch_port % 2 != 0 or switch_port < 2):
            print("Sorry, the number of switch port supported should be a positive even number! Please try again...")
            continue
    except ValueError:
        print("Sorry, the number of switch port supported should be an even number! Please try again...")
        continue
    else:
        break
print(Fattree(switch_port))
# # calculate the number of servers and switches used for generating the fattree topology, using same number of switch port (k)
# num_servers = (switch_port ** 3) // 4  # (K^3)/4, where k = switch port count in a switch
# num_switches = 5 * (switch_port ** 2) // 4  # 5*(k^2)/4, where k = switch port count in a switch
# # we will pass the same number of switches and servers to Jellyfish topology for proper comparison between these two topologies
# # print(Jellyfish(num_servers, num_switches, switch_port))

# ft_topo = topo.Fattree(4)
# jf_topo = Jellyfish(16, 8, 4)
# jf_topo = topo.Jellyfish(16,12 , 4)

#get_edges_fattree()
#get_nodes_fattree()

#get_nodes_jellyfish()
#get_nodes_jellyfish()


# draw_fattree(4)

# draw_jellyfish(16, 6, 4)

