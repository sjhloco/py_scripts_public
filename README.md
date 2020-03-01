# Python Scripts

Contains python scripts created for small tasks

1. render_jinja.py<br />
-Used to render YAML file with Jinja tetmplate for testing expressions used in Ansible<br />

2. sort_f5_http_logs.py<br />
-Used to troubleshoot F5 HTTP health monitor logs by sorting into CSV file. Is not very flexable, for a specific VIP<br />

3. update_exchange_prefixes.py<br />
-Pulls down Exchange online prefixes, compares against existing groups on ASA and checkpoint firewalls and updates them if necessary. Basic in that designed to only do for a specific number devices and subset of exchange addresses. <br />
