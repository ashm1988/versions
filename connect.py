import xml.etree.ElementTree as ET
import socket
import sys
import time
import logging
import re
import mysql.connector

logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
host = '172.28.101.10'
port = 10218

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.info('socket created')
except AttributeError as ae:
    logging.error('socket connection: ' + str(ae))
    sys.exit()

s.connect((host, port))
logging.info('connecting to $name')


message = \
    '<Handshake version=\"2.0\"/>' \
    '<Login username=\"amcfarlane\" passphrase=\"amcfarlane\" encryptMethod=\"none\"/>' \
    '<Request updateType=\"snapshot\" type=\"items\"></Request>'

try:
    s.send(message)
    logging.info('sending handshake, logging and request')
except socket.error:
    logging.error('send failed')
    sys.exit()


def receive_data(the_socket, timeout=2):
    logging.debug('setting socket to none blocking')
    s.setblocking(0)

    # total data in array
    total_data = []

    # beginning = time now
    begin = time.time()
    while 1:
        # if you got some data, then break after timeout
        if total_data and time.time() - begin > timeout:
            break

        # if you got no data at all, wait a little longer, twice the timeout
        elif time.time() - begin > timeout*2:
            break

        # receive something
        try:
            data = the_socket.recv(8192)
            if data:
                total_data.append(data)
                # change the beginning time for measurement
                begin = time.time()
            else:
                # sleep for sometime to indicate a gap
                time.sleep(0.1)
        except:
            pass

    # Check successful connection, remove handshake and logging response then join all parts to make xml string
    s.close()
    if re.match(r'.*success.*', total_data[1]):
        logging.info('logging successful')
        total_data.remove(total_data[0])
        total_data.remove(total_data[0])
    else:
        logging.error(total_data[1])
        sys.exit()

    return ''.join(total_data)


def process_data(received_data):
    logging.info('Collecting server info')
    fix_acceptors = []
    xmlroot = ET.fromstring(received_data)
    instanceid = 0
    data = {
        "server": ['Server: ', ".//Item[@name='System']/Item[@name='Hostname']"],
        "instance": ['Instance name: ', ".//Item[@name='Identity']/Item[@name='Name']"],
        "product": ['Product: ', ".//Item[@name='Identity']/Item[@name='Description']"],
        "core": ['Core Version: ', ".//Item[@name='Identity']/Item[@name='Version']"],
        "otl": ['OTL Version: ', ".//Item[@name='Exchange Adapters']//Item[@name='Version']"],
        "licence": ['Licence Expiry: ', ".//Item[@name='Licence']/Item[@name='Expiry']"],
        "adapter": ['Adapter Logging Enabled: ',
                    ".//Item[@name='Exchange Adapters']//Item[@name='Configuration']//Item[@name='Enabled']"],
        "frapi": ['FRAPI Logging Enabled: ',
                  ".//Item[@name='Client Adapters']//Item[@name='FRAPI2']//Item[@name='Enabled']"]
    }
    # finds the available acceptors and places them in a list called fix_acceptors
    for acceptors in xmlroot.find(".//Item[@name='Client Adapters']/Item[@name='FIX']/Item[@name='Acceptors']"):
        fix_acceptors.append(acceptors.attrib.get('name'))
    # Adds available fix acceptors to the data list
    for acceptor in fix_acceptors:
        data["%s" % acceptor.lower()] = ["%s Logging Enabled: " % acceptor,
                                         ".//Item[@name='Client Adapters']//Item[@name='%s']//Item[@name='Enabled']" % acceptor]

    for instance in data:
        data[instance].append(xmlroot.find(data[instance][1]).attrib.get('value'))
        logging.debug(data[instance][0] + xmlroot.find(data[instance][1]).attrib.get('value'))

    instanceid += 1
    return data


def dbupdate(data):
    config = {
        'user': 'root',
        'password': '',
        'host': '127.0.0.1',
        'database': 'versions',
        'autocommit': True,
    }

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
        "`fix42` VARCHAR(5))"
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
        "`fix42` VARCHAR(5))"
    )

    cnx = mysql.connector.connect(**config)
    cnx.get_warnings = True
    cur = cnx.cursor(buffered=False)


    logging.debug("Create tables if they do not already exist")
    for table in tables:
        cur.execute(tables[table])

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

    statements = "SET @tday=curdate(); " \
                 "INSERT INTO `archive` " \
                 "(`id`,`date`,`server`,`instance`,`product`,`core`,`otl`,`licence`,`adapter`,`frapi`,`fix50`, " \
                 "`fix50sp1`,`fix42`) " \
                 "SELECT `id`,@tday,`server`,`instance`,`product`,`core`,`otl`,`licence`,`adapter`, " \
                 "`frapi`,`fix50`,`fix50sp1`,`fix42` " \
                 "FROM `current`;"

    for statement in cur.execute(statements, multi=True):
        pass

    logging.debug("Update database with details")
    cur.execute("INSERT INTO `current` (`id`) VALUES ('%s')" % instance_id)
    for result in data:
        cur.execute("UPDATE `current` SET `%s`='%s' WHERE `id` = %s" % (result, data[result][2], instance_id))
        logging.debug("UPDATE `current` SET `%s`='%s' WHERE `id` = %d sent to the database", result, data[result][2], instance_id)

    cnx.commit()
    cur.close()
    cnx.close()



dbupdate(process_data(receive_data(s)))