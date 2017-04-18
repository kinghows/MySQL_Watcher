#!/bin/sh

report_base=/opt/mysql/mysql_watcher
datetime=`date +%Y-%m-%d_%H-%M-%S`

python $report_base/mysql_watcher.py -p $report_base/dbset101.ini >$report_base/mysql_watcher_101_$datetime.txt
python $report_base/mysql_watcher.py -p $report_base/dbset102.ini >$report_base/mysql_watcher_102_$datetime.txt
