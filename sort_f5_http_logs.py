# Used to simplify the output got from F5 logs for failed HTTP code - Is a bit crude, needs improvement
# Log file input was that grepped from F5 with just 8080 VIPs

import re
from sys import argv
import csv

# Enables being able to name Source log file when running the script
script, ltm_log = argv

# Build the CSV file With the headers Values
HEADERS = ['Date', 'F5', 'VIP', 'Server', 'TCP_Mon', 'Monitor_Name', 'Response Code1', 'Response Code2', 'Response Code3', 'Response Code4']

with open("output.csv", 'w') as resultFile:
    wr = csv.writer(resultFile, dialect='excel')
    wr.writerow(HEADERS)

# Open the source logfile and save to a variable
with open(ltm_log) as var:
    ltm_log = var.read()

# To split the logs for only 8080_Pool when server failed and when it recovered
ltm_log1 = []
ltm_log_recover = []
match_down = re.compile(r'8080_Pool member.*was up for')
match_up = re.compile(r'8080_Pool member.*was down for')
for x in ltm_log.splitlines():
    if match_down.search(x):
        ltm_log1.append(x)
    elif match_up.search(x):
        ltm_log_recover.append(x)

log_info = []
for x in ltm_log1:
    # Regex each line putting following data into each group
    # (1)Date, (2)name, (3)pool_name, (4)server_name, (5)tcp_state, (6)monitors
    regex1 = re.match(r'(^.*) (D\S*) .*puting/(.*)_8080.*(srv.*):8080.*tcp: (\S*),.*error: (.*)]', x)
    # Write first 5 groups to files
    log_info = list(regex1.group(1, 2, 3, 4, 5))
    # Loop over group 6 which is failed monitors as the number that failed could change
    for y in regex1.group(6).split('/End_User_Computing/HTTP_Transparent_GET_')[1:]:
        # Regex each line to get name and responce codes.
        # (1)name (2)Error msg
        regex2 = re.match(r'(^.*)_srv.*8081:(.*)', y)
        # Create list containing monitor name
        monitor = [regex2.group(1)]
        # Split monitors at each response code
        for z in regex2.group(2).split('Response Code:'):
            monitor.append(z)
            name = [monitor[0]]
            # Join llog info to each monitor, and all responce codes to the monitor
            ltm_log_fail = log_info + name + monitor[2:]
        # Pop last list element so can remove time from it
        c = ltm_log_fail.pop(-1)
        # Loop through and add last reponce back but now a list so can remove time
        for x in c.split('@'):
            ltm_log_fail.append(x)
        # print(ltm_log_fail[:-1])
        # Write reults to CSV file. No need to loop, writerow automatically does for you
        with open("output.csv", 'a') as resultFile:
            wr = csv.writer(resultFile, dialect='excel')
            wr.writerow(ltm_log_fail[:-1])      # -1 removes the time