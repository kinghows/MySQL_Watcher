# MySQL_Watcher
MySQL Watcher is a tool to help DBA's to trouble shoot MySQL performance.

Test in Python-2.7,need install mysql-python.

Edit MySQL connect info in dbset.ini.

run:
python mysql_watcher.py -p dbset.ini
or
python mysql_watcher.py -p dbset.ini >mysql_report.txt
or
use crontab regularly perform mysql_watcher.sh

Enjoy it! 
