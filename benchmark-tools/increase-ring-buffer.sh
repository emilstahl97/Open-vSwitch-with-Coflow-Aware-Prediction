sudo nmcli connection modify ens16f1np1 ethtool.ring-rx 8192
sudo nmcli connection up ens16f1np1
sudo nmcli connection show
sudo ethtool -g ens16f1np1
