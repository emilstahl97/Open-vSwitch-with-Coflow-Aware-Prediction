#!/bin/bash
#
# This is a simple script for configuring an environment that replicates a
# single-node OpenShift network (OCP) setup. The objective is to enable access
# to an external IP (via the node IP) to simulate an externally exposed
# service, akin to using the 'oc expose service <service>' command. In a real
# cluster, the kernel handles the NAT translation from an external virtual IP
# to the node IP. However, in this scenario, we bypass this translation,
# allowing direct access to the external service IP within the 3.0.0.0/8 range.
# It's layout as follows:
#
#                                  40.0.0.0.1/8             40.0.0.0.2/8
#                                  00:00:00:01:00:00        00:00:00:02:00:00
#                         +---------------------+             +---------------------+
#                         |   Cluster Router    +-------------+  Logical Switch GW  |
#                         +----------+----------+             +----------+----------+
#                                    | 1.255.255.254/8                   |
#  +---------------+                 | 00:00:00:00:00:01                 |                  +---------------+
#  |   LB on L1    |      +----------+----------+             +----------+----------+       |   LB on GWR   |
#  | (OCP service) +----->|   Logical Switch 1  |             |         GWR         |<------+  (OCP route)  |
#  |  2.0.0.0/24   |      +--+-------+-------+--+             +----------+----------+       |  3.0.0.0/24   |
#  +---------------+         |       |       |                           | 4.255.255.254/8  +---------------+
#                         +--+--+ +--+--+ +--+--+                        | 00:00:00:03:00:00
#                         | POD | | POD | | POD |             +----------+----------+
#                         +-----+ +-----+ +-----+             |  External Interface |
#                                                             +---------------------+
#
# By default, this script will create 8 PODs, each with a direct IP address
# ranging from 1.0.0.1 to 1.0.0.8. In other words, the last digit in the IP
# address corresponds to the POD number. Each pod resides in its own namespace,
# named podX. To execute commands within a POD's namespace, you can use the
# following syntax:
#
#   # ip netns exec pod6 ip addr show dev eth0
#   140: eth0@if141: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP group default qlen 1000
#       link/ether 00:00:00:00:10:06 brd ff:ff:ff:ff:ff:ff link-netnsid 0
#       inet 1.0.0.6/8 scope global eth0
#          valid_lft forever preferred_lft forever
#
# Additionally, we set up a service IP to simulate POD-to-POD communication on
# the 2.0.0.0 network. Load balancers will be configured for nine UDP ports
# (see UDP_PORT_LIST below), with each POD assigned its own service IP. In the
# format of 2.0.0.<pod_id>. For instance, for POD5, the service IP will be
# 2.0.0.5.
#
# To simulate access from outside the network, we'll set up similar load
# balancers as above. Although each POD will be assigned two IPs in the format
# of 3.0.0.<pod_id> and 3.0.1.<pod_id>, each IP will load balance the nine UDP
# ports.
#
# This is a ovnnb dump of the load balancers for pod1 (removed UUID column):
#
#   # ovn-nbctl lb-list
#   LB                  PROTO      VIP             IPs
#   lb_route_pod1_0     udp        3.0.0.1:2100    1.0.0.1:2100
#                       udp        3.0.0.1:2110    1.0.0.1:2110
#                       udp        3.0.0.1:2120    1.0.0.1:2120
#                       udp        3.0.0.1:2130    1.0.0.1:2130
#                       udp        3.0.0.1:2140    1.0.0.1:2140
#                       udp        3.0.0.1:2150    1.0.0.1:2150
#                       udp        3.0.0.1:2160    1.0.0.1:2160
#                       udp        3.0.0.1:2170    1.0.0.1:2170
#                       udp        3.0.0.1:2180    1.0.0.1:2180
#   lb_route_pod1_1     udp        3.0.1.1:2100    1.0.0.1:2100
#                       udp        3.0.1.1:2110    1.0.0.1:2110
#                       udp        3.0.1.1:2120    1.0.0.1:2120
#                       udp        3.0.1.1:2130    1.0.0.1:2130
#                       udp        3.0.1.1:2140    1.0.0.1:2140
#                       udp        3.0.1.1:2150    1.0.0.1:2150
#                       udp        3.0.1.1:2160    1.0.0.1:2160
#                       udp        3.0.1.1:2170    1.0.0.1:2170
#                       udp        3.0.1.1:2180    1.0.0.1:2180
#   lb_service_pod1     udp        2.0.0.1:2100    1.0.0.1:2100
#                       udp        2.0.0.1:2110    1.0.0.1:2110
#                       udp        2.0.0.1:2120    1.0.0.1:2120
#                       udp        2.0.0.1:2130    1.0.0.1:2130
#                       udp        2.0.0.1:2140    1.0.0.1:2140
#                       udp        2.0.0.1:2150    1.0.0.1:2150
#                       udp        2.0.0.1:2160    1.0.0.1:2160
#                       udp        2.0.0.1:2170    1.0.0.1:2170
#                       udp        2.0.0.1:2180    1.0.0.1:2180
#
# If you have a physical interface for ingress traffic, configure the
# EXTERNAL_INTERFACE below with its name. If not configured, a network
# namespace called external will be created with a veth pair. Refer to the
# test_setup function below on how it can be used.
#
# Before running it with an external interface, it's suggested to perform
# './ocp_simulate.sh setup && ./ocp_simulate.sh test' to ensure all tests pass.
#
#
# This was tested on Fedora39, and you need to install the following packages.
#   dnf install openvswitch ovn ovn-central ovn-host ovn-vtep nmap-ncat nmap
#

# Number of PODs you would like to simulate.
NUMBER_OF_PODS=${NUMBER_OF_PODS:-8}

# Port list of all UDP services we need to forward
UDP_PORT_LIST="2100 2110 2120 2130 2140 2150 2160 2170 2180"

# This is not important for now, as we do not do any inter node POD to POD
# communications. This might be interesting if we want to see the impact on
# geneve encap/decap.
ENCAP_IP=42.42.42.1

# The external interface to access the fake node. If not specified a veth pair
# is created in the 'external' namespace.
EXTERNAL_INTERFACE="ens16f1np1"


# Actual implementation starts here...
function echo_action {
    echo -e "\x1B[1m\x1B[32m$1\x1B[m"
}


function echo_error {
    echo -e "\x1B[1m\x1B[31m$1\x1B[m"
}


function echo_info {
    echo -e "\x1B[1m\x1B[33m$1\x1B[m"
}


function echo_dbg {
    echo -e "\x1B[1m\x1B[34m$1\x1B[m"
}


function show {
    ovs-vsctl show
}


function test_setup {
    # Some basic ping test from POD1 and POD2
    echo_info "ICMP ping POD2 from POD2..."
    ip netns exec pod2 ping -c 2 1.0.0.2 || \
	echo_error "Failed POD1 to POD2 ping"

    echo_info "ICMP ping POD2 from POD1..."
    ip netns exec pod1 ping -c 2 1.0.0.2 || \
	echo_error "Failed POD1 to POD2 ping"


    # Start UDP server on POD2 for remaining tests
    echo_info "Start UDP servers on POD2"
    for port in $UDP_PORT_LIST; do
	ip netns exec pod2 nc -ukl $port -c \
	   "echo -n 'SERVER_ECHO: '; /usr/bin/cat"&
    done
    sleep 1


    # Do UDP pings from POD1 and POD2's direct IP addresses
    echo_info "UDP ping POD2 from POD2..."
    for port in $UDP_PORT_LIST; do
	echo_dbg " Trying port $port..."
	result=$(ip netns exec pod2 bash -c \
		    "(echo 'Hello, server'; sleep 1) | nc -vi 1 -u 1.0.0.2 $port")
	echo "$result" | grep -q "SERVER_ECHO: Hello, server" || \
	    echo_error "Ping from POD2 to POD2 failed!"
    done

    echo_info "UDP ping POD2 from POD1..."
    for port in $UDP_PORT_LIST; do
	echo_dbg " Trying port $port..."
	result=$(ip netns exec pod1 bash -c \
		    "(echo 'Hello, server'; sleep 1) | nc -vi 1 -u 1.0.0.2 $port")
	echo "$result" | grep -q "SERVER_ECHO: Hello, server" || \
	    echo_error "Ping from POD1 to POD2 failed!"
    done


    # Do UDP pings from POD1 to POD2's service IP
    echo_info "UDP service IP ping POD2 from POD1..."
    for port in $UDP_PORT_LIST; do
	echo_dbg " Trying port $port..."
	result=$(ip netns exec pod1 bash -c \
		    "(echo 'Hello, server'; sleep 2) | nc -vi 1 -u 2.0.0.2 $port")
	echo "$result" | grep -q "SERVER_ECHO: Hello, server" || \
	    echo_error "Service IP ping from POD1 to POD2 failed!"
    done

    if [ -z "$EXTERNAL_INTERFACE" ]; then

	# NOTE THAT THE BELOW TWO TESTS WILL ONLY WORK IF YOU REMOVE THE ACLs
	# CONFIGURED.
	#
	# echo_info "ICMP ping POD2 from EXTERNAL..."
	# ip netns exec external ping -c 2 1.0.0.2 || \
	#     echo_error "Failed EXTERNAL to POD2 ping"
        #
	# # Do UDP pings from EXTERNAL to POD2's IP
	# echo_info "UDP IP ping POD2 from EXTERNAL..."
	# for port in $UDP_PORT_LIST; do
	#     echo_dbg " Trying port $port..."
	#     result=$(ip netns exec external bash -c \
	# 		"(echo 'Hello, server'; sleep 2) | nc -vi 1 -u 1.0.0.2 $port")
	#     echo "$result" | grep -q "SERVER_ECHO: Hello, server" || \
	# 	echo_error "IP ping from EXTERNAL to POD2 failed!"
	# done

	# Do UDP pings from EXTERNAL to POD2's route IP
	echo_info "UDP route IP ping POD2 from EXTERNAL..."
	for port in $UDP_PORT_LIST; do
	    echo_dbg " Trying port $port..."
	    result=$(ip netns exec external bash -c \
			"(echo 'Hello, server'; sleep 2) | nc -vi 1 -u 3.0.0.2 $port")
	    echo "$result" | grep -q "SERVER_ECHO: Hello, server" || \
		echo_error "Service IP ping from EXTERNAL to POD2 failed!"
	done
    fi

    # Kill the UDP servers
    echo_info "Kill UDP echo servers on POD2"
    ip netns exec pod2 killall nc
}


function create_pod {
    name=$1
    mac=$2
    ip=$3
    gw=$4
    service_ip=$5
    route_ips=${@:6}
    lb_name=lb_service_"$name"
    route_name=lb_route_"$name"

    echo_action "[$name] Configure POD namespace and veth pair..."
    ip netns add $name
    ip link add $name type veth peer name "$name"_eth0

    ip link set "$name"_eth0 netns $name
    ip -n $name link set dev "$name"_eth0 down
    ip -n $name link set dev "$name"_eth0 name eth0
    ip -n $name link set eth0 address $mac
    ip -n $name addr add $ip dev eth0
    ip -n $name link set lo up
    ip -n $name link set eth0 up
    ip -n $name route add default via $gw dev eth0
    ip link set $name up


    echo_action "[$name] Configure POD interface in OVS..."
    ovs-vsctl add-port br-int $name
    ovs-vsctl set interface $name external_ids:iface-id=$name


    echo_action "[$name] Configure POD interface in OVN..."
    ovn-nbctl lsp-add ls1 $name
    ovn-nbctl lsp-set-addresses $name $mac


    echo_action "[$name] Add load balancer, simulate service IPs..."
    for port in $UDP_PORT_LIST; do
	ovn-nbctl lb-add $lb_name $service_ip:$port "${ip%%/*}":$port udp
    done
    ovn-nbctl ls-lb-add ls1 $lb_name


    echo_action "[$name] Add to port group pg_vifs..."
    ovn-nbctl pg-set-ports pg_vifs $name


    echo_action "[$name] Add load balancer, simulate route IPs..."
    route_id=0
    for route_ip in $route_ips; do
	for port in $UDP_PORT_LIST; do
	    ovn-nbctl lb-add "$route_name"_"$route_id" $route_ip:$port "${ip%%/*}":$port udp
	done
	ovn-nbctl lr-lb-add gwr "$route_name"_"$route_id"

	route_id=$(expr $route_id + 1)
    done
}

function cleanup_system {
    echo_action "Stopping all services..."
    systemctl stop ovn-controller
    systemctl stop ovn-northd
    systemctl stop openvswitch


    echo_action "Remove all configuration databases..."
    rm -f /etc/openvswitch/*.db
    rm -f /var/lib/ovn/ovnnb_db.db
    rm -f /var/lib/ovn/ovnsb_db.db


    echo_action "Delete all namespaces..."
    ip -all netns del
}


function setup_system {
    # Remove all existing configurations
    cleanup_system
    sleep 1


    echo_action "Start OVS/OVN..."
    systemctl start openvswitch
    systemctl start ovn-controller
    systemctl start ovn-northd


    echo_action "Basic OVN chassis configuration..."
    ovs-vsctl set open . external_ids:ovn-encap-ip=$ENCAP_IP
    ovs-vsctl set open . external-ids:ovn-encap-type=geneve
    ovs-vsctl set open . external-ids:ovn-openflow-probe-interval=60
    ovs-vsctl set open . external-ids:ovn-remote-probe-interval=180000
    ovs-vsctl set open . external-ids:ovn-remote=tcp:127.0.0.1:6642


    echo_action "Setup OVN communication..."
    ovn-nbctl set-connection ptcp:6641
    ovn-sbctl set-connection ptcp:6642


    echo_action "Setup switches and routers..."
    local_chassis=$(ovs-vsctl get open . external_ids:system-id)

    ovn-nbctl lr-add cluster-router
    ovn-nbctl lrp-add cluster-router rtr-ls1 00:00:00:00:00:01 1.255.255.254/8
    ovn-nbctl lrp-add cluster-router rtr-ls-gw 00:00:00:01:00:00 40.0.0.1/8

    ovn-nbctl lr-route-add cluster-router 2.0.0.0/16 1.255.255.254
    ovn-nbctl lr-route-add cluster-router 0.0.0.0/0 40.0.0.2

    ovn-nbctl --wait=sb sync
    dp_uuid=$(ovn-sbctl --columns _uuid --data=bare --no-heading list Datapath_Binding cluster-router)

    ovn-nbctl ls-add ls1
    ovn-nbctl lsp-add ls1 ls1-rtr
    ovn-nbctl lsp-set-type ls1-rtr router
    ovn-nbctl lsp-set-addresses ls1-rtr 00:00:00:00:00:01
    ovn-nbctl lsp-set-options ls1-rtr router-port=rtr-ls1
    ovn-nbctl pg-add pg_vifs


    echo_action "Setup gateway switch and router..."
    ovn-nbctl ls-add ls-gw
    ovn-nbctl lsp-add ls-gw ls-gw-rtr
    ovn-nbctl lsp-set-type ls-gw-rtr router
    ovn-nbctl lsp-set-addresses ls-gw-rtr 00:00:00:01:00:00
    ovn-nbctl lsp-set-options ls-gw-rtr router-port=rtr-ls-gw

    ovn-nbctl lsp-add ls-gw ls-gw-gwr
    ovn-nbctl lsp-set-type ls-gw-gwr router
    ovn-nbctl lsp-set-addresses ls-gw-gwr 00:00:00:02:00:00
    ovn-nbctl lsp-set-options ls-gw-gwr router-port=gwr-ls-gw

    ovn-nbctl lr-add gwr
    ovn-nbctl lrp-add gwr gwr-ls-gw 00:00:00:02:00:00 40.0.0.2/8
    ovn-nbctl lrp-add gwr gwr-ext 00:00:00:03:00:00 4.255.255.254/8

    ovn-nbctl --wait=sb sync
    dp_uuid=$(ovn-sbctl --columns _uuid --data=bare --no-heading list Datapath_Binding gwr)

    ovn-nbctl ls-add ls-ext
    ovn-nbctl lsp-add ls-ext ext-gwr
    ovn-nbctl lsp-set-type ext-gwr router
    ovn-nbctl lsp-set-addresses ext-gwr 00:00:00:03:00:00
    ovn-nbctl lsp-set-options ext-gwr router-port=gwr-ext

    ovn-nbctl lsp-add ls-ext vm-ext
    ovn-nbctl lsp-set-addresses vm-ext unknown

    ovn-nbctl pg-add pg_ext
    ovn-nbctl pg-set-ports pg_ext vm-ext

    ovn-nbctl set logical_router gwr options:chassis=${local_chassis}
    ovn-nbctl lr-route-add gwr 1.0.0.0/8 40.0.0.1
    ovn-nbctl lr-route-add gwr 2.0.0.0/8 40.0.0.1


    echo_action "Setup ACLs (port security)..."

    ovn-nbctl acl-add pg_ext to-lport   1000 "outport == @pg_ext" drop
    ovn-nbctl acl-add pg_ext from-lport 1000 "inport  == @pg_ext" drop

    ovn-nbctl acl-add pg_ext to-lport   1002 "outport == @pg_ext && arp" allow
    ovn-nbctl acl-add pg_ext from-lport 1002 "inport  == @pg_ext && arp" allow

    # Accept traffic from external towards 4.0.0.0/8:80 i.e. load balancer and return traffic
    ovn-nbctl acl-add pg_ext from-lport 1001 'ip4 && ip4.dst == 3.0.0.0/8 && udp' allow-related


    echo_action "Adding external interface..."
    if [ -z "$EXTERNAL_INTERFACE" ]; then
	echo_action "Create eth0 in netns 'external'..."

	ip link add ext_ovs type veth peer name ext_eth
	ip link set dev ext_ovs up
	ip netns add external
	ip link set ext_eth netns external
	ip -n external link set dev ext_eth down
	ip -n external link set dev ext_eth name eth0
	ip -n external link set dev eth0 up
	ip -n external link set dev lo up

	ip -n external addr add 4.0.0.1/8 dev eth0
	ip -n external route add 1.0.0.0/8 via 4.255.255.254 dev eth0
	ip -n external route add 2.0.0.0/8 via 4.255.255.254 dev eth0
	ip -n external route add 3.0.0.0/8 via 4.255.255.254 dev eth0

	ovs-vsctl add-port br-int ext_ovs
	ovs-vsctl set interface ext_ovs external_ids:iface-id=vm-ext
    else
	echo_action "Add external port to gateway..."
	ovs-vsctl add-port br-int $EXTERNAL_INTERFACE
	ovs-vsctl set interface $EXTERNAL_INTERFACE external_ids:iface-id=vm-ext
    fi


    echo_action "Setup $NUMBER_OF_PODS PODS..."
    for i in $(seq 1 $NUMBER_OF_PODS); do
	hex=$(printf "%02x" $i)
	create_pod pod$i 00:00:00:00:10:$hex 1.0.0.$i/8 1.255.255.254 2.0.0.$i 3.0.0.$i 3.0.1.$i
    done
}


case "$1" in
    setup)
        setup_system
        ;;
    cleanup)
        cleanup_system
        ;;
    show)
        show
        ;;
    test)
        test_setup
        ;;
    *)
        echo_error "ERROR: Invalid Argument!!"
        echo_error "  Usage: $0 {setup|cleanup|test|show}"
        ;;
esac
