#!/bin/sh
report_base=/services/script
datetime=`date +%Y-%m-%d_%H-%M`
python $report_base/mysql_watcher.py -p $report_base/dbset101.ini  -s html>$report_base/mysql_watcher101_$datetime.html
python $report_base/mysql_watcher.py -p $report_base/dbset102.ini  -s html>$report_base/mysql_watcher102_$datetime.html
python $report_base/SendEmail.py -p $report_base/emailset101.ini -f $report_base/mysql_watcher101_$datetime.html,$report_base/mysql_watcher102_$datetime.html
