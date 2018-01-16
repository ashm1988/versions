import xml.etree.ElementTree as ET
import socket
import sys
import time
import logging
import re
import mysql.connector
import datetime
import argparse


data = [
    "a",
    "b",
    "c",
    "d",
    "e"
]

del data[:0]
print data