import sys
import os
import random
import time
import multiprocessing
import pcapy
import dpkt

# mac
interface = 'en0'
enable_monitor  = 'tcpdump -i en0 -Ic1 -py IEEE802_11'
disable_monitor = 'tcpdump -i en0 -Ic1'
change_channel  = 'airport -c{}'

# linux
# interface = 'mon0'
# enable_monitor  = 'ifconfig wlan1 down; iw dev wlan1 interface add mon0 type monitor; ifconfig mon0 down; iw dev mon0 set type monitor; ifconfig mon0 up; ifconfig wlan1 up'
# disable_monitor = 'iw dev mon0 del'
# change_channel  = 'iw dev mon0 set channel {}'

channels = [
    1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, # 2.4GHz
    36, 40, 44, 48, 52, 56, 60, 64, 100, 104, 108, 112, 116, 120, 124, 128, 132, 136, 140, 149, 153, 157, 161 # 5GHz
]

def start():
    os.system(enable_monitor)
    rotator(channels, change_channel)
    try: sniff(interface)
    except KeyboardInterrupt as e: sys.exit(e)
    finally: os.system(disable_monitor)

def rotator(channels, change_channel):
    def hop():
        while True:
            try:
                channel = random.choice(channels)
                print('Changing to channel ' + str(channel) + '...')
                os.system(change_channel.format(channel))
                time.sleep(1) # seconds
            except BaseException as e: sys.exit(e)
    multiprocessing.Process(target=hop).start()

def to_address(address): # decode a MAC or BSSID address
    return ':'.join('%02x' % ord(b) for b in address)

def sniff(interface):
    max_packet_size = 256 # bytes
    promiscuous = 0 # boolean masquerading as an int
    timeout = 100 # milliseconds
    packets = pcapy.open_live(interface, max_packet_size, promiscuous, timeout)
    packets.setfilter('') # bpf syntax (empty string = everything)
    def loop(header, data):
        packet = dpkt.radiotap.Radiotap(data)
        frame = packet.data
        if frame.type == dpkt.ieee80211.MGMT_TYPE:
            body = frame.mgmt
            body_source = to_address(body.src)
            body_destination = to_address(body.dst)
            body_bssid = to_address(body.bssid) # access point address
            request_type = str(frame.subtype) # listed here: https://github.com/kbandla/dpkt/blob/b8fe25c7b310954daca86df730e36eaa2d06fb19/dpkt/ieee80211.py#L15
            print('[MANAGEMENT FRAME]  ' + request_type + ' * ' + body_bssid + ' * ' + body_source + ' => ' + body_destination)
        elif frame.type == dpkt.ieee80211.CTL_TYPE:
            print('[CONTROL FRAME]')
        elif frame.type == dpkt.ieee80211.DATA_TYPE:
            print('[DATA FRAME]')
    packets.loop(-1, loop)

start()
