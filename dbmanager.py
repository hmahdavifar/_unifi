import json
import urllib.error
import urllib.parse
import urllib.request
import urllib.response

# todo: check dbmanager thread safety
DB_NAME = 'testtest'
DB_SERVER_URL = 'http://213.233.168.27:8086'
CHANNEL_TAG_KEY = 'channel'
MAC_TAG_KEY = 'mac'
ESSID_TAG_KEY = 'essid'
INFO_FILE_PATH = 'info.txt'

info2ip_map = {}


class ApInfo:
    def __init__(self, mac, essid, channel):
        self.mac = mac
        self.essid = essid
        self.channel = channel

    def get_influx_format(self):
        legal_essid = self.essid.replace(' ', '\ ').replace(',', '\,')
        if self.essid == '':
            legal_essid = '_NO_ESSID_'
        return str.format('mac={},essid={},channel={}', self.mac, legal_essid, self.channel)

    def __hash__(self):
        return hash(self.mac) + hash(self.channel)

    def __eq__(self, other):
        return self.mac == other.mac and self.channel == other.channel

    def __str__(self):
        return str.format('{}\t{}\t{}', self.mac, self.essid, self.channel)


def get_measure(ip):
    return 'Ap.' + ip.split('.')[3] + '.scan' #put print here


def load_info2ip_map():
    with open(INFO_FILE_PATH, 'r') as file:
        for line in file:
            print(line)
            tokens = line.split()
            info2ip_map[ApInfo(tokens[3], tokens[4], tokens[5])] = tokens[0]


def write_info(owner_ip, ng_interface, wifi_interface, ap_info):
    with open(INFO_FILE_PATH, 'a') as file:
        file.write(str.format('{}\t{}\t{}\t{}\n', owner_ip, ng_interface, wifi_interface, ap_info))


def write_scan_results(owner_ip, data, time_stamp):
    data_influx = ''
    for (info, signal) in data:
        data_influx += str.format('{},{} value={} {}\n', get_measure(owner_ip), info.get_influx_format(), signal,
                                  time_stamp)
    print(data_influx)
    print('count=', len(data))
    _write_to_db(data_influx, DB_NAME)


def write_stats(owner_ip, stats, time_stamp):
    data_str = 'stats,ap=Ap.{} '.format(owner_ip.split('.')[3])
    for (stats_name, value) in stats:
        data_str += '{}={},'.format(stats_name, value)
    data_str = data_str.rpartition(',')[0]
    data_str += ' {}\n'.format(time_stamp)
    print(data_str)
    _write_to_db(data_str, DB_NAME)


def _write_to_db(data, db_name):
    write_url = DB_SERVER_URL + '/write?' + urllib.parse.urlencode({'db': db_name, 'precision': 's'})
    try:
        with urllib.request.urlopen(write_url, data.encode('ascii')) as response:
            print(response.read())
    except urllib.error.HTTPError as e:
        print(e, e.info())


def _exec_query(q, db_name):
    http_query = urllib.parse.urlencode({'db': db_name, 'q': q})
    print(http_query)
    with urllib.request.urlopen(DB_SERVER_URL + '/query?' + http_query) as response:
        return json.loads(response.read().decode('utf-8'))


def read_neighbours(ap_info, duration, strength_threshold):
    influx_query = str.format('SELECT MEAN("value") FROM "{}" '
                              'WHERE "time" > now() - {} '
                              'GROUP BY "mac","essid","channel"', get_measure(info2ip_map[ap_info]), duration)
    print(influx_query)
    results = _exec_query(influx_query, DB_NAME)['results']
    print(results)
    if results[0]:
        series = results[0]['series']
    else:
        series = {}
    return [(ApInfo(s['tags']['mac'], s['tags']['essid'], s['tags']['channel']), s['values'][0][1]) for s in series
            if s['values'][0][1] > strength_threshold]