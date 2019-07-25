# This script is to go through ASA access list (read from the device or a file) and produce human readable xl file.
import csv
import os
from os.path import expanduser
from sys import exit
import ipaddress
from ipaddress import IPv4Network
from getpass import getpass
from netmiko import Netmiko

################# Variables to change dependant on environment #################
# Sets it has users home directory
directory = expanduser("~")
# To change the default header values in the CSV file
csv_columns = ['ACL Name', 'Line Number', 'Access', 'Protocol', 'Source Address',
               'Source Port', 'Destination Address', 'Destination Port', 'Hit Count']

################################## Gather information from user ##################################
# 1. Welcome and nformational screen
def start():
    global against_asa

    print()
    print('=' * 30, 'ASA ACL Auditer v0.1 (tested 9.6)', '=' * 30)
    print('This tool can be used to search IPs or all addresses in specific or all ACLs')
    print('Make sure a space is left between entries and that capitliaztion is correct for ACL names')
    print('The output will be stored in a CSV file saved in your the home directory')
    print('If searching against a file put it in your home directory. The file has to contain expanded access-lists (show access-list)')
    print()
    # Options of whether to test against an ASA or a static file.
    while True:
        print('Do you want to grab the ACL config from an ASA or use a file?')
        print('1. Search against a ASA')
        print('2. Search against a file')
        answer = input('Type 1 or 2> ')
        if answer == '1':
            against_asa = True
            test_login()    # Test log into ASA
            break
        elif answer == '2':
            against_asa = False
            gather_info()
            break
        else:
            print('\n!!! ERROR - Response not understood, please try again\n')

# 2. Gets username/password and checks connectivity
def test_login():
    global net_conn             # Make connection variable global so can be used in all functions

    while True:
        try:
            device = input("Enter IP of the ASA firewall: ")
            username = input("Enter your username: ")
            password = getpass()
            net_conn = Netmiko(host=device, username=username, password=password, device_type='cisco_asa')
            net_conn.find_prompt()      # Expects to recieve prompt back from access switch
            break
        except Exception as e:              # If login fails loops to begining with the error message
            print(e)

    gather_info()                   # Runs next function

# 3. Gets the IPs to searched in ACLs, file name and collects data from the ASA
def gather_info():
    global filename
    # Prompts user to enter the IPs to be searched and makes a list of them.
    print("\nEnter the IPs you want to search for in the ACLs seperated by a space.")
    print("Leave blank if you want to search all IPs.")
    ips_entered = input('> ')
    search_ips = []
    if len(ips_entered) != 0:
        search_ips = ips_entered.split(' ')

    # Prompts user to enter the ACLs to be searched and makes a list of them.
    print("\nEnter the names of the ACLs you want to search in followed by space.")
    print("Leave blank if you want to search all ACLs: ")
    acls_entered = input('> ')
    acl_names = []
    if len(acls_entered) != 0:
        acl_names = acls_entered.split(' ')

    # Prompts user to enter the name of the file to be created. It it already exists prompts user to confirm they want to overwrite.
    while True:
        print("\nEnter the name of the file to save the results to.")
        filename = input('> ')
        filename = os.path.join(directory, filename + ".csv")
        if os.path.exists(filename):
            print("The filename already exists, do you want to overwrite this?")
            print("Type y if this is correct, or n to re-enter the file name.")
            answer = input('> ')
            if answer == 'y':
                break
        else:
            break
    # Run next function
    verify(search_ips, acl_names)

################################## Validates information and gets ACLs from ASA or file ##################################
# 4. Verifies that the entered details is of a valid format
def verify(search_ips, acl_names):
    ip_error = []
    acl_error = []

    # Checks to make sure that the IP address are valid, if not exits the script
    if len(search_ips) != 0:
        for ip in search_ips:
            # Checks if IPs are valid, gathers list of non-valid IPs
            try:
                ipaddress.ip_address(ip)
            except ValueError as errorCode:
                ip_error.append(str(errorCode))
    # Runs if there was an ip address error (list not empty)
    if len(ip_error) != 0:
        print("!!!ERROR - Invalid IP addresses entered !!!")
        for x in ip_error:
            print(x)
        exit()

    # ASA - Checks to make sure that the ACL names are on the ASA, if not exits the script
    if against_asa is True:
        if len(acl_names) != 0:
            asa_acls = []
            acl = net_conn.send_command('show run access-group')
            vpn_acl = net_conn.send_command('show run | in split-tunnel-network-list')
            # Gathers list of access-group ACLs and group policy ACLs
            for x in acl.splitlines():
                asa_acls.append(x.split(' ')[1])
            for x in vpn_acl.splitlines():
                asa_acls.append(x.split('value')[1])
            # Converts to a set to remove duplicates, then finds any element from acl_names not in acls
            acl_error = list(set(acl_names) - set(asa_acls))
            # Runs if there was an acl name error (list not empty)
            if len(acl_error) != 0:
                print("!!!ERROR - Invalid ACL names entered !!!")
                for x in acl_error:
                    print("'{}' does not appear to be an ACL on the ASA".format(x))
                exit()
        # Run next function
        get_acl(search_ips, acl_names)

   # FILE - Prompts user to enter the name of the file to be loaded. If cant find it prompts user to re-enter
    elif against_asa is False:
        while True:
            print("\nEnter the full filename (including extension) of the file containing the ACLs. It must already be in your home directory.")
            filename = input('> ')
            filename = os.path.join(directory, filename)
            if os.path.exists(filename):
                with open(filename) as var:
                    acl1 = var.read().splitlines()
                # Cleans up ACL output so is same standard as ASA output.
                for x in list(acl1):
                    if ('show' in x) or ('#' in x) or ('elements' in x) or ('cached' in x) or ('alert-interval' in x) or ('remark' in x) or (len(x) == 0):
                        acl1.remove(x)
                # Creates just a list of ACL names to comapre againt user entered ACL names
                file_acls = []
                for x in acl1:
                    y = x.lstrip()
                    y = y.split(' ')
                    file_acls.append(y[1])
                # Converts to a set to remove duplicates, then finds any element from acl_names not in acls
                acl_error = list(set(acl_names) - set(file_acls))
                # Runs if there was an acl name error (list not empty)
                if len(acl_error) != 0:
                    print("!!!ERROR - Invalid ACL names entered !!!")
                    for x in acl_error:
                        print("'{}' does not appear to be an ACL in the file".format(x))
                        exit()
                else:
                    filter_acl(search_ips, acl_names, acl1)       # runs next function
                    break
            else:
                print('!!! ERROR - Cant find the file, was looking for {}'.format(filename))
                print('Make sure it is in home directory and named correctly before trying again.')

# 5a. Connects to the ASA and gathers the ACLs
def get_acl(search_ips, acl_names):
    acl = ''
    # To get all ACL entries from all ACLs
    if len(search_ips) == 0 and len(acl_names) == 0:
        acl = net_conn.send_command('show access-list | ex elements|cached|alert-interval|remark')
    # To get all ACL entries from specific ACLs
    elif len(search_ips) == 0 and len(acl_names) != 0:
        for x in acl_names:
            acl = acl + net_conn.send_command('show access-list {}'.format(x))
    # To get certain ACL entries from all acls
    elif len(search_ips) != 0 and len(acl_names) == 0:
        search_ips = '|'.join(search_ips)
        acl = net_conn.send_command('show access-list | in {}'.format(search_ips))
    # To get certain ACL entries from specificacls
    elif len(search_ips) != 0 and len(acl_names) != 0:
        search_ips = '|'.join(search_ips)
        for x in acl_names:
            acl = acl + net_conn.send_command('show access-list {} | in {}'.format(x, search_ips))
    # Disconnect from ASA and run next function
    net_conn.disconnect()
    format_data(search_ips, acl_names, acl)

# 5b. Searches through the file to filter only specified IPs and/or ACLs
def filter_acl(search_ips, acl_names, acl1):
    if (len(acl_names) != 0) and (len(search_ips) != 0):
        acl2 = []
        for x in acl_names:
            for y in acl1:
                if x in y:
                    acl2.append(y)
        acl = []
        for x in search_ips:
            for y in acl2:
                if x in y:
                    acl.append(y)
    elif len(acl_names) != 0:
        acl = []
        for x in acl_names:
            for y in acl1:
                if x in y:
                    acl.append(y)
    elif len(search_ips) != 0:
        acl = []
        for x in search_ips:
            for y in acl1:
                if x in y:
                    acl.append(y)
    # Converts the ACL file back from a list into a string and runs next function
    acl = '\n'.join(acl)
    format_data(search_ips, acl_names, acl)

################################## Sanitize the data ##################################
def format_data(search_ips, acl_names, acl):
    # 4. Pad out any and remove hitcnt text by replacing fields, all dont whilst file is one big string
    acl = acl.replace('any4', 'any')    # Incase any4 acls used for packet captures
    acl = acl.replace('any', 'any any1')
    for elem in ['(hitcnt=', ')']:
        acl = acl.replace(elem, '')

    # 5. Clean up ACL by removing remarks and informational data
    acl = acl.splitlines()
    for x in list(acl):
        if ('elements' in x) or ('cached' in x) or ('alert-interval' in x) or ('remark' in x) or (len(x) == 0):
            acl.remove(x)
    # 6. Remove unneeded fields, lines with object-group in and logging
    acl1 = []
    for x in acl:
        if 'object-group' not in x:     # Remove all lines with object-group
            y = x.strip()               # Removes all starting and trailing whitespaces
            y = y.split(' ')
            for z in [0, 1, 2]:         # Deletes access-list, line and extended
                del y[z]
            if 'log' in y:              # If ACL is logging removes log and 3 fields after (log notifications interval 300)
                del y[-6:-2]
            acl1.append(y[:-1])         # Removes ACL hash from the end of the output

    # 7. Now got only data we need normalise source ports by joining range, removing eq and padding out if is no source port.
    acl2 = []
    for b in acl1:
        if b[6] == 'range':             # If has a source range of ports replace "range" with "start-end" port numbers
            c = b.pop(7)
            d = b.pop(7)
            b[6] = c + '-' + d
        elif b[6] == 'eq':              # If has a single source port delete eq
            del b[6]
        elif 'icmp' not in b:           # If it is not ICMP and has no source port padout with any_port
            (b.insert(6, 'any_port'))
        else:
            if ('.' in b[6]) or (b[6] == 'any'):        # If ICMP has no port padout with any_port
                (b.insert(6, 'any_port'))
        acl2.append(b)
    # 8. Normalise destination ports by joining range, removing eq and padding out if no source port.
    acl3 = []
    for b in acl2:
        if 'range' in b:
            c = b.pop(-3)
            d = b.pop(-2)
            b[-2] = c + '-' + d
        elif 'eq' in b:
            del b[-3]
        elif 'icmp' not in b:
            (b.insert(-1, 'any_port'))
        else:
            if ('.' in b[-2]) or (b[-2] == 'any1'):
                (b.insert(-1, 'any_port'))
        acl3.append(b)

    # 9. For all host entries delete host and add /32 subnet mask after the IP
    acl4 = []
    for x in acl3:
        if x[4] == 'host':
            del x[4]
            (x.insert(5, '255.255.255.255'))
        if x[7] == 'host':
            del x[7]
            (x.insert(8, '255.255.255.255'))
        acl4.append(x)
    # 10. Convert subnet mask to prefix and pad out old mask filed with 'any1'
    for x in acl4:
        if x[4] != 'any':
            y = IPv4Network((x[4], x[5])).with_prefixlen
            x[4] = y
            x[5] = 'any1'
        if x[7] != 'any':
            y = IPv4Network((x[7], x[8])).with_prefixlen
            x[7] = y
            x[8] = 'any1'
        del x[5]        # Delete the 'any1' padding that was used
        del x[7]
    # 11. Create CSV from the output
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(csv_columns)
        for data in acl4:
            writer.writerow(data)
    print()
    print('File {} has been created'.format(filename))

# Starts the script
start()

################################## Run or test elements of script ##################################

#filename = 'acl_name1.csv'
#search_ips = []
#acl_names = []
#search_ips = ['10.10.10.81', '10.10.10.3']
#acl_names = ['media', 'data']
#with open('acl.txt') as var:
#    acl = var.read()

#against_asa = True
#gather_info()
#verify(search_ips, acl_names)
#get_acl(search_ips, acl_names)
#format_data(search_ips, acl_names, acl)