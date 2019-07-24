#!/usr/local/bin/python
# coding: utf-8

# MySQL Watcher V1.3.0 for python3
# trouble shoot MySQL performance
# Copyright (C) 2017-2017 Kinghow - Kinghow@hotmail.com
# Git repository available at https://github.com/kinghows/MySQL_Watcher

import getopt
import sys
import MySQLdb
import configparser
import math
import time
import os
import prettytable
import psutil
import platform
import glob
import re
from collections import OrderedDict
from collections import namedtuple
from warnings import filterwarnings

filterwarnings('ignore', category = MySQLdb.Warning)

tab1="="
tab2="*"
linesize=104

SYS_PARM_FILTER = (
    'autocommit',
    'binlog_cache_size',
    'bulk_insert_buffer_size',
    'character_set_server',
    'tx_isolation',
    'tx_read_only',
    'sql_mode',
# connection #
    'interactive_timeout',
    'wait_timeout',
    'lock_wait_timeout',
    'skip_name_resolve',
    'max_connections',
    'max_connect_errors',
# table cache performance settings
    'table_open_cache',
    'table_definition_cache',
    'table_open_cache_instances',
# performance settings
    'have_query_cache',
    'join_buffer_size',
    'key_buffer_size',
    'key_cache_age_threshold',
    'key_cache_block_size',
    'key_cache_division_limit',
    'large_pages',
    'locked_in_memory',
    'long_query_time',
    'max_allowed_packet',
    'max_binlog_size',
    'max_length_for_sort_data',
    'max_sort_length',
    'max_tmp_tables',
    'max_user_connections',
    'optimizer_prune_level',
    'optimizer_search_depth',
    'query_cache_size',
    'query_cache_type',
    'query_prealloc_size',
    'range_alloc_block_size',
# session memory settings #
    'read_buffer_size',
    'read_rnd_buffer_size',
    'sort_buffer_size',
    'tmp_table_size',
    'join_buffer_size',
    'thread_cache_size',
# log settings #
    'log_error',
    'slow_query_log',
    'slow_query_log_file',
    'log_queries_not_using_indexes',
    'log_slow_admin_statements',
    'log_slow_slave_statements',
    'log_throttle_queries_not_using_indexes',
    'expire_logs_days',
    'long_query_time',
    'min_examined_row_limit',
    'binlog-rows-query-log-events',
    'log-bin-trust-function-creators',
    'expire-logs-days',
    'log-slave-updates',
# innodb settings #
    'innodb_page_size',
    'innodb_buffer_pool_size',
    'innodb_buffer_pool_instances',
    'innodb_buffer_pool_chunk_size',
    'innodb_buffer_pool_load_at_startup',
    'innodb_buffer_pool_dump_at_shutdown',
    'innodb_lru_scan_depth',
    'innodb_lock_wait_timeout',
    'innodb_io_capacity',
    'innodb_io_capacity_max',
    'innodb_flush_method',
    'innodb_file_format',
    'innodb_file_format_max',
    'innodb_undo_logs',
    'innodb_undo_tablespaces',
    'innodb_flush_neighbors',
    'innodb_log_file_size',
    'innodb_log_files_in_group',
    'innodb_log_buffer_size',
    'innodb_purge_threads',
    'innodb_large_prefix',
    'innodb_thread_concurrency',
    'innodb_print_all_deadlocks',
    'innodb_strict_mode',
    'innodb_sort_buffer_size',
    'innodb_write_io_threads',
    'innodb_read_io_threads',
    'innodb_file_per_table',
    'innodb_stats_persistent_sample_pages',
    'innodb_autoinc_lock_mode',
    'innodb_online_alter_log_max_size',
    'innodb_open_files',
# replication settings #
    'master_info_repository',
    'relay_log_info_repository',
    'sync_binlog',
    'gtid_mode',
    'enforce_gtid_consistency',
    'log_slave_updates',
    'binlog_format',
    'binlog_rows_query_log_events',
    'relay_log',
    'relay_log_recovery',
    'slave_skip_errors',
    'slave-rows-search-algorithms',
# semi sync replication settings #
    'plugin_load',
    'rpl_semi_sync_master_enabled',
    'rpl_semi_sync_master_timeout',
    'rpl_semi_sync_slave_enabled',
# password plugin #
    'validate_password_policy',
    'validate-password',
# metalock performance settings
    'metadata_locks_hash_instances',
# new innodb settings #
    'loose_innodb_numa_interleave',
    'innodb_buffer_pool_dump_pct',
    'innodb_page_cleaners',
    'innodb_undo_log_truncate',
    'innodb_max_undo_log_size',
    'innodb_purge_rseg_truncate_frequency',
# new replication settings #
    'slave-parallel-type',
    'slave-parallel-workers',
    'slave_preserve_commit_order',
    'slave_transaction_retries',
# other change settings #
    'binlog_gtid_simple_recovery',
    'log_timestamps',
    'show_compatibility_56'
)

def f_get_conn(dbinfo):
    try:
        conn = MySQLdb.connect(host=dbinfo[0],user=dbinfo[1],passwd=dbinfo[2],db=dbinfo[3],port=int(dbinfo[4]))
        return conn
    except MySQLdb.Error as e:
        print ("Error %d: %s" % (e.args[0], e.args[1]))
        sys.exit(1)

def f_get_query_value(conn, query):
    cursor = conn.cursor()
    getNum = cursor.execute(query)
    if getNum > 0:
        result = cursor.fetchone()
    else:
        result = ['0']
    cursor.close()
    return result[0]

def f_get_query_record(conn, query):
    cursor = conn.cursor()
    cursor.execute(query)
    records = cursor.fetchall()
    cursor.close()
    return records

def f_print_title(title):
    print ()
    print (int((linesize-4)/2 - int(len(title)/2)) * tab1, title, int((linesize-4)/2+1 - int(len(title)/2)) * tab1)
    print ()

def f_print_table_body(rows, style,tab):
    for row in rows:
        k = 0
        for col in row:
            k += 1
            print (tab,end='')
            if style[k].split(',')[2] == 'l':
                print (str(col).ljust(int(style[k].split(',')[1])),end='')
            elif style[k].split(',')[2] == 'r':
                print (str(col).rjust(int(style[k].split(',')[1])),end='')
            else:
                print (str(col).center(int(style[k].split(',')[1])),end='')
        print (tab)

def f_print_table_txt(rows, title, style):
    field_names = []
    f_print_title(title)
    table = prettytable.PrettyTable()
    for k in style.keys():
        field_names.append(style[k].split(',')[0])
    table.field_names = field_names
    for k in style.keys():
        table.align[style[k].split(',')[0]] = style[k].split(',')[1]
    for row in rows:
        table.add_row(row)
    print (table)

def f_print_table_html(rows, title, style):
    print ("""<p /><h3 class="awr"><a class="awr" name="99999"></a>""" + title + "</h3><p />")
    print ("""<table border="1">""")

    print ("""<tr>""",end='')
    for k in style.keys():
        v = style[k]
        print ("""<th class="awrbg">""",end='')
        print (v.split(',')[0],end='')
        print ("""</th>""",end='')
    print ("""</tr>""")

    linenum = 0
    for row in rows:
        k = 0
        linenum += 1
        print ("<tr>",end='')
        if linenum % 2 == 0:
            classs='awrc'
        else:
            classs='awrnc'

        for col in row:
            k += 1
            if style[k].split(',')[1] == 'r':
                print ("""<td align="right" class='"""+classs+"'>"+str(col)+"</td>",end='')
            else:
                print ("""<td class='"""+classs+"'>"+str(col)+"</td>",end='')
        print ("</tr>")
    print ("""</table>
<br /><a class="awr" href="#top">Back to Top</a>
<p />
<p />
        """)

def f_print_table(rows,title,style,save_as):
    if save_as == "txt":
        f_print_table_txt(rows, title, style)
    elif save_as == "html":
        f_print_table_html(rows, title, style)

def f_print_query_table(conn, title, query, style,save_as):
    rows = f_get_query_record(conn, query)
    f_print_table(rows,title,style,save_as)

def f_is_sys_schema_exist(conn):
    query = "SHOW DATABASES"
    rows = f_get_query_record(conn, query)
    exist=False
    for row in rows:
       if row[0]=='sys':
           exist = True
           break
    return exist

def f_print_optimizer_switch(conn,save_as,perfor_or_infor):
    title = "Optimizer Switch"
    style = {1: 'switch_name,l', 2: 'value,r'}
    rows =[]
    query="select variable_value from "+perfor_or_infor+".global_variables where variable_name='optimizer_switch'"
    recode = f_get_query_record(conn, query)
    for col in recode[0][0].split(','):
        rows.append([col.split('=')[0],col.split('=')[1]])
    f_print_table(rows, title, style,save_as)

def f_print_log_error(conn,perfor_or_infor,save_as):
    title = "Log file Statistics"
    style = {1: 'start & shutdown:,l'}
    rows =[]
    WarnLog = 0
    ErrLog  = 0
    query = "SELECT variable_value FROM " + perfor_or_infor + ".global_variables where variable_name ='log_error'"
    filename = f_get_query_value(conn, query)
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            for line in f:
                if ('ready for connections' in line or 'Shutdown completed' in line):
                    rows.append([line])
                if ('Warning' in line):
                    WarnLog += 1
                if ('error' in line):
                    ErrLog += 1
    else:
        rows.append([filename + " not exists"])

    rows.append(['Warning & Error Statistics:'])
    rows.append([filename + ' contains ' + str(WarnLog) + ' warning(s).'])
    rows.append([filename + ' contains ' + str(ErrLog) + ' error(s).'])
    f_print_table(rows, title, style,save_as)

def f_print_caption(dbinfo,mysql_version,save_as):
    if save_as == "txt":
        print (tab2 * linesize)
        print (tab2, 'MySQL Watcher  V1.3.0'.center(linesize - 4), tab2)
        print (tab2, 'Kinghow@hotmail.com'.center(linesize - 4), tab2)
        print (tab2, 'https://github.com/kinghows/MySQL_Watcher'.center(linesize - 4), tab2)
        print (tab2 * linesize)
    elif save_as == "html":
        print ("""
<html><head><title>MySQL Watcher V1.2.0 Kinghow@hotmail.com https://github.com/kinghows/MySQL_Watcher </title>
<style type=\"text/css\">
body.awr {font:bold 10pt Arial,Helvetica,Geneva,sans-serif;color:black; background:White;}
pre.awr  {font:8pt Courier;color:black; background:White;}
h1.awr   {font:bold 20pt Arial,Helvetica,Geneva,sans-serif;color:#336699;background-color:White;border-bottom:1px solid #cccc99;margin-top:0pt; margin-bottom:0pt;padding:0px 0px 0px 0px;}
h2.awr   {font:bold 18pt Arial,Helvetica,Geneva,sans-serif;color:#336699;background-color:White;margin-top:4pt; margin-bottom:0pt;}
h3.awr {font:bold 16pt Arial,Helvetica,Geneva,sans-serif;color:#336699;background-color:White;margin-top:4pt; margin-bottom:0pt;}
li.awr {font: 8pt Arial,Helvetica,Geneva,sans-serif; color:black; background:White;}
th.awrnobg {font:bold 8pt Arial,Helvetica,Geneva,sans-serif; color:black; background:White;padding-left:4px; padding-right:4px;padding-bottom:2px}
th.awrbg {font:bold 8pt Arial,Helvetica,Geneva,sans-serif; color:White; background:#0066CC;padding-left:4px; padding-right:4px;padding-bottom:2px}
td.awrnc {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;}
td.awrc    {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;}
td.awrnclb {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-left: thin solid black;}
td.awrncbb {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-left: thin solid black;border-right: thin solid black;}
td.awrncrb {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-right: thin solid black;}
td.awrcrb    {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-right: thin solid black;}
td.awrclb    {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-left: thin solid black;}
td.awrcbb    {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-left: thin solid black;border-right: thin solid black;}
a.awr {font:bold 8pt Arial,Helvetica,sans-serif;color:#663300; vertical-align:top;margin-top:0pt; margin-bottom:0pt;}
td.awrnct {font:8pt Arial,Helvetica,Geneva,sans-serif;border-top: thin solid black;color:black;background:White;vertical-align:top;}
td.awrct   {font:8pt Arial,Helvetica,Geneva,sans-serif;border-top: thin solid black;color:black;background:#FFFFCC; vertical-align:top;}
td.awrnclbt  {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-top: thin solid black;border-left: thin solid black;}
td.awrncbbt  {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-left: thin solid black;border-right: thin solid black;border-top: thin solid black;}
td.awrncrbt {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:White;vertical-align:top;border-top: thin solid black;border-right: thin solid black;}
td.awrcrbt     {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-top: thin solid black;border-right: thin solid black;}
td.awrclbt     {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-top: thin solid black;border-left: thin solid black;}
td.awrcbbt   {font:8pt Arial,Helvetica,Geneva,sans-serif;color:black;background:#FFFFCC; vertical-align:top;border-top: thin solid black;border-left: thin solid black;border-right: thin solid black;}
table.tdiff {  border_collapse: collapse; }
</style></head><body class="awr">
<h1 class="awr">
WORKLOAD REPOSITORY report for
</h1>
       """)

    title = "Basic Information"
    style = {1: 'host,c', 2: 'user,c', 3: 'db,c', 4: 'mysql version,c'}
    rows = [[dbinfo[0], dbinfo[1], dbinfo[3], mysql_version]]
    f_print_table(rows, title, style,save_as)

def f_print_ending(save_as):
    if save_as == "txt":
        f_print_title('--@--  End  --@--')
    elif save_as == "html":
        print ("""
    <p />
    End of Report
    </body></html>
             """)

def size(device):
    nr_sectors = open(device+'/size').read().rstrip('\n')
    sect_size = open(device+'/queue/hw_sector_size').read().rstrip('\n')
    return (float(nr_sectors)*float(sect_size))/(1024.0*1024.0*1024.0)

def f_print_linux_info(save_as):
    title = "Linux info"
    style = {1: 'Linux,l',2: 'Info,l'}
    rows =[]
    #version
    rows.append(["Version",platform.uname()[0]+' '+platform.uname()[2]+' '+platform.uname()[4]])
    #cpu
    cpu_count = 0
    with open('/proc/cpuinfo') as f:
        for line in f:
            if line.strip():
                if line.rstrip('\n').startswith('model name'):
                    model_name = line.rstrip('\n').split(':')[1]
                    cpu_count +=1
    rows.append(["CPU",model_name + ' X '+str(cpu_count)])
    #mem
    meminfo = OrderedDict()
    with open('/proc/meminfo') as f:
        for line in f:
            meminfo[line.split(':')[0]] = line.split(':')[1].strip()
    rows.append(["Memory",'Total: {0}'.format(meminfo['MemTotal'])+' Free: {0}'.format(meminfo['MemFree'])])
    #net
    with open('/proc/net/dev') as f:
        net_dump = f.readlines()
    device_data = {}
    data = namedtuple('data', ['rx', 'tx'])
    for line in net_dump[2:]:
        line = line.split(':')
        if line[0].strip() != 'lo':
            device_data[line[0].strip()] = data(float(line[1].split()[0]) / (1024.0 * 1024.0),
                                                float(line[1].split()[8]) / (1024.0 * 1024.0))
    for dev in device_data.keys():
        rows.append(["Net",'{0}: {1} MiB {2} MiB'.format(dev, device_data[dev].rx, device_data[dev].tx)])
    #Device
    dev_pattern = ['sd.*', 'mmcblk*']
    for device in glob.glob('/sys/block/*'):
        for pattern in dev_pattern:
            if re.compile(pattern).match(os.path.basename(device)):
                rows.append(["Device",'{0}, Size: {1} GiB'.format(device, size(device))])
    #process
    pids = []
    for subdir in os.listdir('/proc'):
        if subdir.isdigit():
            pids.append(subdir)
    rows.append(["Processes",'Total number of running : {0}'.format(len(pids))])

    f_print_table(rows, title, style,save_as)

def f_print_filesystem_info(save_as):
    title = "Filesystem info"
    style = {1: 'Filesystem,l',2: 'Size,r',3: 'Used,r',4: 'Avail,r',5: 'Use %,r',6: ' Mounted on,l'}
    rows =[]
    file_info = []
    j = 0
    for line in os.popen('df -h').readlines():
        for eachList in line.strip().split():
            file_info.append(eachList)
            j +=1
    i = 6
    while i<j-6:
        rows.append([file_info[i+1],file_info[i+2],file_info[i+3],file_info[i+4],file_info[i+5],file_info[i+6]])
        i += 6
    f_print_table(rows, title, style,save_as)

def f_print_linux_status(save_as):
    ###获取参数###################################################################
    #scputimes(user=, nice, system, idle, iowait, irq, softirq,steal, guest, guest_nice)
    cpu_times = psutil.cpu_times()
    #scpustats(ctx_switches, interrupts, soft_interrupts, syscalls)
    #cpu_stats = psutil.cpu_stats()
    # svmem(total , available, percent, used , free, active, inactive, buffers, cached, shared)
    mem = psutil.virtual_memory()
    # sswap(total, used, free, percent, sin, sout)
    swap = psutil.swap_memory()
    #sdiskusage(total, used, free, percent)
    #disk_usage = psutil.disk_usage('/')
    #sdiskio(read_count, write_count, read_bytes, write_bytes, read_time, write_time)
    #disk_io_counters = psutil.disk_io_counters()
    #snetio(bytes_sent, bytes_recv, packets_sent, packets_recv, errin, errout, dropin, dropout)
    #net = psutil.net_io_counters()
    #load
    try:
        load = os.getloadavg()
    except (OSError, AttributeError):
        stats = {}
    else:
        stats = {'min1': load[0], 'min5': load[1], 'min15': load[2]}

    #Uptime = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
    ###打印参数###################################################################
    style1 = {1: '&nbsp;,6,l', 2: '&nbsp;,10,r',3: '&nbsp;,6,l', 4: '&nbsp;,10,r',5: '&nbsp;,6,l', 6: '&nbsp;,6,r',7: '&nbsp;,8,l',8: '&nbsp;,6,r',9: '&nbsp;,6,l', 10: '&nbsp;,6,r',11: '&nbsp;,6,l', 12: '&nbsp;,5,r',}
    style = {1: '&nbsp;,l', 2: '&nbsp;,r',3: '&nbsp;,l', 4: '&nbsp;,r',5: '&nbsp;,l', 6: '&nbsp;,r',7: '&nbsp;,l',8: '&nbsp;,r',9: '&nbsp;,l', 10: '&nbsp;,r',11: '&nbsp;,l', 12: '&nbsp;,r',}
    rows=[
          ["CPU", str(psutil.cpu_percent(interval=1))+'%',"nice", cpu_times.nice,"MEM", str(mem.percent) + '%',"active", str(mem.active/1024/1024) + 'M',"SWAP", str(swap.percent)+'%',"LOAD", str(psutil.cpu_count())+'core'],
          ["user", cpu_times.user,"irq", cpu_times.irq,"total", str(mem.total/1024/1024)+'M',"inactive", str(mem.inactive/1024/1024) + 'M',"total", str(swap.total/1024/1024) + 'M',"1 min", stats["min1"]],
          ["system", cpu_times.system,"iowait", cpu_times.iowait,"used", str(mem.used/1024/1024)+'M',"buffers", str(mem.buffers/1024/1024) + 'M',"used", str(swap.used/1024/1024) + 'M',"5 min", stats["min5"]],
          ["idle", cpu_times.idle,"steal", cpu_times.steal,"free", str(mem.free/1024/1024) + 'M',"cached", str(mem.cached/1024/1024) + 'M',"free", str(swap.free/1024/1024) + 'M',"15 min", stats["min15"]]
         ]

    title = "Linux Overview"
    if save_as == "txt":
        f_print_title(title)
        f_print_table_body(rows, style1,' ')
    elif save_as == "html":
        f_print_table_html(rows, title, style)

def f_print_host_memory_topN(topN,save_as):
    ps_result = list()
    for proc in psutil.process_iter():
        ps_result.append({'name': proc.name(), 'pid': proc.pid, 'cpu_percent': proc.cpu_percent(),
                          'memory_percent': proc.memory_percent()})
    rows = []
    for i, item in enumerate(sorted(ps_result, key=lambda x: x['memory_percent'], reverse=True)):
        if i >= topN:
            break
        rows.append([i + 1, item['name'], item['pid'], format(item['memory_percent'] / 100, '.2%')])

    style = {1: 'No,r', 2: 'Name,l',3: 'Pid,r', 4: 'Memory percent,r'}
    title = "Host memory top"+str(topN)
    f_print_table(rows, title, style, save_as)

def f_sec2dhms(sec):
    day = 24*60*60
    hour = 60*60
    min = 60
    if sec <60:
        return  "%ds"%math.ceil(sec)
    elif  sec > day:
        days = divmod(sec,day)
        return "%dd%s"%(int(days[0]),f_sec2dhms(days[1]))
    elif sec > hour:
        hours = divmod(sec,hour)
        return '%dh%s'%(int(hours[0]),f_sec2dhms(hours[1]))
    else:
        mins = divmod(sec,min)
        return "%dm%ds"%(int(mins[0]),math.ceil(mins[1]))

def f_get_mysql_status(conn):
    query = "SHOW GLOBAL STATUS"
    rows = f_get_query_record(conn, query)
    mysqlstatus = dict(rows)
    return mysqlstatus

def f_print_mysql_status(conn,perfor_or_infor,interval,save_as):
    ###获取参数###################################################################
    mysqlstatus1 = f_get_mysql_status(conn)
    time.sleep(interval)
    mysqlstatus2 = f_get_mysql_status(conn)

    # 执行查询的总次数
    Questions1 = int(mysqlstatus1["Questions"])
    Questions2 = int(mysqlstatus2["Questions"])
    # 服务器已经运行的时间（以秒为单位）
    Uptime2 = int(mysqlstatus2["Uptime"])
    Com_commit1 = int(mysqlstatus1["Com_commit"])
    Com_commit2 = int(mysqlstatus2["Com_commit"])
    Com_rollback1 = int(mysqlstatus1["Com_rollback"])
    Com_rollback2 = int(mysqlstatus2["Com_rollback"])
    # 从硬盘读取键的数据块的次数。如果Key_reads较大，则Key_buffer_size值可能太小。
    # 可以用Key_reads/Key_read_requests计算缓存损失率
    #Key_reads1 = int(mysqlstatus1["Key_reads"])
    #Key_reads2 = int(mysqlstatus2["Key_reads"])
    # 从缓存读键的数据块的请求数
    #Key_read_requests1 = int(mysqlstatus1["Key_read_requests"])
    #Key_read_requests2 = int(mysqlstatus2["Key_read_requests"])
    # 向硬盘写入将键的数据块的物理写操作的次数
    #Key_writes1 = int(mysqlstatus1["Key_writes"])
    #Key_writes2 = int(mysqlstatus2["Key_writes"])
    # 将键的数据块写入缓存的请求数
    #Key_write_requests1 = int(mysqlstatus1["Key_write_requests"])
    #Key_write_requests2 = int(mysqlstatus2["Key_write_requests"])
    # 不能满足InnoDB必须单页读取的缓冲池中的逻辑读数量。
    Innodb_buffer_pool_reads1 = int(mysqlstatus1["Innodb_buffer_pool_reads"])
    Innodb_buffer_pool_reads2 = int(mysqlstatus2["Innodb_buffer_pool_reads"])
    # InnoDB已经完成的逻辑读请求数
    Innodb_buffer_pool_read_requests1 = int(mysqlstatus1["Innodb_buffer_pool_read_requests"])
    Innodb_buffer_pool_read_requests2 = int(mysqlstatus2["Innodb_buffer_pool_read_requests"])

    # 当前打开的表的数量
    Open_tables1 = int(mysqlstatus2["Open_tables"])-int(mysqlstatus1["Open_tables"])
    Open_tables2 = int(mysqlstatus2["Open_tables"])
    # 已经打开的表的数量。如果Opened_tables较大，table_cache 值可能太小
    Opened_tables1 = int(mysqlstatus2["Opened_tables"])-int(mysqlstatus1["Opened_tables"])
    Opened_tables2 = int(mysqlstatus2["Opened_tables"])
    # 创建用来处理连接的线程数。如果Threads_created较大，你可能要
    # 增加thread_cache_size值。缓存访问率的计算方法Threads_created/Connections
    Threads_created1 = int(mysqlstatus1["Threads_created"])
    Threads_created2 = int(mysqlstatus2["Threads_created"])
    # 试图连接到(不管是否成功)MySQL服务器的连接数。缓存访问率的计算方法Threads_created/Connections
    Connections1 = int(mysqlstatus1["Connections"])
    Connections2 = int(mysqlstatus2["Connections"])
    Threads_connected1 = str(int(mysqlstatus2["Threads_connected"])-int(mysqlstatus1["Threads_connected"]))
    Threads_connected2 = mysqlstatus2["Threads_connected"]
    Aborted_connects1 = str(int(mysqlstatus2["Aborted_connects"])-int(mysqlstatus1["Aborted_connects"]))
    Aborted_connects2 = mysqlstatus2["Aborted_connects"]
    # Com_select/s：平均每秒select语句执行次数
    # Com_insert/s：平均每秒insert语句执行次数
    # Com_update/s：平均每秒update语句执行次数
    # Com_delete/s：平均每秒delete语句执行次数
    Com_select1 = int(mysqlstatus1["Com_select"])
    Com_select2 = int(mysqlstatus2["Com_select"])
    Com_insert1 = int(mysqlstatus1["Com_insert"])
    Com_insert2 = int(mysqlstatus2["Com_insert"])
    Com_update1 = int(mysqlstatus1["Com_update"])
    Com_update2 = int(mysqlstatus2["Com_update"])
    Com_delete1 = int(mysqlstatus1["Com_delete"])
    Com_delete2 = int(mysqlstatus2["Com_delete"])
    Com_replace1 = int(mysqlstatus1["Com_replace"])
    Com_replace2 = int(mysqlstatus2["Com_replace"])
    # 不能立即获得的表的锁的次数。如果该值较高，并且有性能问题，你应首先优化查询，然后拆分表或使用复制。
    #Table_locks_waited1 = int(mysqlstatus1["Table_locks_waited"])
    #Table_locks_waited2 = int(mysqlstatus2["Table_locks_waited"])
    # 立即获得的表的锁的次数
    #Table_locks_immediate1 = int(mysqlstatus1["Table_locks_immediate"])
    #Table_locks_immediate2 = int(mysqlstatus2["Table_locks_immediate"])
    # 服务器执行语句时自动创建的内存中的临时表的数量。如果Created_tmp_disk_tables较大，
    # 你可能要增加tmp_table_size值使临时 表基于内存而不基于硬盘
    Created_tmp_tables1 = int(mysqlstatus1["Created_tmp_tables"])
    Created_tmp_tables2 = int(mysqlstatus2["Created_tmp_tables"])
    # 服务器执行语句时在硬盘上自动创建的临时表的数量
    Created_tmp_disk_tables1 = int(mysqlstatus1["Created_tmp_disk_tables"])
    Created_tmp_disk_tables2 = int(mysqlstatus2["Created_tmp_disk_tables"])
    # 查询时间超过long_query_time秒的查询的个数 缓慢查询个数
    Slow_queries1 = int(mysqlstatus1["Slow_queries"])
    Slow_queries2 = int(mysqlstatus2["Slow_queries"])
    # 没有主键（key）联合（Join）的执行。该值可能是零。这是捕获开发错误的好方法，因为一些这样的查询可能降低系统的性能。
    Select_full_join1 = int(mysqlstatus1["Select_full_join"])
    Select_full_join2 = int(mysqlstatus2["Select_full_join"])
    #  Percentage of full table scans
    Handler_read_rnd_next1 = int(mysqlstatus1["Handler_read_rnd_next"])
    Handler_read_rnd_next2 = int(mysqlstatus2["Handler_read_rnd_next"])
    Handler_read_rnd1 = int(mysqlstatus1["Handler_read_rnd"])
    Handler_read_rnd2 = int(mysqlstatus2["Handler_read_rnd"])
    Handler_read_first1 = int(mysqlstatus1["Handler_read_first"])
    Handler_read_first2 = int(mysqlstatus2["Handler_read_first"])
    Handler_read_next1 = int(mysqlstatus1["Handler_read_next"])
    Handler_read_next2 = int(mysqlstatus2["Handler_read_next"])
    Handler_read_key1 = int(mysqlstatus1["Handler_read_key"])
    Handler_read_key2 = int(mysqlstatus2["Handler_read_key"])
    Handler_read_prev1 = int(mysqlstatus1["Handler_read_prev"])
    Handler_read_prev2 = int(mysqlstatus2["Handler_read_prev"])
    # 缓冲池利用率
    Innodb_buffer_pool_pages_total1 = int(mysqlstatus1["Innodb_buffer_pool_pages_total"])
    Innodb_buffer_pool_pages_total2 = int(mysqlstatus2["Innodb_buffer_pool_pages_total"])
    Innodb_buffer_pool_pages_free1 = int(mysqlstatus1["Innodb_buffer_pool_pages_free"])
    Innodb_buffer_pool_pages_free2 = int(mysqlstatus2["Innodb_buffer_pool_pages_free"])

    ###计算参数###################################################################
    Uptimes1 = str(interval) + "s"
    Uptimes2 = f_sec2dhms(Uptime2)
    # QPS = Questions / Seconds
    QPS1 = str(round((Questions2-Questions1) * 1.0 / interval, 2))+' ('+str(Questions2-Questions1)+'/'+str(interval)+')'
    QPS2 = str(round(Questions2* 1.0 / Uptime2, 2))+' ('+str(Questions2)+'/'+str(Uptime2)+')'

    TPS1 = str(round((Com_commit2 + Com_rollback2-Com_commit1 - Com_rollback1) * 1.0 / interval, 2))+' (('+str(Com_commit2 -Com_commit1)+'+'+str(Com_rollback2- Com_rollback1)+')/'+str(interval)+')'
    TPS2 = str(round((Com_commit2 + Com_rollback2)* 1.0 / Uptime2, 2))+' (('+str(Com_commit2)+'+'+str(Com_rollback2)+')/'+str(Uptime2)+')'

    Read1 = Com_select2 -Com_select1
    Read2 = Com_select2 
    ReadS1 = str(round(Read1 * 1.0 / interval, 2))+' ('+str(Read1)+'/'+str(interval)+')'
    ReadS2 = str(round(Read2* 1.0 / Uptime2, 2))+' ('+str(Read2)+'/'+str(Uptime2)+')'

    Write1 = Com_insert2 + Com_update2 + Com_delete2 + Com_replace2-Com_insert1 - Com_update1 - Com_delete1 - Com_replace1
    Write2 = Com_insert2 + Com_update2 + Com_delete2 + Com_replace2
    WriteS1 = str(round(Write1 * 1.0 / interval, 2))+' ('+str(Write1)+'/'+str(interval)+')'
    WriteS2 = str(round(Write2* 1.0 / Uptime2, 2))+' ('+str(Write2)+'/'+str(Uptime2)+')'
    # Read/Write Ratio
    if Write1!=0:
        rwr1 = str(round(Read1 * 1.0 / Write1,2))+' ('+str(Read1)+'/'+str(Write1)+')'
    else:
        rwr1 ='0.0%'

    if Write2!=0:
        rwr2 = str(round(Read2 * 1.0 / Write2,2))+' ('+str(Read2)+'/'+str(Write2)+')'
    else:
        rwr2 ='0.0%'

    Slow_queries_per_second1 = str(round((Slow_queries2-Slow_queries1) * 1.0 / interval, 2))+' ('+str(Slow_queries2-Slow_queries1)+'/'+str(interval)+')'
    Slow_queries_per_second2 = str(round(Slow_queries2 * 1.0 / Uptime2, 2))+' ('+str(Slow_queries2)+'/'+str(Uptime2)+')'
    #Slow_queries / Questions
    SQ1 = str(round(((Slow_queries2-Slow_queries1) * 1.0 / (Questions2-Questions1)) * 100, 2)) + "%"+' ('+str(Slow_queries2-Slow_queries1)+'/'+str(Questions2-Questions1)+')'
    SQ2 = str(round((Slow_queries2 * 1.0 / Questions2) * 100, 2)) + "%"+' ('+str(Slow_queries2)+'/'+str(Questions2)+')'

    if (Connections2-Connections1) != 0:
        Thread_cache_hits1 = str(round((1 - (Threads_created2-Threads_created1)* 1.0 / (Connections2-Connections1)) * 100, 2)) + "%"
    else:
        Thread_cache_hits1 = '0.0%'
    Thread_cache_hits2 = str(round((1 - Threads_created2 * 1.0 / Connections2) * 100, 2)) + "%"

    if (Innodb_buffer_pool_read_requests2-Innodb_buffer_pool_read_requests1) != 0:
        Innodb_buffer_read_hits1 = str(round((1 - (Innodb_buffer_pool_reads2-Innodb_buffer_pool_reads1) * 1.0 / (Innodb_buffer_pool_read_requests2-Innodb_buffer_pool_read_requests1)) * 100, 2)) + "%"+ "%"+' (1-'+str(Innodb_buffer_pool_reads2-Innodb_buffer_pool_reads1)+'/'+str(Innodb_buffer_pool_read_requests2-Innodb_buffer_pool_read_requests1)+')'
    else:
        Innodb_buffer_read_hits1 = '0.0%'
    Innodb_buffer_read_hits2 = str(round((1 - Innodb_buffer_pool_reads2* 1.0 / Innodb_buffer_pool_read_requests2) * 100, 2)) + "%"+' (1-'+str(Innodb_buffer_pool_reads2)+'/'+str(Innodb_buffer_pool_read_requests2)+')'

    Innodb_buffer_pool_utilization1 = str(round((Innodb_buffer_pool_pages_total1 - Innodb_buffer_pool_pages_free1) * 1.0 / Innodb_buffer_pool_pages_total1 * 100,2)) + "%"+' ('+str(Innodb_buffer_pool_pages_total1 - Innodb_buffer_pool_pages_free1)+'/'+str(Innodb_buffer_pool_pages_total1)+')'
    Innodb_buffer_pool_utilization2 = str(round((Innodb_buffer_pool_pages_total2 - Innodb_buffer_pool_pages_free2) * 1.0 / Innodb_buffer_pool_pages_total2 * 100,2)) + "%"+' ('+str(Innodb_buffer_pool_pages_total2 - Innodb_buffer_pool_pages_free2)+'/'+str(Innodb_buffer_pool_pages_total2)+')'

    """
    if (Key_read_requests2-Key_read_requests1) != 0:
        Key_buffer_read_hits1 = str(round((1 - (Key_reads2-Key_reads1) * 1.0 / (Key_read_requests2-Key_read_requests1)) * 100, 2)) + "%"
    else:
        Key_buffer_read_hits1 = '0.0%'
    if Key_read_requests2 != 0:
        Key_buffer_read_hits2 = str(round((1 - Key_reads2* 1.0 / Key_read_requests2) * 100, 2)) + "%"
    else:
        Key_buffer_read_hits2 = '0.0%'

    if (Key_write_requests2-Key_write_requests1)!=0:
        Key_buffer_write_hits1 = str(round((1 - (Key_writes2-Key_writes1)* 1.0 / (Key_write_requests2-Key_write_requests1)) * 100, 2)) + "%"
    else:
        Key_buffer_write_hits1 = '0.0%'
    if Key_write_requests2!=0:
        Key_buffer_write_hits2 = str(round((1 - Key_writes2* 1.0 / Key_write_requests2) * 100, 2)) + "%"
    else:
        Key_buffer_write_hits2 = '0.0%'
    """
    if (Select_full_join2-Select_full_join1) > 0:
        Select_full_join_per_second1 = str(round((Select_full_join2-Select_full_join1) * 1.0 / interval, 2))+' ('+str(Select_full_join2-Select_full_join1)+'/'+str(interval)+')'
    else:
        Select_full_join_per_second1 = '0.0%'
    Select_full_join_per_second2 = str(round(Select_full_join2 * 1.0 / Uptime2, 2))+' ('+str(Select_full_join2)+'/'+str(Uptime2)+')'

    if (Com_select2-Com_select1) > 0:
        full_select_in_all_select1 = str(round(((Select_full_join2-Select_full_join1) * 1.0 / (Com_select2-Com_select1)) * 100, 2)) + "%"+' ('+str(Select_full_join2-Select_full_join1)+'/'+str(Com_select2-Com_select1)+')'
    else:
        full_select_in_all_select1 = '0.0%'
    full_select_in_all_select2 = str(round((Select_full_join2 * 1.0 / Com_select2) * 100, 2)) + "%"+' ('+str(Select_full_join2)+'/'+str(Com_select2)+')'

    #((Handler_read_rnd_next + Handler_read_rnd) / (Handler_read_rnd_next + Handler_read_rnd + Handler_read_first + Handler_read_next + Handler_read_key + Handler_read_prev)).
    if (Handler_read_rnd_next2 -Handler_read_rnd_next1+ Handler_read_rnd2-Handler_read_rnd1 + Handler_read_first2 -Handler_read_first1+ Handler_read_next2-Handler_read_next1 + Handler_read_key2-Handler_read_key1 + Handler_read_prev2-Handler_read_prev1) > 0:
        full_table_scans1=str(round((Handler_read_rnd_next2 + Handler_read_rnd2-Handler_read_rnd_next1 - Handler_read_rnd1)* 1.0 / (Handler_read_rnd_next2 -Handler_read_rnd_next1+ Handler_read_rnd2-Handler_read_rnd1 + Handler_read_first2 -Handler_read_first1+ Handler_read_next2-Handler_read_next1 + Handler_read_key2-Handler_read_key2 + Handler_read_prev2-Handler_read_prev1)* 100, 2)) + "%"
    else:
        full_table_scans1 = '0.0%'
    full_table_scans2=str(round((Handler_read_rnd_next2 + Handler_read_rnd2)* 1.0 / (Handler_read_rnd_next2 + Handler_read_rnd2 + Handler_read_first2 + Handler_read_next2 + Handler_read_key2 + Handler_read_prev2)* 100, 2)) + "%"
    """
    if (Table_locks_immediate2-Table_locks_immediate1) > 0:
        lock_contention1 = str(round(((Table_locks_waited2-Table_locks_waited1) * 1.00 / (Table_locks_immediate2-Table_locks_immediate1)) * 100, 2)) + "%"
    else:
        lock_contention1 = '0.0%'
    lock_contention2 = str(round((Table_locks_waited2 * 1.00 / Table_locks_immediate2) * 100, 2)) + "%"
    """
    if (Created_tmp_tables2-Created_tmp_tables1) > 0:
        Temp_tables_to_disk1 = str(round(((Created_tmp_disk_tables2-Created_tmp_disk_tables1) * 1.0 / (Created_tmp_tables2-Created_tmp_tables1)) * 100, 2)) + "%"+' ('+str(Created_tmp_disk_tables2-Created_tmp_disk_tables1)+'/'+str(Created_tmp_tables2-Created_tmp_tables1)+')'
    else:
        Temp_tables_to_disk1 = '0.0%'
    Temp_tables_to_disk2 = str(round((Created_tmp_disk_tables2 * 1.0 / Created_tmp_tables2) * 100, 2)) + "%"+' ('+str(Created_tmp_disk_tables2)+'/'+str(Created_tmp_tables2)+')'

    ###打印参数###################################################################
    title = "MySQL Overview"
    style = {1: 'Key,l', 2: 'In '+Uptimes1+',r', 3: 'Total,r'}
    rows=[
          ["Uptimes",Uptimes1,Uptimes2],
          ["QPS (Questions / Seconds)", QPS1, QPS2],
          ["TPS ((Commit + Rollback)/ Seconds)", TPS1, TPS2],
          ["Reads per second", ReadS1, ReadS2],
          ["Writes per second", WriteS1, WriteS2],
          ["Read/Writes", rwr1,rwr2],
          ["Slow queries per second", Slow_queries_per_second1, Slow_queries_per_second2],
          ["Slow_queries/Questions", SQ1,SQ2],
          ["Threads connected", Threads_connected1, Threads_connected2],
          ["Aborted connects", Aborted_connects1, Aborted_connects2],
          ["Thread cache hits (>90%)", Thread_cache_hits1, Thread_cache_hits2],
          ["Innodb buffer hits(96% - 99%)", Innodb_buffer_read_hits1,Innodb_buffer_read_hits2],
          ["Innodb buffer pool utilization", Innodb_buffer_pool_utilization1,Innodb_buffer_pool_utilization2],
          #["Key buffer read hits(99.3% - 99.9%)",str(Key_buffer_read_hits1), str(Key_buffer_read_hits2)],
          #["Key buffer write hits(99.3% - 99.9%)", str(Key_buffer_write_hits1), str(Key_buffer_write_hits2)],
          ["Select full join per second", Select_full_join_per_second1, Select_full_join_per_second2],
          ["full select in all select", full_select_in_all_select1, full_select_in_all_select2],
          ["full table scans", full_table_scans1, full_table_scans2],
          #["MyISAM Lock waiting ratio", lock_contention1, lock_contention2],
          ["Current open tables", str(Open_tables1), str(Open_tables2)],
          ["Accumulative open tables", str(Opened_tables1), str(Opened_tables2)],
          ["Temp tables to disk(<10%)", Temp_tables_to_disk1, Temp_tables_to_disk2]
          ]

    f_print_table(rows, title, style,save_as)

if __name__=="__main__":
    dbinfo=["127.0.0.1","root","","mysql",3306] #host,user,passwd,db,port
    config_file="dbset.ini"
    mysql_version=""
    option = []
    save_as = "txt"

    opts, args = getopt.getopt(sys.argv[1:], "p:s:")
    for o,v in opts:
        if o == "-p":
            config_file = v
        elif o == "-s":
            save_as = v

    config = configparser.ConfigParser()
    config.read(config_file)
    dbinfo[0] = config.get("database","host")
    dbinfo[1] = config.get("database","user")
    dbinfo[2] = config.get("database","passwd")
    dbinfo[3] = config.get("database","db")
    dbinfo[4] = config.get("database", "port")
    interval  = int(config.get("option", "interval"))

    conn = f_get_conn(dbinfo)
    query ="select @@version"
    mysql_version = f_get_query_value(conn, query)
    f_print_caption(dbinfo,mysql_version,save_as)

    if "5.6" in mysql_version:
        perfor_or_infor = "information_schema"
    else:
        perfor_or_infor = "performance_schema"
        
    sys_schema_exist = f_is_sys_schema_exist(conn)

    if config.get("option","linux_info")=='ON':
        f_print_linux_info(save_as)

    if config.get("option","filesystem_info")=='ON':
        f_print_filesystem_info(save_as)

    if config.get("option","linux_overview")=='ON':
        f_print_linux_status(save_as)

    if config.get("option","host_memory_topN")!='OFF':
        topN=int(config.get("option","host_memory_topN"))
        f_print_host_memory_topN(topN,save_as)

    if config.get("option","mysql_overview")=='ON':
        f_print_mysql_status(conn,perfor_or_infor,interval,save_as)

    if config.get("option","sys_parm")=='ON':
        title = "System Parameter "
        query = "SELECT variable_name,IF(INSTR(variable_name,'size'), \
                 CASE  \
                 WHEN variable_value>=1024*1024*1024*1024*1024 THEN CONCAT(variable_value/1024/1024/1024/1024/1024,'P') \
                 WHEN variable_value>=1024*1024*1024*1024 THEN CONCAT(variable_value/1024/1024/1024/1024,'T') \
                 WHEN variable_value>=1024*1024*1024 THEN CONCAT(variable_value/1024/1024/1024,'G') \
                 WHEN variable_value>=1024*1024 THEN CONCAT(variable_value/1024/1024,'M') \
                 WHEN variable_value>=1024 THEN CONCAT(variable_value/1024,'K') \
                 ELSE variable_value END , \
                 variable_value)  \
                 FROM "+perfor_or_infor+".global_variables  \
                 where variable_name in ('" + "','".join(list(SYS_PARM_FILTER)) + "')"
        style = {1: 'parameter_name,l', 2: 'value,r'}
        f_print_query_table(conn, title, query, style,save_as)
        f_print_optimizer_switch(conn,save_as,perfor_or_infor)

    if config.get("option","log_error_statistics")=='ON':
        f_print_log_error(conn,perfor_or_infor,save_as)

    if config.get ( "option", "replication" ) == 'ON':
        title = "Replication"
        query = """SELECT USER,HOST,command,CONCAT(FLOOR(TIME/86400),'d',FLOOR(TIME/3600)%24,'h',FLOOR(TIME/60)%60,'m',TIME%60,'s') TIMES,state
                   FROM information_schema.processlist WHERE COMMAND = 'Binlog Dump' OR COMMAND = 'Binlog Dump GTID'"""
        style = {1: 'USER,l', 2: 'HOST,l', 3: 'command,l', 4: 'TIMES,r', 5: 'state,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "connect_count" ) == 'ON':
        title = "Connect Count"
        query = """SELECT SUBSTRING_INDEX(HOST,':',1) HOSTS,USER,db,command,COUNT(*),SUM(TIME)
                   FROM information_schema.processlist
                   WHERE Command !='' AND DB !='information_schema'
                   GROUP BY HOSTS,USER,db,command"""
        style = {1: 'HOSTS,l', 2: 'USER,l', 3: 'db,l', 4: 'command,l', 5: 'COUNT(*),r', 6: 'SUM(TIME),r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "avg_query_time" ) == 'ON' and not ("5.6" in mysql_version):
        title = "Avg Query Time"
        query = """SELECT schema_name,SUM(count_star) COUNT, ROUND((SUM(sum_timer_wait)/SUM(count_star))/1000000) avg_microsec
                   FROM performance_schema.events_statements_summary_by_digest
                   WHERE schema_name IS NOT NULL
                   GROUP BY schema_name"""
        style = {1: 'schema_name,l', 2: 'COUNT,r', 3: 'avg_microsec,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "slow_query_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "slow_query_topN"))
        title = "Slow Query Top"+str(topN)
        query = "SELECT QUERY,db,exec_count,total_latency,max_latency,avg_latency FROM sys.statements_with_runtimes_in_95th_percentile LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'db,r', 3: 'exec_count,r', 4: 'total_latency,r', 5: 'max_latency,r', 6: 'avg_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "err_sql_count" ) == 'ON' and ("5.7" in mysql_version):
        title = "Err Sql Count"
        query = """SELECT schema_name,SUM(sum_errors) err_count
                   FROM performance_schema.events_statements_summary_by_digest
                   WHERE sum_errors > 0
                   GROUP BY schema_name"""
        style = {1: 'schema_name,l', 2: 'err_count,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "err_sql_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "err_sql_topN"))
        title = "Err SQL Top"+str(topN)
        query = "SELECT QUERY,db,exec_count,ERRORS FROM sys.statements_with_errors_or_warnings ORDER BY ERRORS DESC LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'db,r', 3: 'exec_count,r', 4: 'ERRORS,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "query_analysis_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "query_analysis_topN"))
        title = "query analysis top"+str(topN)
        query = """SELECT QUERY,full_scan,exec_count,total_latency,lock_latency,rows_sent_avg,rows_examined_avg,
                 tmp_tables,tmp_disk_tables,rows_sorted,last_seen
                   FROM sys.statement_analysis
                   where db='""" + dbinfo[3] + "' ORDER BY total_latency DESC  LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'fscan,l', 3: 'ex_cot,r', 4: 'total_ltc,r', 5:'lock_ltc,r', 6: 'rw_st_avg,r',
                 7: 'rw_exm_avg,9,r',8: 'tmp_table,9,r',9: 'tp_dk_tab,9,r',10: 'rows_sort,9,r',11: 'last_seen,19,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "query_full_table_scans_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "query_full_table_scans_topN"))
        title = "query full table scans top"+str(topN)
        query = """SELECT QUERY,exec_count,total_latency,no_index_used_count,no_good_index_used_count,no_index_used_pct,rows_sent_avg,rows_examined_avg,last_seen
                    FROM sys.statements_with_full_table_scans
                    where db='""" + dbinfo[3] + "' ORDER BY total_latency DESC  LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'ex_cot,r', 3: 'total_ltc,r', 4:'no_idx_use,r', 5: 'n_g_idx_use,r',6: 'n_i_u_pct,r',
                 7: 'rw_st_avg,r',8: 'rw_exm_avg,r',9: 'last_seen,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "query_sorting_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "query_sorting_topN"))
        title = "query sorting top"+str(topN)
        query = """SELECT QUERY,exec_count,total_latency,sort_merge_passes,avg_sort_merges,sorts_using_scans,sort_using_range,
                    rows_sorted,avg_rows_sorted,last_seen
                    FROM sys.statements_with_sorting
                    where db='""" + dbinfo[3] + "' ORDER BY avg_rows_sorted DESC  LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'ex_cot,r', 3: 'total_ltc,r', 4:'st_mg_ps,r', 5: 'avg_st_mg,r',6: 'st_us_scan,r',
                 7: 'st_us_rag,r',8: 'rows_sort,r',9: 'avg_rw_st,r',10: 'last_seen,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "query_with_temp_tables_topN" ) != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "query_with_temp_tables_topN"))
        title = "query with temp tables top"+str(topN)
        query = """SELECT QUERY,exec_count,total_latency,memory_tmp_tables,disk_tmp_tables,avg_tmp_tables_per_query,tmp_tables_to_disk_pct,last_seen
                    FROM sys.statements_with_temp_tables
                    where db='""" + dbinfo[3] + "' ORDER BY avg_tmp_tables_per_query DESC  LIMIT "+str(topN)
        style = {1: 'QUERY,l', 2: 'ex_cot,r', 3: 'total_ltc,r', 4:'mem_tmp_tab,r', 5: 'dsk_tmp_tab,r',6: 'avg_tt_per_qry,r',
                 7: 'tt_to_dk_pct,r',8:'last_seen,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "database_size" ) == 'ON':
        title = "Database Size"
        query = """SELECT table_schema,
                   CONCAT(ROUND(SUM(data_length)/(1024*1024),2),'MB') AS 'Table Size',
                   CONCAT(ROUND(SUM(index_length)/(1024*1024),2),'MB') AS 'Index Size' ,
                   CONCAT(ROUND(SUM(data_length)/(1024*1024),2) + ROUND(SUM(index_length)/(1024*1024),2),'MB') AS 'DB Size'
                   FROM information_schema.tables GROUP BY table_schema
                   UNION
                   SELECT '*** all ***' table_schema,
                   CONCAT(ROUND(SUM(data_length)/(1024*1024),2),'MB') AS 'Table Size',
                   CONCAT(ROUND(SUM(index_length)/(1024*1024),2),'MB') AS 'Index Size' ,
                   CONCAT(ROUND(SUM(data_length)/(1024*1024),2) + ROUND(SUM(index_length)/(1024*1024),2),'MB') AS 'DB Size'
                   FROM information_schema.tables"""
        style = {1: 'table_schema,l', 2: 'Table Size,r', 3: 'Index Size,r', 4: 'DB Size,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option","object_count")=='ON':
        title = "Object Count"
        query = "SELECT information_schema.routines.ROUTINE_TYPE AS object_type, COUNT(0) AS COUNT FROM information_schema.routines \
                 WHERE information_schema.routines.ROUTINE_SCHEMA='" + dbinfo[3] + "' GROUP BY information_schema.routines.ROUTINE_TYPE UNION \
                 SELECT information_schema.tables.TABLE_TYPE AS object_type, COUNT(0) AS COUNT FROM information_schema.tables  \
                 WHERE information_schema.tables.TABLE_SCHEMA='" + dbinfo[3] + "' GROUP BY information_schema.tables.TABLE_TYPE UNION \
                 SELECT CONCAT('INDEX (',information_schema.statistics.INDEX_TYPE,')') AS object_type,COUNT(0) AS COUNT FROM information_schema.statistics \
                 WHERE information_schema.statistics.TABLE_SCHEMA='" + dbinfo[3] + "' GROUP BY information_schema.statistics.INDEX_TYPE UNION \
                 SELECT 'TRIGGER' AS `TRIGGER`,COUNT(0) AS COUNT FROM information_schema.triggers \
                 WHERE information_schema.triggers.TRIGGER_SCHEMA='" + dbinfo[3] + "' UNION \
                 SELECT 'EVENT' AS object_type, COUNT(0) AS COUNT FROM information_schema.events \
                 WHERE information_schema.events.EVENT_SCHEMA='" + dbinfo[3] + "'"
        style = {1:'object_type,l',2: 'COUNT,r'}
        if save_as == "txt":
            f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "table_info" ) == 'ON':
        title = "Table Info"
        query = """select table_name,engine,row_format as format,table_rows,avg_row_length as avg_row,
                   round((data_length)/1024/1024,2) as data_mb,
                   round((index_length)/1024/1024,2) as index_mb,
                   round((data_length+index_length)/1024/1024,2) as total_mb
                   from information_schema.tables
                   where table_schema='""" + dbinfo[3] + "'"
        style = {1: 'table_name,l', 2: 'engine,l', 3: 'format,l', 4: 'table_rows,r', 5: 'avg_row,r',
                 6: 'data_mb,r', 7: 'index_mb,r', 8: 'total_mb,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "index_info" ) == 'ON':
        title = "Index Info"
        query = """select index_name,non_unique,seq_in_index,column_name,collation,cardinality,nullable,index_type
                   from information_schema.statistics
                   where table_schema='""" + dbinfo[3] + "'"
        style = {1: 'index_name,l', 2: 'non_unique,l', 3: 'seq_in_index,l', 4: 'column_name,l',
                 5: 'collation,r', 6: 'cardinality,r', 7: 'nullable,r', 8: 'index_type,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_index_statistics") == 'ON' and sys_schema_exist:
        title = "schema_index_statistics"
        query = """SELECT table_name,index_name ,rows_selected,select_latency,rows_inserted,insert_latency,rows_updated,
                    update_latency,rows_deleted,delete_latency
                    FROM sys.schema_index_statistics where table_schema='""" +  dbinfo[3] + "' ORDER BY table_name"
        style = {1: 'table_name,l', 2: 'index_name,l', 3: 'rows_selected,r', 4: 'select_latency,r',5: 'rows_inserted,r',
                 6: 'insert_latency,r', 7: 'rows_updated,r', 8: 'update_latency,r', 9: 'rows_deleted,r',10: 'delete_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_table_statistics") == 'ON' and sys_schema_exist:
        title = "schema_table_statistics"
        query = """SELECT table_name,total_latency ,rows_fetched,fetch_latency,rows_inserted,insert_latency,rows_updated,
                    update_latency,rows_deleted,delete_latency,io_read_requests,io_read,io_read_latency,io_write_requests,
                    io_write,io_write_latency,io_misc_requests,io_misc_latency
                    FROM sys.schema_table_statistics  where table_schema='""" +  dbinfo[3] + "' ORDER BY table_name"
        style = {1: 'table_name,l', 2: 'tal_ltc,r', 3: 'rw_ftc,r', 4: 'ftc_ltc,r',
                 5: 'rw_ins,r', 6: 'ins_ltc,r', 7: 'rw_upd,r', 8: 'upd_ltc,r',
                 9: 'rw_del,r', 10: 'del_ltc,r', 11: 'io_rd_rq,r', 12: 'io_read,r',
                 13: 'io_rd_ltc,r', 14: 'io_wt_rq,r', 15: 'io_write,r',16: 'io_wt_ltc,r',
                 17: 'io_ms_rq,r',18: 'io_ms_ltc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_table_statistics_with_buffer") == 'ON' and sys_schema_exist:
        title = "schema_table_statistics_with_buffer"
        query = """SELECT table_name,innodb_buffer_allocated,innodb_buffer_data,innodb_buffer_free,innodb_buffer_pages,
                    innodb_buffer_pages_hashed,innodb_buffer_pages_old,innodb_buffer_rows_cached
                    FROM sys.schema_table_statistics_with_buffer where table_schema='""" + dbinfo[3] + "' ORDER BY table_name"
        style = {1: 'table_name,l', 2: 'indb_buf_alc,r', 3: 'indb_buf_data,r', 4: 'indb_buf_free,r', 5: 'indb_buf_page,r',
                 6: 'indb_buf_page_hash,r', 7: 'indb_buf_page_old,r', 8: 'indb_buf_rw_cach,r'}
        f_print_query_table(conn, title, query, style, save_as)

    if config.get("option", "schema_tables_with_full_table_scans") == 'ON' and sys_schema_exist:
        title = "schema_tables_with_full_table_scans"
        query = """SELECT object_schema,object_name,rows_full_scanned,latency FROM sys.schema_tables_with_full_table_scans
                    where object_schema='""" + dbinfo[3] + "' ORDER BY object_name"
        style = {1: 'object_schema,l', 2: 'object_name,l', 3: 'rows_full_scanned,r', 4: 'latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_unused_indexes") == 'ON' and sys_schema_exist:
        title = "Schema Unused Indexes"
        query = "SELECT object_schema,object_name,index_name FROM sys.schema_unused_indexes where object_schema='" +  dbinfo[3] + "'"
        style = {1: 'object_schema,l', 2: 'object_name,l', 3: 'index_name,l'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary") == 'ON' and sys_schema_exist:
        title = "host_summary"
        #host 监听连接过的主机 statements 当前主机执行的语句总数 statement_latency 语句等待时间（延迟时间） statement_avg_latency 执行语句平均延迟时间 table_scans 表扫描次数
        #file_ios io时间总数 file_io_latency 文件io延迟 current_connections 当前连接数 total_connections 总链接数 unique_users 该主机的唯一用户数 current_memory 当前账户分配的内存
        #total_memory_allocated 该主机分配的内存总数
        if "5.6" in mysql_version:
            query = """SELECT host,statements,statement_latency,statement_avg_latency,table_scans,file_ios,file_io_latency,current_connections,
                        total_connections,unique_users
                        FROM sys.host_summary"""
            style = {1: 'host,l', 2: 'statements,r', 3: 'st_ltc,r', 4: 'st_avg_ltc,r', 5: 'table_scan,r', 6: 'file_ios,r',
                     7: 'f_io_ltc,r', 8: 'cur_conns,r', 9: 'total_conn,r', 10: 'unq_users,r'}
        else:
            query = """SELECT host,statements,statement_latency,statement_avg_latency,table_scans,file_ios,file_io_latency,current_connections,
                    total_connections,unique_users,current_memory,total_memory_allocated
                    FROM sys.host_summary"""
            style = {1: 'host,l', 2: 'statements,r', 3: 'st_ltc,r', 4: 'st_avg_ltc,r', 5: 'table_scan,r', 6: 'file_ios,r',
                     7: 'f_io_ltc,r', 8: 'cur_conns,r', 9: 'total_conn,r', 10: 'unq_users,r', 11: 'cur_mem,r',
                     12: 'tal_mem_alc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_file_io_type") == 'ON' and sys_schema_exist:
        title = "host_summary_by_file_io_type"
        #•host 主机 event_name IO事件名称 total 该主机发生的事件 total_latency 该主机发生IO事件总延迟时间 max_latency 该主机IO事件中最大的延迟时间
        query = """SELECT host,event_name,total,total_latency,max_latency
                    FROM sys.host_summary_by_file_io_type"""
        style = {1: 'host,l', 2: 'event_name,l', 3: 'total,r', 4: 'total_ltc,r', 5: 'max_ltc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_file_io") == 'ON' and sys_schema_exist:
        title = "host_summary_by_file_io_type"
        #•host 主机 ios IO事件总数 io_latency IO总的延迟时间
        query = """SELECT host,ios,io_latency
                    FROM sys.host_summary_by_file_io"""
        style = {1: 'host,l', 2: 'ios,r', 3: 'io_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_stages") == 'ON' and sys_schema_exist:
        title = "host_summary_by_stages"
        #•host 主机  event_name stage event名称 total stage event发生的总数 total_latency stage event总的延迟时间 avg_latency stage event平均延迟时间
        query = """SELECT host,event_name,total,total_latency,avg_latency
                    FROM sys.host_summary_by_stages"""
        style = {1: 'host,l', 2: 'event_name,l', 3: 'total,r', 4: 'total_latency,r', 5: 'avg_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_statement_latency") == 'ON' and sys_schema_exist:
        title = "host_summary_by_statement_latency"
        #host 主机  total 这个主机的语句总数  total_latency 这个主机总的延迟时间 max_latency 主机最大的延迟时间 lock_latency 等待锁的锁延迟时间
        #rows_sent 该主机通过语句返回的总行数 rows_examined 在存储引擎上通过语句返回的行数 rows_affected 该主机通过语句影响的总行数 full_scans 全表扫描的语句总数
        query = """SELECT host,total,total_latency,max_latency,lock_latency,rows_sent,rows_examined,rows_affected,full_scans
                    FROM sys.host_summary_by_statement_latency"""
        style = {1: 'host,l', 2: 'total,r', 3: 'total_latency,r', 4: 'max_latency,r', 5: 'lock_latency,r',
                 6: 'rows_sent,r', 7: 'rows_examined,r', 8: 'rows_affected,r',9: 'full_scans,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_statement_type") == 'ON' and sys_schema_exist:
        title = "host_summary_by_statement_type"
        #host 主机  statement 最后的语句事件名称 total sql语句总数 total_latency sql语句总延迟数 max_latency 最大的sql语句延迟数
        # lock_latency 锁延迟总数 rows_sent 语句返回的行总数 rows_examined 通过存储引擎的sql语句的读取的总行数 rows_affected 语句影响的总行数 full_scans 全表扫描的语句事件总数
        query = """SELECT host,statement,total,total_latency,max_latency,lock_latency,rows_sent,rows_examined,rows_affected,full_scans
                    FROM sys.host_summary_by_statement_type"""
        style = {1: 'host,l', 2: 'statement,l', 3: 'total,r', 4: 'total_latency,r', 5: 'max_latency,r',
                 6: 'lock_latency,r', 7: 'rows_sent,r', 8: 'rows_examined,r',9: 'rows_affected,r',10: 'full_scans,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary") == 'ON' and sys_schema_exist:
        title = "user_summary"
        # statements 当前用户执行的语句总数 statement_latency 语句等待时间（延迟时间） statement_avg_latency 执行语句平均延迟时间 table_scans 表扫描次数
        #file_ios io时间总数 file_io_latency 文件io延迟 current_connections 当前连接数 total_connections 总链接数 unique_users 该用户的唯一主机数 current_memory 当前账户分配的内存
        #total_memory_allocated 该主机分配的内存总数
        if "5.6" in mysql_version:

            query = """SELECT user,statements,statement_latency,statement_avg_latency,table_scans,file_ios,file_io_latency,current_connections,
                    total_connections,unique_hosts
                    FROM sys.user_summary"""
            style = {1: 'user,l', 2: 'statements,r', 3: 'st_ltc,r', 4: 'st_avg_ltc,r', 5: 'table_scan,r', 6: 'file_ios,r',
                     7: 'f_io_ltc,r', 8: 'cur_conns,r', 9: 'total_conn,r', 10: 'unq_hosts,r'}
        else:
            query = """SELECT user,statements,statement_latency,statement_avg_latency,table_scans,file_ios,file_io_latency,current_connections,
                        total_connections,unique_hosts,current_memory,total_memory_allocated
                        FROM sys.user_summary"""
            style = {1: 'user,l', 2: 'statements,r', 3: 'st_ltc,r', 4: 'st_avg_ltc,r', 5: 'table_scan,r', 6: 'file_ios,r',
                     7: 'f_io_ltc,r', 8: 'cur_conns,r', 9: 'total_conn,r', 10: 'unq_hosts,r', 11: 'cur_mem,r', 12: 'tal_mem_alc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary_by_file_io_type") == 'ON' and sys_schema_exist:
        title = "user_summary_by_file_io_type"
        #event_name IO事件名称 total 该用户发生的事件 total_latency 该用户发生IO事件总延迟时间 max_latency 该用户IO事件中最大的延迟时间
        query = """SELECT user,event_name,total,latency,max_latency
                    FROM sys.user_summary_by_file_io_type"""
        style = {1: 'user,l', 2: 'event_name,l', 3: 'total,r', 4: 'latency,r', 5: 'max_ltc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary_by_file_io") == 'ON' and sys_schema_exist:
        title = "user_summary_by_file_io_type"
        # ios IO事件总数 io_latency IO总的延迟时间
        query = """SELECT user,ios,io_latency
                    FROM sys.user_summary_by_file_io"""
        style = {1: 'user,l', 2: 'ios,r', 3: 'io_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary_by_stages") == 'ON' and sys_schema_exist:
        title = "user_summary_by_stages"
        #  event_name stage event名称 total stage event发生的总数 total_latency stage event总的延迟时间 avg_latency stage event平均延迟时间
        query = """SELECT user,event_name,total,total_latency,avg_latency
                    FROM sys.user_summary_by_stages"""
        style = {1: 'user,l', 2: 'event_name,l', 3: 'total,r', 4: 'total_latency,r', 5: 'avg_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary_by_statement_latency") == 'ON' and sys_schema_exist:
        title = "user_summary_by_statement_latency"
        #  total 这个主机的语句总数  total_latency 这个主机总的延迟时间 max_latency 主机最大的延迟时间 lock_latency 等待锁的锁延迟时间
        #rows_sent 该主机通过语句返回的总行数 rows_examined 在存储引擎上通过语句返回的行数 rows_affected 该主机通过语句影响的总行数 full_scans 全表扫描的语句总数
        query = """SELECT user,total,total_latency,max_latency,lock_latency,rows_sent,rows_examined,rows_affected,full_scans
                    FROM sys.user_summary_by_statement_latency"""
        style = {1: 'user,l', 2: 'total,r', 3: 'total_latency,r', 4: 'max_latency,r', 5: 'lock_latency,r',
                 6: 'rows_sent,r', 7: 'rows_examined,r', 8: 'rows_affected,r',9: 'full_scans,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "user_summary_by_statement_type") == 'ON' and sys_schema_exist:
        title = "user_summary_by_statement_type"
        #statement 最后的语句事件名称 total sql语句总数 total_latency sql语句总延迟数 max_latency 最大的sql语句延迟数
        # lock_latency 锁延迟总数 rows_sent 语句返回的行总数 rows_examined 通过存储引擎的sql语句的读取的总行数 rows_affected 语句影响的总行数 full_scans 全表扫描的语句事件总数
        query = """SELECT user,statement,total,total_latency,max_latency,lock_latency,rows_sent,rows_examined,rows_affected,full_scans
                    FROM sys.user_summary_by_statement_type"""
        style = {1: 'user,l', 2: 'statement,l', 3: 'total,r', 4: 'total_latency,r', 5: 'max_latency,r',
                 6: 'lock_latency,r', 7: 'rows_sent,r', 8: 'rows_examined,r',9: 'rows_affected,r',10: 'full_scans,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "innodb_buffer_stats_by_schema") == 'ON' and sys_schema_exist:
        title = "innodb_buffer_stats_by_schema"
        #object_schema 数据库名称 allocated 分配给当前数据库的总的字节数 data 分配给当前数据库的数据字节数 pages 分配给当前数据库的总页数
        # pages_hashed 分配给当前数据库的hash页数 pages_old 分配给当前数据库的旧页数  rows_cached 当前数据库缓存的行数
        query = """SELECT object_schema,allocated,data,pages,pages_hashed,pages_old,rows_cached
                    FROM sys.innodb_buffer_stats_by_schema"""
        style = {1: 'object_schema,l', 2: 'allocated,r', 3: 'data,r', 4: 'pages,r', 5: 'pages_hashed,r',
                 6: 'pages_old,r', 7: 'rows_cached,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "innodb_buffer_stats_by_table") == 'ON' and sys_schema_exist:
        title = "innodb_buffer_stats_by_table"
        # object_schema 数据库名称 object_name 表名称 allocated 分配给表的总字节数 data 分配该表的数据字节数 pages 分配给表的页数
        #  pages_hashed 分配给表的hash页数 pages_old 分配给表的旧页数 rows_cached 表的行缓存数
        query = """SELECT object_schema,object_name,allocated,data,pages,pages_hashed,pages_old,rows_cached
                    FROM sys.innodb_buffer_stats_by_table"""
        style = {1: 'object_schema,l', 2: 'object_name,l', 3: 'allocated,r', 4: 'data,r', 5: 'pages,r',
                 6: 'pages_hashed,r', 7: 'pages_old,r', 8: 'rows_cached,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "io_by_thread_by_latency_topN")  != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "io_by_thread_by_latency_topN"))
        title = "io_by_thread_by_latency top"+str(topN)
        #user 对于当前线程来说，这个值是线程被分配的账户，对于后台线程来讲，就是线程的名称 total IO事件的总数 total_latency IO事件的总延迟
        # min_latency 单个最小的IO事件延迟 avg_latency 平均IO延迟 max_latency 最大IO延迟 thread_id 线程ID processlist_id 对于当前线程就是此时的ID，对于后台就是null
        query = """SELECT user,total,total_latency,min_latency,avg_latency,max_latency,thread_id,processlist_id
                    FROM sys.io_by_thread_by_latency  LIMIT """+str(topN)
        style = {1: 'user,l', 2: 'total,r', 3: 'total_latency,r', 4: 'min_latency,r', 5: 'avg_latency,r',
                 6: 'max_latency,r', 7: 'thread_id,r', 8: 'processlist_id,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "io_global_by_file_by_bytes_topN")  != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "io_global_by_file_by_bytes_topN"))
        title = "io_global_by_file_by_bytes top"+str(topN)
        query = """SELECT file,count_read,total_read,avg_read,count_write,total_written,avg_write,total,write_pct
                    FROM sys.io_global_by_file_by_bytes  LIMIT """+str(topN)
        style = {1: 'file,l', 2: 'count_read,r', 3: 'total_read,r', 4: 'avg_read,r', 5: 'count_write,r',
                 6: 'total_written,r', 7: 'avg_write,r', 8: 'total,r', 9: 'write_pct,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "io_global_by_file_by_latency_topN")  != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "io_global_by_file_by_latency_topN"))
        title = "io_global_by_file_by_latency top"+str(topN)
        query = """SELECT file,total,total_latency,count_read,read_latency,count_write,write_latency,count_misc,misc_latency
                    FROM sys.io_global_by_file_by_latency  LIMIT """+str(topN)
        style = {1: 'file,l', 2: 'total,r', 3: 'total_latency,r', 4: 'count_read,r', 5: 'read_latency,r',
                 6: 'count_write,r', 7: 'write_latency,r', 8: 'count_misc,r', 9: 'misc_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "io_global_by_wait_by_bytes_topN")  != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "io_global_by_wait_by_bytes_topN"))
        title = "io_global_by_wait_by_bytes top"+str(topN)
        query = """SELECT event_name,total,total_latency,min_latency,avg_latency,max_latency,count_read,total_read,avg_read,count_write,
                    total_written,avg_written,total_requested
                    FROM sys.io_global_by_wait_by_bytes  LIMIT """+str(topN)
        style = {1: 'event_name,l', 2: 'total,r', 3: 'total_latency,r', 4: 'min_latency,r', 5: 'avg_latency,r',
                 6: 'max_latency,r', 7: 'count_read,r', 8: 'total_read,r', 9: 'avg_read,r', 10: 'count_write,r',
                 11: 'total_written,r', 12: 'avg_written,r', 13: 'total_requested,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "io_global_by_wait_by_latency_topN")  != 'OFF' and sys_schema_exist:
        topN = int(config.get("option", "io_global_by_wait_by_latency_topN"))
        title = "io_global_by_wait_by_latency top"+str(topN)
        query = """SELECT event_name,total,total_latency,avg_latency,max_latency,read_latency,write_latency,misc_latency,count_read,
                    total_read,avg_read,count_write,total_written,avg_written
                    FROM sys.io_global_by_wait_by_latency  LIMIT """+str(topN)
        style = {1: 'event_name,l', 2: 'total,r', 3: 'total_latency,r', 4: 'avg_latency,r', 5: 'max_latency,r',
                 6: 'read_latency,r', 7: 'write_latency,r', 8: 'misc_latency,r', 9: 'count_read,r', 10: 'total_read,r',
                 11: 'avg_read,r', 12: 'count_write,r', 13: 'total_written,r', 14: 'avg_written,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "wait_classes_global_by_avg_latency") == 'ON' and sys_schema_exist:
        title = "wait_classes_global_by_avg_latency"
        query = """SELECT event_class,total,total_latency,min_latency,avg_latency,max_latency
                    FROM sys.wait_classes_global_by_avg_latency"""
        style = {1: 'event_class,l', 2: 'total,r', 3: 'total_latency,r',4: 'min_latency,r', 5: 'avg_latency,r', 6: 'max_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "wait_classes_global_by_latency") == 'ON' and sys_schema_exist:
        title = "wait_classes_global_by_latency"
        query = """SELECT event_class,total,total_latency,min_latency,avg_latency,max_latency
                    FROM sys.wait_classes_global_by_latency"""
        style = {1: 'event_class,l', 2: 'total,r', 3: 'total_latency,r',4: 'min_latency,r', 5: 'avg_latency,r', 6: 'max_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "waits_by_host_by_latency") == 'ON' and sys_schema_exist:
        title = "waits_by_host_by_latency"
        query = """SELECT HOST,EVENT,total,total_latency,avg_latency,max_latency
                    FROM sys.waits_by_host_by_latency """
        style = {1: 'host,l',2: 'event,l', 3: 'total,r', 4: 'total_latency,r',5: 'avg_latency,r', 6: 'max_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "waits_by_user_by_latency") == 'ON' and sys_schema_exist:
        title = "waits_by_user_by_latency"
        query = """SELECT USER,EVENT,total,total_latency,avg_latency,max_latency
                    FROM sys.waits_by_user_by_latency """
        style = {1: 'user,l',2: 'event,l', 3: 'total,r', 4: 'total_latency,r',5: 'avg_latency,r', 6: 'max_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "waits_global_by_latency") == 'ON' and sys_schema_exist:
        title = "waits_global_by_latency"
        query = """SELECT EVENTS,total,total_latency,avg_latency,max_latency
                    FROM sys.waits_global_by_latency """
        style = {1: 'event,l', 2: 'total,r', 3: 'total_latency,r',4: 'avg_latency,r', 5: 'max_latency,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_table_lock_waits") == 'ON' and sys_schema_exist and not "5.6" in mysql_version:
        title = "schema_table_lock_waits"
        query = """SELECT object_schema,object_name,waiting_account,waiting_lock_type,
                    waiting_lock_duration,waiting_query,waiting_query_secs,waiting_query_rows_affected,waiting_query_rows_examined,
                    blocking_account,blocking_lock_type,blocking_lock_duration
                    FROM sys.schema_table_lock_waits"""
        #,sql_kill_blocking_query,sql_kill_blocking_connection
        style = {1: 'object_schema,l', 2: 'object_name,r', 3: 'wait_account,r', 4: 'wt_lk_tp,l', 5: 'w_l_dur,l',
                 6: 'waiting_query,l', 7: 'w_qry_s,l', 8: 'w_q_r_a,l',9: 'w_q_r_e,l',10: 'blk_account,l',
                 11: 'bk_lk_tp,l',12: 'b_l_dur,l'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "innodb_lock_waits") == 'ON' and sys_schema_exist:
        title = "innodb_lock_waits"
        #wait_started 锁等待发生的时间 wait_age 锁已经等待了多长时间 wait_age_secs 以秒为单位显示锁已经等待的时间
        #locked_table 被锁的表 locked_index 被锁住的索引 locked_type 锁类型 waiting_trx_id 正在等待的事务ID waiting_trx_started 等待事务开始的时间
        #waiting_trx_age 已经等待事务多长时间 waiting_trx_rows_locked 正在等待的事务被锁的行数量 waiting_trx_rows_modified 正在等待行重定义的数量
        #waiting_pid 正在等待事务的线程id waiting_query 正在等待锁的查询 waiting_lock_id 正在等待锁的ID waiting_lock_mode 等待锁的模式
        #blocking_trx_id 阻塞等待锁的事务id blocking_pid 正在锁的线程id blocking_query 正在锁的查询 blocking_lock_id 正在阻塞等待锁的锁id.
        #blocking_lock_mode 阻塞锁模式 blocking_trx_started 阻塞事务开始的时间 blocking_trx_age 阻塞的事务已经执行的时间 blocking_trx_rows_locked 阻塞事务锁住的行的数量
        # blocking_trx_rows_modified 阻塞事务重定义行的数量 sql_kill_blocking_query kill 语句杀死正在运行的阻塞事务 sql_kill_blocking_connection kill 语句杀死会话中正在运行的阻塞事务
        query = """SELECT wait_started,wait_age,locked_table,locked_index,locked_type,waiting_query,waiting_lock_mode,blocking_query,blocking_lock_mode
                    FROM sys.innodb_lock_waits"""
        style = {1: 'wait_start,l', 2: 'wait_age,r', 3: 'locked_table,r', 4: 'locked_index,l', 5: 'locked_type,l',
                 6: 'waiting_query,l', 7: 'wt_lk_md,l', 8: 'blocking_query,l',9: 'bk_lk_md,l'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "memory_by_host_by_current_bytes") == 'ON' and sys_schema_exist and not "5.6" in mysql_version:
        title = "memory_by_host_by_current_bytes"
        query = """SELECT HOST,current_count_used,current_allocated,current_avg_alloc,current_max_alloc,total_allocated
                    FROM sys.memory_by_host_by_current_bytes"""
        style = {1: 'HOST,l', 2: 'crt_count_used,r', 3: 'crt_allocatedc,r',4: 'crt_avg_alloc,r', 5: 'crt_max_alloc,r',6: 'tal_alloc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "memory_by_thread_by_current_bytes") == 'ON' and sys_schema_exist and not "5.6" in mysql_version:
        title = "memory_by_thread_by_current_bytes"
        query = """SELECT thread_id,USER,current_count_used,current_allocated,current_avg_alloc,current_max_alloc,total_allocated
                    FROM sys.memory_by_thread_by_current_bytes ORDER BY thread_id"""
        style = {1: 'thread_id,r', 2: 'USER,l', 3: 'crt_count_used,r', 4: 'crt_allocatedc,r',5: 'crt_avg_alloc,r', 6: 'crt_max_alloc,r',7: 'tal_alloc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "memory_by_user_by_current_bytes") == 'ON' and sys_schema_exist  and not "5.6" in mysql_version:
        title = "memory_by_user_by_current_bytes"
        query = """SELECT USER,current_count_used,current_allocated,current_avg_alloc,current_max_alloc,total_allocated
                    FROM sys.memory_by_user_by_current_bytes"""
        style = {1: 'USER,l', 2: 'crt_count_used,r', 3: 'crt_alloc,r',4: 'crt_avg_alloc,r', 5: 'crt_max_alloc,r',6: 'tal_alloc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "memory_global_by_current_bytes") == 'ON' and sys_schema_exist  and not "5.6" in mysql_version:
        title = "memory_global_by_current_bytes"
        query = """SELECT event_name,current_count,current_alloc,current_avg_alloc,high_count,high_alloc,high_avg_alloc
                    FROM sys.memory_global_by_current_bytes ORDER BY current_alloc DESC"""
        style = {1: 'event_name,l', 2: 'crt_count,r', 3: 'crt_alloc,r',4: 'crt_avg_alloc,r', 5: 'high_count,r',6: 'high_alloc,r',7: 'high_avg_alloc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "memory_global_total") == 'ON' and sys_schema_exist  and not "5.6" in mysql_version:
        title = "memory_global_total"
        query = """SELECT total_allocated FROM sys.memory_global_total"""
        style = {1: 'total_allocated,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "processlist" ) == 'ON' and sys_schema_exist:
        title = "processlist"
        query = """SELECT thd_id,USER,command,TIME,current_statement,statement_latency,full_scan,last_statement,last_statement_latency
                    FROM sys.processlist
                    where db='""" + dbinfo[3] + "'"
        style = {1: 'thd_id,r', 2: 'USER,l', 3: 'command,r', 4:'TIME,r', 5: 'current_sql,r',6: 'sql_ltc,r',
                 7: 'fscan,r',8: 'last_sql,r',9: 'lsql_ltc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "session" ) == 'ON' and sys_schema_exist:
        title = "session"
        query = """SELECT thd_id,USER,command,TIME,current_statement,statement_latency,lock_latency,full_scan,last_statement,last_statement_latency
                    FROM sys.session
                    where db='""" + dbinfo[3] + "'"
        style = {1: 'thd_id,r', 2: 'USER,l', 3: 'command,r', 4:'TIME,r', 5: 'current_sql,r',6: 'sql_ltc,r',
                 7: 'lock_ltc,r',8: 'fscan,r',9: 'last_sql,r',10: 'lsql_ltc,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "metrics" ) == 'ON' and sys_schema_exist:
        title = "metrics"
        query = """SELECT Variable_name,Variable_value,TYPE,Enabled
                    FROM sys.metrics
                    WHERE Variable_name!='rsa_public_key'  and Variable_name!='ssl_cipher_list' and Enabled='YES'"""
        style = {1: 'Variable_name,l', 2: 'Variable_value,r', 3: 'TYPE,l', 4:'Enabled,r'}
        f_print_query_table(conn, title, query, style,save_as)

    conn.close()
    f_print_ending(save_as)