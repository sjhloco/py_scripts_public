############ DHCP checking ###############
# 5. Check that none of the IP addresses are pingable

#def check_dhcp

#    # Check IPs assigned by IPAM not used, 0 means used 2 means not used. subprocesss to stop displaying on screen
#         for ip_addr in self.vip_ip_snat:
#             if WINDOWS == False:
#                 return_code = subprocess.call(['ping', '-q', '-c', '3', ip_addr], stdout=subprocess.DEVNULL)
#                 if return_code == 0:
#                     self.ip_not_used = "Assigned IP address {} is already in use.".format(ip_addr),
#                     "\nPlease investigate this and run the script again."
#                 else:
#                     self.ip_not_used = True
#             elif WINDOWS == True:
#                 return_code = subprocess.call(['ping', '-n', '3', ip_addr], stdout=subprocess.DEVNULL)
#                 if return_code == 0:
#                     self.ip_not_used = "Assigned IP address {} is already in use.".format(ip_addr),
#                     "\nPlease investigate this and run the script again."
#                 else:
#                     self.ip_not_used = True
