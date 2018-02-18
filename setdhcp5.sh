#!/bin/bash


APNAME="ba288"
APPASS="pass22"

if [[ $EUID != 0 ]]; then echo "Must be root"; exit 33; fi


cat > /usr/bin/autohotspot <<EOF1
#!/bin/bash
sysctl -w net.ipv4.ip_forward=1
service hostapd stop
service dnsmasq stop
iw dev wlan0 interface add uap0 type __ap
iptables -t nat -A POSTROUTING -o wlan0 -j MASQUERADE
ifdown wlan0
ip link set uap0 up
ip addr add 192.168.1.1/24 broadcast 192.168.1.255 dev uap0
service hostapd start
ifup wlan0
service dnsmasq start

EOF1

chmod +x /usr/bin/autohotspot

cat > /etc/hostapd/hostapd.conf <<EOF3
interface=uap0
driver=nl80211
ssid=amusic
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=88888888
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

EOF3

echo "DAEMON_CONF=/etc/hostapd/hostapd.conf" > /etc/default/hostapd

cat > /etc/dnsmasq.conf <<EOF4
interface=uap0
dhcp-range=192.168.1.20,192.168.1.100,255.255.255.0,12h
#addn-hosts=/etc/hosts.dnsmasq
#address=/#/192.168.1.1
EOF4

cat > /etc/network/interfaces <<EOF5
source-directory /etc/network/interfaces.d

auto wlan0
iface wlan0 inet dhcp
  wpa-ssid "$APNAME"
  wpa-psk "$APPASS"

EOF5


function one_alsa_mixer() {
cat >> /etc/asound.conf <<EOF11
pcm.dmix:$1 {
    type dmix
    ipc_key 112$1
    ipc_perm 0660
    slave {
        pcm "hw:$1"
        period_size 128
        buffer_size 256
        rate 44100
    }
}
ctl.dmix:$1 {
  type hw
  card "hw:$1"
}
EOF11
}

#rm -fv /etc/asound.conf

for COUNT in 0 1 
do
	echo #one_alsa_mixer $COUNT
done
echo "All done! Please reboot"

