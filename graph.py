import dbmanager

DURATION = '15m'
STRENGTH_THRESHOLD = -82


class Node:
    def __init__(self, node_id, data):
        self.id = node_id
        self.data = data
        self._adj_list = {}

    def add_neighbour(self, node, weight):
        assert node not in self._adj_list
        self._adj_list[node] = weight

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return isinstance(other, Node) and self.id == other.id

    def get_neighbours(self):
        return self._adj_list.items()


class Graph:
    def __init__(self):
        self._nodes = []
        self._data_to_nodes_map = {}

    def get_node(self, data):
        result = self._data_to_nodes_map.get(data)
        if result is None:
            result = Node(len(self._nodes) + 1, data)
            self._nodes.append(result)
            self._data_to_nodes_map[data] = result
        return result


g = Graph()
dbmanager.load_info2ip_map()
fringe = dbmanager.info2ip_map.keys()
for fringe_ap_info in fringe:
    v = g.get_node(fringe_ap_info)
    for (ap_info, signal_strength) in dbmanager.read_neighbours(fringe_ap_info, DURATION, STRENGTH_THRESHOLD):
        u = g.get_node(ap_info)
        print(v.data, '---->', u.data)
        v.add_neighbour(u, signal_strength)

nodes_json = ''
for node in g._nodes:
    label = node.data.essid
    if node.data in fringe:
        label = dbmanager.info2ip_map[node.data] + "\\n" + node.data.mac
    nodes_json += str.format('{{id: {}, label: "{}", group: {}}},', node.id, label, node.data.channel)
nodes_json = '[' + nodes_json + ']'

edges_json = ''
index = 1
removable_ids = ''
for v in g._nodes:
    for (u, w) in v.get_neighbours():
        if v.data.channel != u.data.channel:
            removable_ids += str(index) + ','
        edges_json += str.format('{{id: {}, from: {}, to: {}, w: {}}},', index, v.id, u.id, w)
        index += 1
edges_json = '[' + edges_json + ']'

with open('init.js', 'w') as file:
    file.write(str.format('var nodes = new vis.DataSet({});\n', nodes_json))
    file.write(str.format('var edges = new vis.DataSet({});\n', edges_json))
    file.write(str.format('rm_list = [{}]\n', removable_ids))

