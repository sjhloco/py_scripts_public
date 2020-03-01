#!/usr/bin/env python

from ipaddress import ip_network
from getpass import getpass
from netmiko import Netmiko
import json
import requests
import sys
from pprint import pprint
from os.path import expanduser
import os


######################## Variables to change dependant on environment ########################
# Where script will look for saved file and the filename. By default is the users home directory
directory = expanduser("~")
filename = "ms_exchange_pfx.txt"

# Where the Microsoft updated prefixes are pulled from
getURL = f"https://endpoints.office.com/endpoints/worldwide?ServiceAreas=Exchange&clientrequestid=a0b4eb9c-2aa9-4041-b039-938ffd1a4fd6"

# FIrewalls that will ahve the groups checked and possibly updated
dc1_asa = '10.10.10.1'
dc2_asa = '10.10.10.1'
ckp_url = 'https://10.10.10.1/web_api/'

###################################### 1. Get pfxs from Microsoft ######################################
def get_ms_pfxs():
    ms_ex_online, ms_ex_protect = ([] for i in range(2))
    req = requests.get(getURL)
    # If does not return error runs next module
    if req.status_code == 200:
        output = req.json()         # grab output in JSON format

        # Gets a list of IPv4 addresses from Exchange online prefixes
        for x in output:
            if x['urls'][0] == 'outlook.office.com' and  x['urls'][1] == 'outlook.office365.com':
                ms_ex_online1 = [ip for ip in x['ips'] if '.' in ip]
                # Changes the prefix into a subnet mask
                for x in ms_ex_online1:
                    ms_ex_online.append(ip_network(x).with_netmask.replace('/', ' '))

        # Gets a list of IPv4 addresses from Exchange protection prefixes
        for x in output:
            if x['urls'][0] == '*.protection.outlook.com':
                ms_ex_protect1 = [ip for ip in x['ips'] if '.' in ip]
                # Changes the prefix into a subnet mask
                for x in ms_ex_protect1:
                    ms_ex_protect.append(ip_network(x).with_netmask.replace('/', ' '))
    # if error exits script
    else:
        print('!!!ERROR - Check {} is valid as returned a status code of {}!!!'.format(getURL,req.status_code))
        exit()
    return [ms_ex_online, ms_ex_protect]


###################################### 3. Compare and returns user info ######################################
def compare_pfxs(ms_pfxs, asa_pfxs):
    # Find any prefixes to be added to the object-groups
    ex_online_add = set(ms_pfxs[0]) - set(asa_pfxs[0])
    ex_protect_add = set(ms_pfxs[1]) - set(asa_pfxs[1])
    # Find any prefixes to be removed from the object-groups
    ex_online_rmv = set(asa_pfxs[0]) - set(ms_pfxs[0])
    ex_protect_rmv = set(asa_pfxs[1]) - set(ms_pfxs[1])





    # Creates a file containing MS prefixes as well as ASA object groups
    file = os.path.join(directory, filename)
    with open(file, 'w+') as open_file:
        open_file.write('=== Microsoft outlook.office.com and outlook.office365.com Prefixes ===\n')
        open_file.writelines(list("%s\n" % item for item in ms_pfxs[0]))
        open_file.write('\n=== ASA object-group Exchange-online-v1 ===\n')
        open_file.writelines(list("%s\n" % item for item in asa_pfxs[0]))
        open_file.write('\n=== Microsoft *.protection.outlook.com Prefixes ===\n')
        open_file.writelines(list("%s\n" % item for item in ms_pfxs[1]))
        open_file.write('\n=== ASA object-group Exchange-online-protection-v1 ===\n')
        open_file.writelines(list("%s\n" % item for item in asa_pfxs[1]))
        open_file.write('\n' + '=' * 80)

    # If are no changes in prefixes exits script
    if len(ex_online_add) == 0 and len(ex_online_rmv) == 0 and len(ex_protect_add) == 0 and len(ex_protect_add) == 0:
        print("\nAll prefixes are upto date, no changes needed.")
        print("The file '{}' has been created, attach this to the SR and close it.\n".format(file))
        exit(0)
    # Informs user of any changes between current ASA and MS prefixes
    else:
        print('The following changes need to be made to Exchange-online-v1 on the ASAs and CKP:')
        if len(ex_online_add) == 0:
            print('Add: None')
        else:
            print('Add: '), pprint(ex_online_add)
        if len(ex_online_rmv) == 0:
            print('Remove: None')
        else:
            print('Remove: '), pprint(ex_online_rmv)
        print('\nThe following changes need to be made to Exchange-online-Protection-v1 on the ASAs:')
        if len(ex_protect_add) == 0:
            print('Add: None')
        else:
            print('Add: '), pprint(ex_protect_add)
        if len(ex_protect_rmv) == 0:
            print('Remove: None')
        else:
            print('Remove: '), pprint(ex_protect_rmv)

    # Either runs the apply_changes function or exits
        print("\nDo you want the script to make these changes automatically?")
        check = input("y or n: ").lower()
        while True:
            if check == 'y':
                return [ex_online_add, ex_online_rmv, ex_protect_add, ex_protect_rmv]
            elif check == 'n':
                print("You must log into the ASA and/or CKP and make these changes manually.")
                print("{} has been created, attach to the ticket once the changes completed.".format(file))
                exit(0)
            else:
                check = input("Not recognised, please try again:")


###################################### 3. Compare and returns user info ######################################

def apply_changes(asa_user, asa_pass, changes):
    global asa_config
    asa_config = ['object-group network Exchange-online-v1']
    # If ex_online_add or ex_online_rmv are not empty (exchange online objects need updating)
    if len(changes[0]) != 0 or len(changes[1]) != 0:
        if len(changes[0]) != 0:
            for x in changes[0]:
                asa_config.append('network-object ' + x)
        if len(changes[1]) != 0:
            for x in changes[1]:
                asa_config.append('no network-object ' + x)

    # If x_protect_add or ex_protect_add are not empty (exchange protection objects need updating)
    if len(changes[2]) != 0 or len(changes[3]) != 0:
        asa_config.extend(['exit', 'object-group network Exchange-online-protection-v1'])
        if len(changes[2]) != 0:
            for x in changes[2]:
                asa_config.append('network-object ' + x)
        if len(changes[3]) != 0:
            for x in changes[3]:
                asa_config.append('no network-object ' + x)

    asa = Asa(asa_user, asa_pass)
    output = asa.post_asa_pfxs()

    file = os.path.join(directory, filename)
    with open(file, 'a') as open_file:
        open_file.write('\n\n=== ASA configuration Before ===\n{}'.format(output[0]))
        open_file.write('\n\n=== ASA configuration After  ===\n{}'.format(output[1]))
        open_file.write('\n\n=== ASA configuration Logging  ===\n')
        open_file.writelines(list("%s\n" % item for item in output[2]))
        open_file.write('\n\n' + '=' * 80)

    print("\nAll the configuration has been applied successfully.")
    print("Verify the details in the file '{}', attach it to the SR and close it.\n".format(file))
    exit()

###################################### 2a. Interaction with ASA ######################################
class Asa():
    def __init__(self, asa_user, asa_pass):
        self.asa_user = asa_user
        self.asa_pass = asa_pass
        self.net_conn = Netmiko(host=dc1_asa, username=asa_user, password=asa_pass, device_type='cisco_asa')

    def get_asa_pfxs(self):
        asa_ex_online, asa_ex_protect = ([] for i in range(2))
        # Gathers the object-groups for exchange-online and protection from the ASA
        asa_ex_online1 = self.net_conn.send_command('show run object-group id Exchange-online-v1')
        asa_ex_protect1 = self.net_conn.send_command('show run object-group id Exchange-online-protection-v1')
        self.net_conn.disconnect()

        # Strip so just have network and subnet mask
        for x in asa_ex_online1.splitlines():
            if 'network-object' in x:
                asa_ex_online.append((x.replace(' network-object ', '')))
        for x in asa_ex_protect1.splitlines():
            if 'network-object' in x:
                asa_ex_protect.append((x.replace(' network-object ', '')))
        # Swap any host entries for 255.255.255.255
        for x in asa_ex_online:
            if 'host' in x:
                asa_ex_online.remove(x)
                asa_ex_online.append(x.split('host ')[1] + ' 255.255.255.255')
        for x in asa_ex_protect:
            if 'host' in x:
                asa_ex_protect.remove(x)
                asa_ex_protect.append(x.split('host ')[1] + ' 255.255.255.255')
        return [asa_ex_online, asa_ex_protect]

    # Applies the configuration to the ASAs
    def post_asa_pfxs(self):
        print("Applying configuration on {}, please wait...".format(dc1_asa))
        show_cmds = ['show run object-group id Exchange-online-v1', 'show run object-group id Exchange-online-protection-v1']
        asa_log = []
        asa_before = self.net_conn.send_config_set(show_cmds)
        asa_log.append(self.net_conn.send_config_set(asa_config))
        asa_log.append(self.net_conn.save_config())
        asa_after = self.net_conn.send_config_set(show_cmds)
        self.net_conn.disconnect()
        return [asa_before[13:-33], asa_after[13:-33], asa_log]


###################################### 2b. Interaction with Checkpoint ######################################

# class Ckp():
#     def __init__(self, ckp_user, ckp_pass):     ### WILL HAVE MORE DATA INPUT
#         self.ckp_user = ckp_user
#         self.ckp_pass = ckp_pass
#         # alternative to login method need to test where once class insatised get sid to then use when running cmds
#         # payload = {'user':ckp_user, 'password' : ckp_pass}
#         # response = api_call(ckp_url, 'login', payload, '', 'GET')
#         # self.sid = response["sid"]

#     # Engine that runs any cmds fed into it on checkpoint
#     def api_call(self, ckp_url, command, json_payload, sid, method):
#         url = ckp_url + command
#         # If is the first time logging in creates a session ID which can be used rather than credentials fo future API calls
#         if sid == '':
#             request_headers = {'Content-Type' : 'application/json'}
#         else:   # SID used if not first tiem logging in
#             request_headers = {'Content-Type' : 'application/json', 'X-chkp-sid' : sid}

#         # Runs the API call using either get (show cmds) or post (enter config)
#         if method == 'get':
#             r = requests.get(url,data=json.dumps(json_payload), headers=request_headers)
#         elif method == 'post':
#             r = requests.post(url,data=json.dumps(json_payload), headers=request_headers)
#         return r.json()

#     def login(self):
#         payload = {'user':self.ckp_user, 'password': self.ckp_pass}
#         response = api_call(ckp_url, 'login', payload, '', 'GET')
#         return response["sid"]

#     # Gathers sid for each request
#     sid = login()
#     def get_data(self):
#         ckp_ex_online = api_call(ckp_url, 'show-group', show_data, sid, 'GET')
#         print(json.dumps(ckp_ex_online))
#         logout = api_call(ckp_url, "logout", {},sid)
#         print("logout result: " + json.dumps(logout))

#     def change_data(self):
#         add_net = api_call(ckp_url, 'add-network', add_data, sid, 'POST')
#         print(json.dumps(add_net))
#         change_grp = api_call(ckp_url, 'set-group', set_data, sid, 'POST')
#         print(json.dumps(change_grp))
#         del_net = api_call(ckp_url, 'delete-network', del_data, sid, 'POST')
#         print(json.dumps(del_net))
#         publish = api_call(ckp_url, "publish", {},sid)
#         print("publish result: " + json.dumps(publish))
#         logout = api_call(ckp_url, "logout", {},sid)
#         print("logout result: " + json.dumps(logout))

###################################### Run the scripts ######################################
# 1. Starts the script taking input of CSV file name

def main():
    # 1. Gathers published prefixes from Microsoft
    ms_pfxs = get_ms_pfxs()
    # 2. Gathers info from ASA about existing group members
    # asa_user = input("Enter asa username: ")
    # asa_pass = getpass("Enter asa password: ")
    asa_user = 'ste'
    asa_pass = 'p1aya.gir0n'
    asa = Asa(asa_user, asa_pass)
    asa_pfxs = asa.get_asa_pfxs()

    # ckp_user = input("Enter checkpoint username: ")
    # ckp_pass = getpass("Enter checkpoint password: ")
    # ckp = Ckp(ckp_user, ckp_pass)
    # ckp_pfxs = ckp.get_ckp_pfxs()

    # 3. Compare existing Vs new prefixes
    changes = compare_pfxs(ms_pfxs, asa_pfxs)
    # 4. Update the prefixes on the firewalls
    apply_changes(asa_user, asa_pass, changes)

if __name__ == '__main__':
    main()


# Todo
# Add extra checks for DC2-ASA and Checkpoint. Compare these outputs, if are different exit script - User has to make them the same!!!
# Add DC2-ASA config into apply_changes section
# Add CKP config into apply_changes section
# Ways to DRY and make more stremalined, some examples are when writing to file






# CREDS


# SHOW CMDS
# show_input = {'name':'Exchange-online-v1'}
# May also need to use 'details-level': 'full' and/or "show-as-ranges" : "true"

# CHANGE cmds
# add_data = {'name':'new_network', "subnet" : "192.0.2.0", "subnet-mask" : "255.255.255.0"}
# set_data = {'name':'Exchange-online-v1', "members" : {"add" : "member1"}}
# set_data = {'name':'Exchange-online-v1', "members" : {"add" : ["member1", "member2"]}}
# set_data = {'name':'Exchange-online-v1', "members" : {"add" : "member1"}, "members" : {"remove" : "member2"}}
# del_data = {'name':'new_network'}

# https://sc1.checkpoint.com/documents/latest/APIs/#web/delete-network~v1.6