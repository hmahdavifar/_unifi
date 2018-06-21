import os
import socket
import subprocess
import sys
from datetime import datetime
from subprocess import CalledProcessError

COLLECTOR_IP = socket.gethostbyname('192.168.130.123')
COLLECTOR_PORT = '4444'
TIME_INTERVAL = '15'


class RemoteHost:
    @staticmethod
    def _run_on_shell(cmd):
        result = subprocess.run(cmd, shell=True)
        if result.returncode == 0:
            print('Done.')
        else:
            print('Error!')
        return result

    def __init__(self, host_name, user_name='WS', password='inFo@WS'):
        self.host_name = host_name
        self.user_name = user_name
        self.password = password

    def copy_file(self, src, dst):
        print('copying', src, 'to', self.host_name + '...')
        return self._run_on_shell(
            str.format("sshpass -p {} scp -o StrictHostKeyChecking=no -o ConnectTimeout=7 '{}' {}@{}:{}",
                       self.password, src, self.user_name, self.host_name, dst))

    def run_cmd(self, cmd):
        cmd = cmd.replace('"', '\\"')
        print('running', cmd, 'on', self.host_name + '...')
        return self._run_on_shell(
            str.format('sshpass -p {} ssh -o StrictHostKeyChecking=no -o ConnectTimeout=7 {}@{} "{}"',
                       self.password, self.user_name, self.host_name, cmd))

    def is_accessible(self):
        print('checking', self.host_name + '...')
        if self.run_cmd('ls').returncode == 0:
            return True
        else:
            return False

    def sync_date(self):
        self.run_cmd("date -s '{}'".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    def install_script(self, script, *args):
        self.run_cmd('nohup /bin/sh {} {} &'.format(script, ' '.join(args)))


ip_to_rhost_map = {}
with open('ip_list.txt', 'r+') as ips_file:
    if '-findAll' in sys.argv:
        for i in range(0, 9):
            for j in range(0, 5):
                ip = '172.18.64.' + str(100 + 10 * i + j)
                remote = RemoteHost(ip)
                if remote.is_accessible():
                    print(ip, file=ips_file)
                    ip_to_rhost_map[ip] = remote
    else:
        for line in ips_file:
            ip_to_rhost_map[line.strip()] = RemoteHost(line.strip())
if '-cmd' in sys.argv:
    cmd = sys.argv[sys.argv.index('-cmd') + 1]
    for host in ip_to_rhost_map.values():
        host.run_cmd(cmd)
if '-copyAll' in sys.argv:
    for host in ip_to_rhost_map.values():
        for script in os.listdir('scripts'):
            host.copy_file('scripts/' + script, script)
if '-info' in sys.argv:
    for host in ip_to_rhost_map.values():
        host.run_cmd('/bin/sh read_info.sh {} {}'.format(COLLECTOR_IP, COLLECTOR_PORT))
if '-sync' in sys.argv:
    for host in ip_to_rhost_map.values():
        host.sync_date()
if '-stats' in sys.argv:
    with open('info.txt', 'r') as info_file:
        for line in info_file:
            tokens = line.split()
            if tokens[0] in ip_to_rhost_map.keys():
                ip_to_rhost_map[tokens[0]].install_script('read_stats.sh', COLLECTOR_IP, COLLECTOR_PORT, TIME_INTERVAL,
                                                          tokens[2], tokens[1])
if '-scan' in sys.argv:
    with open('info.txt', 'r') as info_file:
        for line in info_file:
            tokens = line.split()
            for host in ip_to_rhost_map.values():
                if tokens[0] == host.host_name:
                    host.install_script('do_scan.sh', COLLECTOR_IP, COLLECTOR_PORT, TIME_INTERVAL, tokens[1])
if '-peers' in sys.argv:
    with open('info.txt', 'r') as info_file:
        for line in info_file:
            tokens = line.split()
            for host in ip_to_rhost_map.values():
                if tokens[0] == host.host_name:
                    host.run_cmd('/bin/sh find_peers.sh {} {} {}'.format(COLLECTOR_IP, COLLECTOR_PORT, tokens[1]))
if '-rrm' in sys.argv:
    peers = []
    with open('rrm.txt', 'r') as rrm_file:
        aptokens = rrm_file.readline().split()
    with open('peers.txt', 'r') as peers_file:
        for line in peers_file:
            peer = line.split()
            peers.append(peer)
    if (len(peers) > 3 and int(aptokens[1]) == 27):
        if aptokens[0] in ip_to_rhost_map.keys():
            with open('info.txt', 'r') as info_file:
                for line in info_file:
                    tokens = line.split()
                    for host in ip_to_rhost_map.values():
                        if tokens[0] == host.host_name:
                            host.run_cmd('iwconfig {} txpower 63mW'.format(tokens[1]))
    elif len(peers) <= 3 and aptokens[1] != 27 :
        if aptokens[0] in ip_to_rhost_map.keys():
            with open('info.txt', 'r') as info_file:
                for line in info_file:
                    tokens = line.split()
                    for host in ip_to_rhost_map.values():
                        if tokens[0] == host.host_name:
                            host.run_cmd('iwconfig {} txpower 501mW'.format(tokens[1]))

