# MySQL_Watcher
MySQL Watcher is a tool to help DBA's to trouble shoot MySQL performance.

pip install psutil

pip install prettytable

2.7：

pip install mysql-python

3.x:

pip install mysqlclient

Some options must be executed on the host,not remote.

The MySQL sys schema support now.

https://github.com/mysql/mysql-sys

Some sys view is off by default, you can set in the dbset.ini.

example:

![txt example](https://github.com/kinghows/MySQL_Watcher/blob/master/txt.jpg)
![html example](https://github.com/kinghows/MySQL_Watcher/blob/master/html.jpg)

Edit MySQL connect info in dbset.ini.

execute:

2.7:

python mysql_watcher.py

python mysql_watcher.py -p dbset.ini

python mysql_watcher.py -p dbset.ini -s txt >mysql_watcher.txt

python mysql_watcher.py -p dbset.ini -s html >mysql_watcher.html

send email:

python SendEmail.py -p emailset.ini -f my_report1.html,my_report2.html

3.x:

python3 mysql_watcher3.py

python3 mysql_watcher3.py -p dbset.ini

python3 mysql_watcher3.py -p dbset.ini -s txt >mysql_watcher.txt

python3 mysql_watcher3.py -p dbset.ini -s html >mysql_watcher.html

send email:

python3 SendEmail3.py -p emailset.ini -f my_report1.html,my_report2.html

use crontab regularly perform sql_report.sh,auto generate  report,and send email.

Enjoy it! 
