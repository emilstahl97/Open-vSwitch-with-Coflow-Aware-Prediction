learned_macs_in_ovn=$(sudo ovn-sbctl list fdb | grep mac | wc -l)
echo "Number of MACs learned by OVN: $learned_macs_in_ovn"
learned_macs_in_ovs=$(sudo ovs-ofctl dump-flows br-int | grep "table=72" | wc -l)
echo "Number of MACs learned by OVS: $learned_macs_in_ovs"   


