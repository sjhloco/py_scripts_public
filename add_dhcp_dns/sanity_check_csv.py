#!/usr/bin/env python

import os
from os.path import expanduser
import csv
import ipaddress
import sys

################# Variables to change dependant on environment #################
# Sets it has users home directory
directory = expanduser("~")
# to toggle between windows and linux (used for ping)
WINDOWS = False


################# Makes sure IP addresses are in valid format #################

# 1. Open CSV file and create a list of tuples (ip_add, domain_name)
ipadd_domain1 = []                           # list to store tuples
def read_csv(csv_file):
    with open(csv_file, 'r') as x:          # Open file
        csv_read = csv.reader(x)			# Read the csv file
        for row in csv_read:                # For each row converts to tuple and adds to list
            ipadd_domain1.append(tuple(row))
    ipadd_domain = ipadd_domain1[1:]        # Removes the header column
    verify(ipadd_domain)                    # Runs 2

# 2. Make sure that the IP addresses are in the correct format, if not ends exits script
def verify(ipadd_domain):
    ip_error = []                                   # List to store invalid IPs
    for ip in ipadd_domain:
        try:                                    # Checks if IPs are valid, gathers list of non-valid IPs
            ipaddress.ip_address(ip[0])
        except ValueError as errorCode:
            ip_error.append(str(errorCode))     # If invalid adds to list
    # Exits script if there was an ip address error (list not empty)
    if len(ip_error) != 0:                          # If invalid IP list is not empty
        print("!!!ERROR - Invalid IP addresses entered !!!")
        for x in ip_error:
            print(x)                                # Prints bad IPs and stops script
        exit()







# 6. Runs the script
csv_file = os.path.join(directory, "test.csv")
read_csv(csv_file)







# import subprocess





