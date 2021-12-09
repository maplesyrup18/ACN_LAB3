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

    def __eq__(self, other):
        return self.id == other.id and self.type == other.type

class Jellyfish:

    def __init__(self, num_servers, num_switches, num_ports):
        self.servers = []
        self.switches = []
        self.generate(num_servers, num_switches, num_ports)

    def generate(self, num_servers, num_switches, num_ports):

        # TODO: code for generating the jellyfish topology
        server_dict = switch_dict = {}
        available_ports = []
        # generating all switches
        for iterator in range(num_switches):
            self.switches.append(Node("s" + str(iterator), "switch"))
            switch_dict.update({"s" + str(iterator): Node("s" + str(iterator), "switch")})
            available_ports.append(num_ports)

        # generating all servers
        for iterator in range(num_servers):
            self.servers.append(Node("h" + str(iterator), "server"))
            server_dict.update({"h" + str(iterator): Node("h" + str(iterator), "server")})

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
            switch_dict["s" + str(iterator)].edges.append(
                switch_dict["s" + str(iterator)].add_edge(server_dict["h" + str(iterator)]))
            print("Connected switch ", switch_dict["s" + str(iterator)].id, "to the host ",
                  server_dict["h" + str(iterator)].id)
            available_ports[iterator] -= 1
            servers_iterated = iterator

        # for balancing the server to switch count
        if server_switch_ratio >= 1:
            for iterator in range(server_switch_ratio):
                switch_used_list = []
                random_switch_chooser = 0
                while random_switch_chooser in switch_used_list:
                    random_switch_chooser = random.randint(0, num_switches)
                switch_dict["s" + str(random_switch_chooser)].edges.append(
                switch_dict["s" + str(random_switch_chooser)].add_edge(server_dict["h" + str(servers_iterated)]))
                print("Connected switch ", switch_dict["s" + str(iterator)].id, "to the host ",
                  server_dict["h" + str(servers_iterated)].id)
                available_ports[random_switch_chooser] -= 1
                # random_switch_chooser += 1
                servers_iterated += 1
                switch_used_list.append(random_switch_chooser)

        # creating a set data-structure for links to avoid duplicates
        joint_links = set()

        # start randomly linking switches in case free-ports are available
        num_of_switches_left = num_switches
        repeated_random_check_failure = 0

        while (num_of_switches_left > 1) and (repeated_random_check_failure < 5):
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
                        switch_dict["s" + str(each_link[0])].edges.append(
                            switch_dict["s" + str(each_link[0])].add_edge(switch_dict["s" + str(each_link[1])]))
                        print("Connected switch ", switch_dict["s" + str(each_link[0])].id, "to the switch ",
                              server_dict["s" + str(each_link[1])].id)
                        # num_switches[each_link[0]], num_switches[each_link[1]])


class Fattree:

    def __init__(self, num_ports):
        self.servers = []
        self.switches = []
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
        edge_switch_list = aggregation_switch_list = core_switch_list = server_list = {}
        # creating dictionary above for storing mapping
        current_switch_count = 0
        current_server_count = 0

        edge_start_index = 0
        edge_end_index = 0
        aggregator_start_index = 0
        aggregator_end_index = 0
        core_start_index = 0
        core_end_index = 0

        # few interesting properties to consider
        # Each edge switch connects to (k/2) nodes and k/2 aggregation switches within same pod
        # Each aggregation switch connects to (k/2) edge switches from same pod, and k/2 core switches
        # Each core switch connects to only one aggregation switch (randomly, first for simplicity) in a given pod

        # creating edge switches
        edge_start_index = 0
        for iterator in range(edge_layer_switch_count):
            # edge_switch_list.append("s" + str(iterator))
            current_switch_count += 1
            self.switches.append(Node("s" + str(current_switch_count), "edge"))
            edge_switch_list.update({"edge" + str(iterator): Node("s" + str(current_switch_count), "edge")})
            print("Edge switch", current_switch_count)
        edge_end_index = len(self.switches) - 1

        aggregator_start_index = len(self.switches)
        # creating aggregation switches
        for iterator in range(1, aggregation_layer_switch_count + 1):
            # edge_switch_list.append("s" + str(iterator))
            current_switch_count += 1
            self.switches.append(Node("s" + str(current_switch_count), "aggregator"))
            aggregation_switch_list.update(
                {"aggregator" + str(iterator): Node("s" + str(current_switch_count), "aggregator")})

            print("Aggregator switch ", current_switch_count)
        aggregator_end_index = len(self.switches) - 1


        # creating core switches
        core_start_index = len(self.switches)
        for iterator in range(1, core_layer_switch_count + 1):
            # core_switch_list.append("s" + str(iterator))
            current_switch_count += 1
            self.switches.append(Node("s" + str(current_switch_count), "core"))
            core_switch_list.update({"core" + str(iterator): Node("s" + str(current_switch_count), "core")})

            print("Core switch ", current_switch_count)
        core_end_index = len(self.switches) - 1

        # creating hosts
        for host_iterator in range(total_servers_count):
            current_server_count += 1
            server_list.update({"host" + str(host_iterator): Node("h" + str(current_server_count), "host")})
            self.servers.append(Node("h" + str(current_server_count), "host"))

            print("Host ", current_server_count)

        current_server_count = 1
        temp_server = Node(current_switch_count,"host")
        temp_switch = Node(current_switch_count,"switches")
        # iterating the edge switches and adding link with hosts first
        for iterator in range(1, edge_layer_switch_count + 1):

            for host_iterator in range(current_server_count, current_server_count + (num_ports // 2)):
                edge_switch_list["edge" + str(iterator - 1)].edges.append(
                    edge_switch_list["edge" + str(iterator - 1)].add_edge(server_list["host" + str(host_iterator - 1)]))
                edge_switch_list["edge" + str(iterator - 1)].add_edge(server_list["host" + str(host_iterator - 1)])
                # for i in range(len(self.servers)):
                #     if self.servers[i] == server_list["host" + str(host_iterator - 1)]:
                #         temp_server = self.servers[i]
                #         print("Matching host found!")
                #         break
                # for i in range(len(self.switches)):
                #     if self.switches[i] == edge_switch_list["edge" + str(iterator - 1)]:
                #         temp_switch = self.switches[i]
                #         print("Matching switch found!")
                #         break
                # temp_switch.add_edge(temp_server)
                #temp_switch.
                print("Connected edge switch ", edge_switch_list["edge" + str(iterator - 1)].id, "to the host ",
                      server_list["host" + str(host_iterator - 1)].id)
                current_server_count += 1

        current_pod = 0
        # print("Switch Count ", current_switch_count)

        # iterating the aggregator switches and adding links with edge switches and core switches
        for iterator in range(1, aggregation_layer_switch_count + 1):

            # link edge switches
            for edge_iterator in range(current_pod * (num_ports // 2),
                                       (current_pod * (num_ports // 2)) + (num_ports // 2)):
                aggregation_switch_list["aggregator" + str(iterator)].edges.append(
                    aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                        edge_switch_list["edge" + str(edge_iterator)]))
                # for i in range(len(self.switches)):
                #     if self.switches[i] == aggregation_switch_list["aggregator" + str(iterator)]:
                #         temp_server = self.switches[i]
                #         print("Matching aggregation switch found!")
                #     if self.switches[i] == edge_switch_list["edge" + str(edge_iterator)]:
                #         temp_switch = self.switches[i]
                #         print("Matching edge switch found!")
                # temp_switch.add_edge(temp_server)
                print("Connected aggregator switch ", aggregation_switch_list["aggregator" + str(iterator)].id,
                      "to the edge switch ",
                      edge_switch_list["edge" + str(edge_iterator)].id)
            if iterator % (num_ports // 2) == 0:
                current_pod += 1
                # print("POD ", current_pod)

            # link core switches
            core_aggregate_connection = 0  # checks for the k/2 connections between core and aggregator
            for core_iterator in range(((iterator - 1) * num_ports // 2) % (core_layer_switch_count),
                                       core_layer_switch_count):
                # ((iterator) * (num_ports // 2)) % (core_layer_switch_count)):

                aggregation_switch_list["aggregator" + str(iterator)].edges.append(
                    aggregation_switch_list["aggregator" + str(iterator)].add_edge(
                        core_switch_list["core" + str(core_iterator + 1)]))
                # for i in range(len(self.switches)):
                #     if self.switches[i] == aggregation_switch_list["aggregator" + str(iterator)]:
                #         temp_server = self.switches[i]
                #         print("Matching aggregation switch found!")
                #     if self.switches[i] == core_switch_list["core" + str(core_iterator + 1)]:
                #         temp_switch = self.switches[i]
                #         print("Matching core switch found!")
                # temp_switch.add_edge(temp_server)
                print("Connected aggregator switch ", aggregation_switch_list["aggregator" + str(iterator)].id,
                      "to the core switch ",
                      core_switch_list["core" + str(core_iterator + 1)].id)
                core_aggregate_connection += 1
                if (core_aggregate_connection == num_ports // 2):
                    break;
            # print("POD ", current_pod)


# https://reproducingnetworkresearch.wordpress.com/2014/06/03/cs244-14-jellyfish-networking-data-centers-randomly/
#while (True):
#    try:
 #       switch_port = int(input(
  #          "Please enter the number of ports of switch for generating the Fattree and Jellyfish topologies (should be even):\n"))
   #     if (switch_port % 2 != 0 or switch_port <2):
    #        print("Sorry, the number of switch port supported should be a positive even number! Please try again...")
     #       continue
    #except ValueError:
     #   print("Sorry, the number of switch port supported should be an even number! Please try again...")
      #  continue
    #else:
     #   break
#print(Fattree(4))
# calculate the number of servers and switches used for generating the fattree topology, using same number of switch port (k)
#num_servers = (switch_port ** 3) // 4  # (K^3)/4, where k = switch port count in a switch
#num_switches = 5 * (switch_port ** 2) // 4  # 5*(k^2)/4, where k = switch port count in a switch
# we will pass the same number of switches and servers to Jellyfish topology for proper comparison between these two topologies
#print(Jellyfish(num_servers, num_switches, switch_port))
