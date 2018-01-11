import xml.etree.ElementTree as ET
import socket
import sys
import time
import logging
import re
import mysql.connector
import datetime



logging.basicConfig(format='%(asctime)s: %(levelname)s: %(message)s', level=logging.DEBUG)
host = '172.28.101.10'
port = 10308

data = {
    "server": ['Server: ', ".//Item[@name='System']/Item[@name='Hostname']", 3],
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

print len(data['server'])
