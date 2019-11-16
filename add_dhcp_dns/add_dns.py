############ DNS checking ###############
# 3. Check that the domain names dont already have a A record
# 4. Check that the addresses dont already have a PTR record

#def check_dns:



# import socket

#     def gather_pre_check(self):
#         core_ip = False             # Used to keep the loop going till core_ip has a value
#         while core_ip == False:
#             try:        # If dns doesnt return a name this stops error killing program
#                 access_name = input("\nWhat is the name of the device to be upgraded or rebooted? ")
#                 access_ip = socket.gethostbyname(access_name)   # DNS lookup to get the IP of the device
#                 access_name = access_name.upper()               # Converts all characters to uppercase

#Is already a module for DNS:
#https://docs.ansible.com/ansible/latest/modules/win_dns_record_module.html#win-dns-record-module

#But not for DHCP. Could try and write but has to be in powershell
#https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general_windows.html#developing-modules-general-windows

socket.gethostbyname('access_name')
socket.gethostbyaddr('192.30.252.130')

socket.gethostbyname(name1)
socket.gethostbyaddr(ip1)

In [6]: socket.gethostbyname(name1)
Out[6]: '10.10.10.11'

In [7]: socket.gethostbyaddr(ip1)
Out[7]: ('ap1.stesworld.com', ['11.10.10.10.in-addr.arpa'], ['10.10.10.11'])

In [8]: socket.gethostbyaddr(ip2)
[Errno 1] Unknown host

In [9]: socket.gethostbyaddr(name2)
[Errno 8] nodename nor servname provided, or not known

IS a module for Ansible for this
https://docs.ansible.com/ansible/latest/modules/win_dns_record_module.html#win-dns-record-module