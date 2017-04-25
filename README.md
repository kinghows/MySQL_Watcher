# MySQL_Watcher
MySQL Watcher is a tool to help DBA's to trouble shoot MySQL performance.

Test in Python-2.7+MySQL5.7,need install mysql-python.

Linux overview just run in linux server local,not remote ,and must install psutil.

example:

![txt example](https://github.com/kinghows/MySQL_Watcher/blob/master/txt.jpg)
![html example](https://github.com/kinghows/MySQL_Watcher/blob/master/html.jpg)

Edit MySQL connect info in dbset.ini.

run:

python mysql_watcher.py -p dbset.ini

python mysql_watcher.py -p dbset.ini -s txt >mysql_report.txt

python mysql_watcher.py -p dbset.ini -s html >mysql_report.html

use crontab regularly perform mysql_watcher.sh

Enjoy it! 
