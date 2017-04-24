# MySQL_Watcher
MySQL Watcher is a tool to help DBA's to trouble shoot MySQL performance.

Test in Python-2.7+MySQL5.7,need install mysql-python.
Linux overview just run in linux server local,not remote ,and must install psutil.

example:
=========================================== Linux Overview ============================================
  CPU            1.0%   nice           1.25   MEM       60.3%   active      2225M   SWAP       0.7%   LOAD     1core  
  user        2545.52   irq           39.76   total     3830M   inactive    1310M   total     2047M   1 min     0.31  
  system      1780.85   iowait     37215.76   used      2112M   buffers      167M   used        13M   5 min     0.16  
  idle      388261.96   steal        174.65   free       158M   cached      1391M   free      2034M   15 min     0.1  
========================================== Database Overview ===========================================
+ ---------------------------------------- + -------------------- + -------------------- +
|                   Key                    |        In 60s        |        Total         |
+ ---------------------------------------- + -------------------- + -------------------- +
| Uptimes                                  |                  60s |             5d19m53s |
| QPS (Questions / Seconds)                |                10.07 |                 9.96 |
| TPS ((Commit + Rollback)/ Seconds)       |                  1.8 |                 1.55 |
| Reads per second                         |                  3.2 |                 3.09 |
| Writes per second                        |                 2.72 |                  3.3 |
| Read/Writes                              |                 1.18 |                 0.94 |
| Slow queries per second                  |                 0.17 |                 0.17 |
| Slow_queries/Questions                   |                1.66% |                1.67% |
| Threads connected                        |                    0 |                   64 |
| Aborted connects                         |                    0 |                    4 |
| Thread cache hits (>90%)                 |               100.0% |               99.31% |
| Innodb buffer hits(96% - 99%)            |               100.0% |               100.0% |
| Innodb buffer pool utilization           |               40.48% |               40.48% |
| Key buffer read hits(99.3% - 99.9%)      |                 0.0% |               99.31% |
| Key buffer write hits(99.3% - 99.9%)     |                 0.0% |                 0.0% |
| Query Cache Hits                         |                 0.0% |                 0.0% |
| Select full join per second              |                 0.05 |                 0.06 |
| full select in all select                |                1.56% |                1.78% |
| full table scans                         |               24.07% |               20.64% |
| MyISAM Lock waiting ratio                |                 0.0% |                 0.0% |
| Current open tables                      |                    0 |                  576 |
| Accumulative open tables                 |                    0 |                55972 |
| Temp tables to disk(<10%)                |               86.36% |               32.77% |
+ ---------------------------------------- + -------------------- + -------------------- +

Edit MySQL connect info in dbset.ini.

run:
python mysql_watcher.py -p dbset.ini
or
python mysql_watcher.py -p dbset.ini >mysql_report.txt
or
use crontab regularly perform mysql_watcher.sh

Enjoy it! 
