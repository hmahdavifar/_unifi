import socket
import sys
import threading
import dbmanager

PORT = 4444  # Arbitrary non-privileged port for listening


class ClientThread(threading.Thread):
    def __init__(self, client_ip, client_port, client_socket):
        threading.Thread.__init__(self)
        self.client_ip = client_ip
        self.client_port = client_port
        self._client_socket = client_socket

    def run(self):
        print("Connection from : " + self.client_ip + ":" + str(self.client_port))
        with self._client_socket as s:
            message = s.makefile()
            request_type = message.readline()
            print(request_type)
            if request_type == '<< put iwlist scan results >>\n':
                self._handle_put_scan(message)
            elif request_type == '<< put error statistics >>\n':
                self._handle_put_stats(message)
            elif request_type == '<< put config info >>\n':
                self._handle_put_info(message)
            elif request_type == '<< put iwlist peers results >>\n':
                self._handel_put_peers(message)
            else:
                print('Bad Request from ' + self.client_ip)

    def _handle_put_scan(self, message):
        time_stamp = message.readline().strip()
        data = []
        state = 0
        for line in message:
            if state == 0 and "Address:" in line:  # never change this block
                mac = line[line.index("Address:") + 8:].strip()
                state = 1
            elif state == 1 and "ESSID:" in line:
                essid = line[line.index(":") + 1:-1].replace('"', '')
                state = 2
            elif state == 2 and "Frequency:" in line:
                if line[line.index(":") + 1] == "2":
                    channel = line[line.index("(") + 1:line.index(")")]
                    channel = channel[channel.index(" ") + 1:]
                    state = 3
                else:
                    state = 0
            elif state == 3 and "Signal level=" in line:
                signal_level = line[line.index("=") + 1:]
                signal_level = signal_level[signal_level.index("=") + 1:]
                signal_level = signal_level[:signal_level.index(" ")]
                data.append(tuple([dbmanager.ApInfo(mac, essid, channel), signal_level]))
                state = 0
            elif line == '<< end >>\n':
                break
        else:
            raise Exception('unterminated message!!!')
        dbmanager.write_scan_results(self.client_ip, data, time_stamp)

    def _handle_put_info(self, message):
        print(message)
        state = 0
        for line in message:
            if state == 0 and ('ESSID:' and 'IEEE 802.' in line):
                next_line = message.readline()
                mac = next_line.split('Access Point:')[1].strip()
                if ":" in mac:  # mac seems to be a valid mac
                    freq = float(next_line.split('Frequency:')[1].split()[0])
                    if freq < 3:  # this is a 2.4GHz interface
                        ng_iface = line.split(maxsplit=1)[0]
                        essid = line.split('"')[1]
                        channel = _get_channel(freq)
                        state = 1
            elif state == 1 and ('wifi' and 'encap:UNSPEC' and mac[3:].replace(':', '-') in line):
                wifi_iface = line.split()[0]
                state = 2
                break
        if state != 2:
            raise Exception('parse error!!!')
        dbmanager.write_info(self.client_ip, ng_iface, wifi_iface, dbmanager.ApInfo(mac, essid, channel))

    def _handle_put_stats(self, message):
        time_stamp = message.readline().strip()
        stats = []
        for line in message:
            print(line)
            if line == '<< end >>\n':
                break
            tokens = line.strip().split('=')
            stats.append((tokens[0], tokens[1]))
        else:
            raise Exception('unterminated message!!!')
        dbmanager.write_stats(self.client_ip, stats, time_stamp)

    def _handel_put_peers(self, message):
        peers = []
        for line in message:
            if line == '<< end >>\n':
                break
            if 'Quality' in line:
                tokens = line.split()
                mac = tokens[0]
                quality = tokens[2].split('=')
                quality = quality[1]
                signal = tokens[4].split('=')
                signal = signal[1]
                noise = tokens[7].split('=')
                noise = noise[1]
                peer = (mac, quality, signal, noise)
                peers.append(peer)
            if 'Tx-Power' in line:
                power = line.split('Tx-Power=')[1].split()[0]
            if 'Frequency' in line:
                freq = line.split('Frequency:')[1].split()[0]
                channel = _get_channel(float(freq))
        else:
            raise Exception('unterminated message!!!')
        dbmanager.pre_rrm(self.client_ip, power, channel, peers)


def _get_channel(freq):
    assert freq < 3
    return int((freq - 2.412) / 0.005 + 1)


listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
print('Socket created')
# Bind socket to local host and port
try:
    listening_socket.bind(('', PORT))  # listening on all addresses
except socket.error as msg:
    print('Bind failed. Error Code: ', msg)
    sys.exit()
print('Socket bind complete')
# Start listening on socket
# max queue length is 10
listening_socket.listen(10)
while True:
    # wait to accept a connection - blocking call
    try:
        (client_sock, (ip, port)) = listening_socket.accept()
        new_thread = ClientThread(ip, port, client_sock)
        new_thread.run()
    except Exception as e:
        print('Client thread closed: ', e, file=sys.stderr)
listening_socket.close()



