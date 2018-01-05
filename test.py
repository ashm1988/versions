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
    '<Login username=\"amcfarlane\" passphrase=\"amcfrlane\" encryptMethod=\"none\"/>' \
    '<Request updateType=\"snapshot\" type=\"items\"></Request>'

try:
    s.send(message)
    logging.info('sending handshake, logging and request')
except socket.error:
    logging.error('send failed')
    sys.exit()


def receive_data(the_socket):
    logging.debug('setting socket to none blocking')
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

    s.close()
    logging.info('logging successful')
    total_data.remove(total_data[0])
    total_data.remove(total_data[0])
    xml = ''.join(total_data)
    return xml

receive_data(s)