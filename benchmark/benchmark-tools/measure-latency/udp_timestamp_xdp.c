/*
 * Build using:
 *   clang -O2 -g -Wall -target bpf -c xdp_prog.c -o xdp_prog.o -I /usr/include/bpf/
 *
 * Load using:
 *   ip link add xdp_veth type veth peer name xdp_eth0
 *   xdp-loader load -vv -m skb -s udp_timestamp_ingress xdp_veth xdp_prog.o
 *
 */

#include <linux/bpf.h>
#include "bpf_helpers.h"
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/udp.h>

#ifndef __bpf_htons
#define __bpf_htons(x) ((__be16)___constant_swab16((x)))
#endif

struct pkt_delay {
    __u64 pkt_id;
    __u64 ingress_ts;
    __u64 egress_ts;
};

SEC("udp_timestamp_ingress")
int xdp_timestamp_ingress(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    struct iphdr *ip = (struct iphdr *)(eth + 1);
    struct udphdr *udp = (struct udphdr *)(ip + 1);
    struct pkt_delay *delay = (struct pkt_delay *)(udp + 1);

    /*
     * Packet is not big enough to hold all data we need to access, so no need
     * to process this further.
     */
    if ((void *)(delay + 1) > data_end)
	return XDP_PASS;
	
    
    /* Check if this is UDP, if so we assume we can modify the packet. */
    if (eth->h_proto != __bpf_htons(ETH_P_IP) || ip->protocol != IPPROTO_UDP)
        return XDP_PASS;

    /*
     * We assume that the pkt_id is set when the PCAP are generated, and we
     * only set the ingress_ts on the physical interface, and the egress_ts
     * when transmitting on the veth pair simulating the POD. This means we need
     * two program.
     */
    delay->ingress_ts = bpf_ktime_get_ns();
    delay->egress_ts = 0;

    return XDP_PASS;
}

SEC("udp_timestamp_egress")
int xdp_timestamp_egress(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    struct iphdr *ip = (struct iphdr *)(eth + 1);
    struct udphdr *udp = (struct udphdr *)(ip + 1);
    struct pkt_delay *delay = (struct pkt_delay *)(udp + 1);

    if ((void *)(delay + 1) > data_end)
	return XDP_PASS;
	
    
    if (eth->h_proto != __bpf_htons(ETH_P_IP) || ip->protocol != IPPROTO_UDP)
        return XDP_PASS;

    delay->egress_ts = bpf_ktime_get_ns(); 

    return XDP_PASS;
}