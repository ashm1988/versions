import xml.etree.ElementTree as ET
import logging


logging.basicConfig(level=logging.DEBUG)
server_type = "Production"
FRVersion = "FR4"


def collect_ports():
    logging.info('creating connection dictionary from Connections.xml')
    connections = {}
    confile = ET.parse("Connections.xml")
    root = confile.getroot()
    for ConnectionConfiguration in root.findall('ConnectionConfiguration'):
        if ConnectionConfiguration.find("FRVersion").text == FRVersion and \
                ConnectionConfiguration.find("Category").text == server_type:
            connections[ConnectionConfiguration.find("Name").text] = ConnectionConfiguration.find("Category").text, \
                                                                    ConnectionConfiguration.find("Type").text, \
                                                                    ConnectionConfiguration.find("FRVersion").text, \
                                                                    ConnectionConfiguration.find("Address").text, \
                                                                    ConnectionConfiguration.find("AnalyticsPort").text,\
                                                                    ConnectionConfiguration.find("Username").text, \
                                                                    ConnectionConfiguration.find("Password").text

    # """ list connections saved """
    for server in connections:
        if connections[server][0] == server_type and connections[server][2] == FRVersion:
            logging.debug('Connections: %s %s', server, connections[server])

    # """ Count connections """
    if len(connections) > 0:
        logging.info('Number of connections: %s', len(connections))
    else:
        logging.warning('No connection details')

    return connections




def main():
    collect_ports()


print main()