import xml.etree.ElementTree as ET
import mysql.connector
import argparse
import datetime
import logging
import socket
import sys
import re

# logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', filename='error.log', filemode='w', level=logging.INFO)
logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
FRVersion = "FR4"
# db_config = {
#     'user': 'otsupport',
#     'password': '0tsupp0rt',
#     'host': '192.168.105.99',
#     'database': 'versions',
#     'autocommit': True,
# }
db_config = {
    'user': 'root',
    'password': '',
    'host': '127.0.0.1',
    'database': 'versions',
    'autocommit': True,
}


def collect_ports(category, connection_file):
    """ Collects the below data from the Connections xml """
    logging.debug('creating connection dictionary from Connections.xml')
    connections = {}
    confile = ET.parse(connection_file)
    root = confile.getroot()
    # Creates a dictionary of connections
    for ConnectionConfiguration in root.findall('ConnectionConfiguration'):
        if ConnectionConfiguration.find("FRVersion").text == FRVersion and \
                ConnectionConfiguration.find("Category").text == category and \
                ConnectionConfiguration.find("Enabled").text == "true":
            connections[ConnectionConfiguration.find("Name").text] = ConnectionConfiguration.find("Category").text, \
                                                                    ConnectionConfiguration.find("Type").text, \
                                                                    ConnectionConfiguration.find("FRVersion").text, \
                                                                    ConnectionConfiguration.find("Address").text, \
                                                                    ConnectionConfiguration.find("AnalyticsPort").text,\
                                                                    ConnectionConfiguration.find("Username").text, \
                                                                    ConnectionConfiguration.find("Password").text

    # log all connections
    for server in connections:
        if connections[server][0] == category and connections[server][2] == FRVersion:
            logging.debug('Connections: %s %s', server, connections[server])

    # Count connections and log
    if len(connections) > 0:
        logging.info('Number of connections: %s', len(connections))
    else:
        logging.error('No connection details')

    return connections


def connect_socket(host, port, connection):
    """ Creates a socket connection, connects to the connections in the dictionary and sends log on request """
    # try and make a socket connection
    try:
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        logging.debug('socket created')
    except socket.error as err:
        logging.error('socket connection: ' + str(err))
        sys.exit()

    # Connect to the server
    logging.debug("connecting to %s", connection)
    try:
        new_socket.connect((host, port))
    except socket.error as err:
        logging.error(err)
        sys.exit()

    message = \
        '<Handshake version=\"2.0\"/>' \
        '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>' \
        '<Request updateType=\"snapshot\" type=\"items\"></Request>'

    # Send log on message
    try:
        new_socket.send(message)
        logging.debug('sending handshake, login and requests')
    except socket.error:
        logging.error('send failed')
        sys.exit()

    return new_socket


def receive_data(the_socket):
    total_data = []

    while 1:
        data = the_socket.recv(8192)
        if not re.search(r'result="error"', data):
            if not re.search(r"</Response>", data):
                total_data.append(data)
            else:
                total_data.append(data)
                break
        else:
            total_data.append(data)
            logging.error(total_data)
            sys.exit()

    the_socket.close()
    logging.debug('Connection to analytics successful and data received')
    del total_data[:2]
    # total_data.remove(total_data[0])
    # total_data.remove(total_data[0])
    xml = ''.join(total_data)
    # logging.debug("Received data: "+xml)
    return xml


def process_data(received_data):
    logging.debug('process_data: Collecting server info')
    fix_acceptors = []
    xmlroot = ET.fromstring(received_data)
    data = {
        "server": ['Server: ', ".//Item[@name='System']/Item[@name='Hostname']"],
        "instance": ['Instance name: ', ".//Item[@name='Identity']/Item[@name='Name']"],
        "product": ['Product: ', ".//Item[@name='Identity']/Item[@name='Description']"],
        "core": ['Core Version: ', ".//Item[@name='Identity']/Item[@name='Version']"],
        "otl": ['OTL Version: ', ".//Item[@name='Exchange Adapters']//Item[@name='Version']"],
        "licence": ['Licence Expiry: ', ".//Item[@name='Licence']/Item[@name='Expiry']"],
    }

    # if fix acceptors exist add them to the dictionary
    if re.search(r'4.1', xmlroot.find(data['core'][1]).attrib.get('value')) and \
            re.search(r'FrontTrade', xmlroot.find(data['product'][1]).attrib.get('value')):
        # finds the available acceptors and places them in a list called fix_acceptors
        for acceptors in xmlroot.find(".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']"):
            fix_acceptors.append(acceptors.attrib.get('name'))
        # Adds available fix acceptors to the data list
        for acceptor in fix_acceptors:
            data["%s" % acceptor.lower()] = ["%s Logging Enabled: " % acceptor,
                                             ".//Item[@name='Client Adapters']//Item[@name='%s']//Item[@name='Enabled']" % acceptor]
        data['frapi'] = ['FRAPI Logging Enabled: ',
                         ".//Item[@name='Client Adapters']//Item[@name='FRAPI2']//Item[@name='Enabled']"]
        data['adapter'] = ['Adapter Logging Enabled: ',
                           ".//Item[@name='Exchange Adapters']//Item[@name='Configuration']//Item[@name='Enabled']"]

    # add value to dictionary
    for instance in data:
        logging.debug("Getting %s", instance)
        data[instance].append(xmlroot.find(data[instance][1]).attrib.get('value'))
        logging.info(data[instance][0] + xmlroot.find(data[instance][1]).attrib.get('value'))

    return data


def archive_database(config):
    cnx = mysql.connector.connect(**config)
    cnx.get_warnings = True
    cur = cnx.cursor(buffered=False)

    tables = {}

    tables['current'] = (
        "CREATE TABLE IF NOT EXISTS `current` ("
        "`id` SMALLINT NOT NULL AUTO_INCREMENT , PRIMARY KEY (`id`),"
        "`server` VARCHAR(35) NOT NULL,"
        "`instance` VARCHAR(35) NOT NULL,"
        "`product` VARCHAR(35) NOT NULL,"
        "`core` VARCHAR(35) NOT NULL,"
        "`otl` VARCHAR(35) NOT NULL,"
        "`licence` VARCHAR(35) NOT NULL,"
        "`adapter` VARCHAR(5),"
        "`frapi` VARCHAR(5),"
        "`fix50` VARCHAR(5),"
        "`fix50sp1` VARCHAR(5),"
        "`fix50sp1-dc` VARCHAR(5),"
        "`fix44` VARCHAR(5),"
        "`fix44-dc` VARCHAR(5))"
    )

    tables['archive'] = (
        "CREATE TABLE IF NOT EXISTS `archive` ("
        "`id` SMALLINT NOT NULL,"
        "`date` DATE NOT NULL,"
        "`server` VARCHAR(35) NOT NULL,"
        "`instance` VARCHAR(35) NOT NULL,"
        "`product` VARCHAR(35) NOT NULL,"
        "`core` VARCHAR(35) NOT NULL,"
        "`otl` VARCHAR(35) NOT NULL,"
        "`licence` VARCHAR(35) NOT NULL,"
        "`adapter` VARCHAR(5),"
        "`frapi` VARCHAR(5),"
        "`fix50` VARCHAR(5),"
        "`fix50sp1` VARCHAR(5),"
        "`fix50sp1-dc` VARCHAR(5),"
        "`fix44` VARCHAR(5),"
        "`fix44-dc` VARCHAR(5))"
    )

    logging.debug("Create tables if they do not already exist")
    for table in tables:
        cur.execute(tables[table])

    tday = datetime.date.today().strftime("%Y-%m-%d")
    archive_statements = "INSERT INTO `archive` " \
                         "(`id`,`date`,`server`,`instance`,`product`,`core`,`otl`,`licence`,`adapter`,`frapi`,`fix50`," \
                         "`fix50sp1`,`fix50sp1-dc`,`fix44`) " \
                         "SELECT `id`,'%s',`server`,`instance`,`product`,`core`,`otl`,`licence`,`adapter`," \
                         "`frapi`,`fix50`,`fix50sp1`,`fix50sp1-dc`,`fix44` " \
                         "FROM `current`;" % tday

    logging.debug("archiving database")
    cur.execute(archive_statements)

    truncate_statement = "TRUNCATE TABLE `current`"
    logging.debug("Truncating current table")
    cur.execute(truncate_statement)

    cnx.commit()
    logging.debug("committing data")
    cur.close()
    cnx.close()


def dbupdate(data, config):
    cnx = mysql.connector.connect(**config)
    cnx.get_warnings = True
    cur = cnx.cursor(buffered=False)

    logging.debug("Check if there is data in the current table")
    cur.execute("SELECT * FROM current")
    count = []
    for line in cur:
        count.append(line[0])
    if len(count) != 0:
        instance_id = max(count) + 1
    else:
        instance_id = 1
    logging.debug("Set next instance_id to %d", instance_id)

    logging.debug("Update database with details")
    cur.execute("INSERT INTO `current` (`id`) VALUES ('%s')" % instance_id)
    for result in data:
        cur.execute("UPDATE `current` SET `%s`='%s' WHERE `id` = %s" % (result, data[result][2], instance_id))
        logging.debug("UPDATE `current` SET `%s`='%s' WHERE `id` = %d sent to the database", result, data[result][2], instance_id)

    cnx.commit()
    logging.debug("committing data")
    cur.close()
    cnx.close()


def main():
    failed = 0
    successful = 0
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--category", default="TestBed", choices=["Production", "TestBed", "BuildOut"],
                        help="Server Category i.e. Production, TestBed (default: %(default)s")
    parser.add_argument("-f", "--connection_file", default="Connections.xml", help="Path to Connections.xml")
    args = parser.parse_args()
    connections = collect_ports(args.category, args.connection_file)
    archive_database(db_config)
    for connection in connections:
        try:
            logging.info('Connecting to %s', connection)
            socket = connect_socket(connections[connection][3], int(connections[connection][4]), connection)
            xml = receive_data(socket)
            data = process_data(xml)
            dbupdate(data, db_config)
            logging.info("%s Completed", connection)
            successful += 1
        except:
            logging.error("%s failed", connection)
            failed += 1
            continue

    logging.info("Script finished")
    logging.info("%s failed", str(failed))
    logging.info("%s successful", str(successful))


if __name__ == "__main__":
    main()
