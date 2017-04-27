#!/usr/local/bin/python
# coding: utf-8
import datetime
import getopt
import sys
import string
import pprint
from warnings import filterwarnings
import MySQLdb
import ConfigParser
import math
import time
import psutil
import os

filterwarnings('ignore', category = MySQLdb.Warning)

tab1="+"
tab2="-"
tab3="|"
tab4="="
tab5="*"
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
    except MySQLdb.Error, e:
        print "Error %d: %s" % (e.args[0], e.args[1])
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
    print
    print ((linesize-4)/2 - int(len(title) / 2)) * tab4, title, ((linesize-4)/2+1 - int(len(title) / 2)) * tab4
    print

def f_print_table_line(style):
    for k in style.keys():
        v = style[k]
        print tab1,
        print int(v.split(',')[1]) * tab2,
    print tab1

def f_print_table_head(style):
    for k in style.keys():
        v = style[k]
        print tab3,
        print v.split(',')[0].center(int(v.split(',')[1])),
    print tab3

def f_print_table_body(rows, style,tab):
    for row in rows:
        k = 0
        for col in row:
            k += 1
            print tab,
            if style[k].split(',')[2] == 'l':
                print str(col).ljust(int(style[k].split(',')[1])),
            elif style[k].split(',')[2] == 'r':
                print str(col).rjust(int(style[k].split(',')[1])),
            else:
                print str(col).center(int(style[k].split(',')[1])),
        print tab

def f_print_table_html(rows, title, style):
    print """<p /><h3 class="awr"><a class="awr" name="99999"></a>""" + title + "</h3><p />"
    print """<table border="1">"""

    print """<tr>""",
    for k in style.keys():
        v = style[k]
        print """<th class="awrbg">""",
        print v.split(',')[0],
        print """</th>""",
    print """</tr>"""

    linenum = 0
    for row in rows:
        k = 0
        linenum += 1
        print "<tr>",
        if linenum % 2 == 0:
            classs='awrc'
        else:
            classs='awrnc'

        for col in row:
            k += 1
            if style[k].split(',')[2] == 'r':
                print """<td align="right" class='"""+classs+"'>"+str(col)+"</td>",
            else:
                print """<td class='"""+classs+"'>"+str(col)+"</td>",
        print "</tr>"
    print """</table>
<br /><a class="awr" href="#top">Back to Top</a>
<p />
<p />
        """

def f_print_table(rows,title,style,save_as):
    if save_as == "txt":
        f_print_title(title)
        f_print_table_line(style)
        f_print_table_head(style)
        f_print_table_line(style)
        f_print_table_body(rows, style, tab3)
        f_print_table_line(style)
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
    style = {1: 'switch_name,40,l', 2: 'value,10,r'}
    rows =[]
    query="select variable_value from "+perfor_or_infor+".global_variables where variable_name='optimizer_switch'"
    recode = f_get_query_record(conn, query)
    for col in recode[0][0].split(','):
        rows.append([col.split('=')[0],col.split('=')[1]])
    f_print_table(rows, title, style,save_as)

def f_print_caption(dbinfo,mysql_version,save_as):
    if save_as == "txt":
        print tab5 * linesize
        print tab5, 'MySQL Watcher  V1.0'.center(linesize - 4), tab5
        print tab5, 'Kinghow@hotmail.com'.center(linesize - 4), tab5
        print tab5 * linesize
    elif save_as == "html":
        print """
<html><head><title>MySQL Watcher  V1.0  Kinghow@hotmail.com </title>
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
       """

    title = "Basic Information"
    style = {1: 'host,15,c', 2: 'user,15,c', 3: 'db,20,c', 4: 'mysql version,41,c'}
    rows = [[dbinfo[0], dbinfo[1], dbinfo[3], mysql_version]]
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
    style = {1: '&nbsp;,6,l', 2: '&nbsp;,10,r',3: '&nbsp;,6,l', 4: '&nbsp;,10,r',5: '&nbsp;,6,l', 6: '&nbsp;,6,r',7: '&nbsp;,8,l',8: '&nbsp;,6,r',9: '&nbsp;,6,l', 10: '&nbsp;,6,r',11: '&nbsp;,6,l', 12: '&nbsp;,5,r',}
    rows=[
          ["CPU", str(psutil.cpu_percent(interval=1))+'%',"nice", cpu_times.nice,"MEM", str(mem.percent) + '%',"active", str(mem.active/1024/1024) + 'M',"SWAP", str(swap.percent)+'%',"LOAD", str(psutil.cpu_count())+'core'],
          ["user", cpu_times.user,"irq", cpu_times.irq,"total", str(mem.total/1024/1024)+'M',"inactive", str(mem.inactive/1024/1024) + 'M',"total", str(swap.total/1024/1024) + 'M',"1 min", stats["min1"]],
          ["system", cpu_times.system,"iowait", cpu_times.iowait,"used", str(mem.used/1024/1024)+'M',"buffers", str(mem.buffers/1024/1024) + 'M',"used", str(swap.used/1024/1024) + 'M',"5 min", stats["min5"]],
          ["idle", cpu_times.idle,"steal", cpu_times.steal,"free", str(mem.free/1024/1024) + 'M',"cached", str(mem.cached/1024/1024) + 'M',"free", str(swap.free/1024/1024) + 'M',"15 min", stats["min15"]]
         ]

    title = "Linux Overview"
    if save_as == "txt":
        f_print_title(title)
        f_print_table_body(rows, style,' ')
    elif save_as == "html":
        f_print_table_html(rows, title, style)

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

def f_print_mysql_status(conn,interval,save_as):
    ###获取参数###################################################################
    mysqlstatus1 = f_get_mysql_status(conn)
    time.sleep(interval)
    mysqlstatus2 = f_get_mysql_status(conn)

    # 执行查询的总次数
    Questions1 = long(mysqlstatus1["Questions"])
    Questions2 = long(mysqlstatus2["Questions"])
    # 服务器已经运行的时间（以秒为单位）
    Uptime2 = long(mysqlstatus2["Uptime"])
    Com_commit1 = long(mysqlstatus1["Com_commit"])
    Com_commit2 = long(mysqlstatus2["Com_commit"])
    Com_rollback1 = long(mysqlstatus1["Com_rollback"])
    Com_rollback2 = long(mysqlstatus2["Com_rollback"])
    # 从硬盘读取键的数据块的次数。如果Key_reads较大，则Key_buffer_size值可能太小。
    # 可以用Key_reads/Key_read_requests计算缓存损失率
    Key_reads1 = long(mysqlstatus1["Key_reads"])
    Key_reads2 = long(mysqlstatus2["Key_reads"])
    # 从缓存读键的数据块的请求数
    Key_read_requests1 = long(mysqlstatus1["Key_read_requests"])
    Key_read_requests2 = long(mysqlstatus2["Key_read_requests"])
    # 向硬盘写入将键的数据块的物理写操作的次数
    Key_writes1 = long(mysqlstatus1["Key_writes"])
    Key_writes2 = long(mysqlstatus2["Key_writes"])
    # 将键的数据块写入缓存的请求数
    Key_write_requests1 = long(mysqlstatus1["Key_write_requests"])
    Key_write_requests2 = long(mysqlstatus2["Key_write_requests"])
    # 不能满足InnoDB必须单页读取的缓冲池中的逻辑读数量。
    Innodb_buffer_pool_reads1 = long(mysqlstatus1["Innodb_buffer_pool_reads"])
    Innodb_buffer_pool_reads2 = long(mysqlstatus2["Innodb_buffer_pool_reads"])
    # InnoDB已经完成的逻辑读请求数
    Innodb_buffer_pool_read_requests1 = long(mysqlstatus1["Innodb_buffer_pool_read_requests"])
    Innodb_buffer_pool_read_requests2 = long(mysqlstatus2["Innodb_buffer_pool_read_requests"])
    # 查询缓存被访问的次数
    Qcache_hits1 = long(mysqlstatus1["Qcache_hits"])
    Qcache_hits2 = long(mysqlstatus2["Qcache_hits"])
    # 加入到缓存的查询数量，缓存没有用到
    Qcache_inserts1 = long(mysqlstatus1["Qcache_inserts"])
    Qcache_inserts2 = long(mysqlstatus2["Qcache_inserts"])
    # 当前打开的表的数量
    Open_tables1 = long(mysqlstatus2["Open_tables"])-long(mysqlstatus1["Open_tables"])
    Open_tables2 = long(mysqlstatus2["Open_tables"])
    # 已经打开的表的数量。如果Opened_tables较大，table_cache 值可能太小
    Opened_tables1 = long(mysqlstatus2["Opened_tables"])-long(mysqlstatus1["Opened_tables"])
    Opened_tables2 = long(mysqlstatus2["Opened_tables"])
    # 创建用来处理连接的线程数。如果Threads_created较大，你可能要
    # 增加thread_cache_size值。缓存访问率的计算方法Threads_created/Connections
    Threads_created1 = long(mysqlstatus1["Threads_created"])
    Threads_created2 = long(mysqlstatus2["Threads_created"])
    # 试图连接到(不管是否成功)MySQL服务器的连接数。缓存访问率的计算方法Threads_created/Connections
    Connections1 = long(mysqlstatus1["Connections"])
    Connections2 = long(mysqlstatus2["Connections"])
    Threads_connected1 = str(long(mysqlstatus2["Threads_connected"])-long(mysqlstatus1["Threads_connected"]))
    Threads_connected2 = mysqlstatus2["Threads_connected"]
    Aborted_connects1 = str(long(mysqlstatus2["Aborted_connects"])-long(mysqlstatus1["Aborted_connects"]))
    Aborted_connects2 = mysqlstatus2["Aborted_connects"]
    # Com_select/s：平均每秒select语句执行次数
    # Com_insert/s：平均每秒insert语句执行次数
    # Com_update/s：平均每秒update语句执行次数
    # Com_delete/s：平均每秒delete语句执行次数
    Com_select1 = long(mysqlstatus1["Com_select"])
    Com_select2 = long(mysqlstatus2["Com_select"])
    Com_insert1 = long(mysqlstatus1["Com_insert"])
    Com_insert2 = long(mysqlstatus2["Com_insert"])
    Com_update1 = long(mysqlstatus1["Com_update"])
    Com_update2 = long(mysqlstatus2["Com_update"])
    Com_delete1 = long(mysqlstatus1["Com_delete"])
    Com_delete2 = long(mysqlstatus2["Com_delete"])
    Com_replace1 = long(mysqlstatus1["Com_replace"])
    Com_replace2 = long(mysqlstatus2["Com_replace"])
    # 不能立即获得的表的锁的次数。如果该值较高，并且有性能问题，你应首先优化查询，然后拆分表或使用复制。
    Table_locks_waited1 = long(mysqlstatus1["Table_locks_waited"])
    Table_locks_waited2 = long(mysqlstatus2["Table_locks_waited"])
    # 立即获得的表的锁的次数
    Table_locks_immediate1 = long(mysqlstatus1["Table_locks_immediate"])
    Table_locks_immediate2 = long(mysqlstatus2["Table_locks_immediate"])
    # 服务器执行语句时自动创建的内存中的临时表的数量。如果Created_tmp_disk_tables较大，
    # 你可能要增加tmp_table_size值使临时 表基于内存而不基于硬盘
    Created_tmp_tables1 = long(mysqlstatus1["Created_tmp_tables"])
    Created_tmp_tables2 = long(mysqlstatus2["Created_tmp_tables"])
    # 服务器执行语句时在硬盘上自动创建的临时表的数量
    Created_tmp_disk_tables1 = long(mysqlstatus1["Created_tmp_disk_tables"])
    Created_tmp_disk_tables2 = long(mysqlstatus2["Created_tmp_disk_tables"])
    # 查询时间超过long_query_time秒的查询的个数 缓慢查询个数
    Slow_queries1 = long(mysqlstatus1["Slow_queries"])
    Slow_queries2 = long(mysqlstatus2["Slow_queries"])
    # 没有主键（key）联合（Join）的执行。该值可能是零。这是捕获开发错误的好方法，因为一些这样的查询可能降低系统的性能。
    Select_full_join1 = long(mysqlstatus1["Select_full_join"])
    Select_full_join2 = long(mysqlstatus2["Select_full_join"])
    #  Percentage of full table scans
    Handler_read_rnd_next1 = long(mysqlstatus1["Handler_read_rnd_next"])
    Handler_read_rnd_next2 = long(mysqlstatus2["Handler_read_rnd_next"])
    Handler_read_rnd1 = long(mysqlstatus1["Handler_read_rnd"])
    Handler_read_rnd2 = long(mysqlstatus2["Handler_read_rnd"])
    Handler_read_first1 = long(mysqlstatus1["Handler_read_first"])
    Handler_read_first2 = long(mysqlstatus2["Handler_read_first"])
    Handler_read_next1 = long(mysqlstatus1["Handler_read_next"])
    Handler_read_next2 = long(mysqlstatus2["Handler_read_next"])
    Handler_read_key1 = long(mysqlstatus1["Handler_read_key"])
    Handler_read_key2 = long(mysqlstatus2["Handler_read_key"])
    Handler_read_prev1 = long(mysqlstatus1["Handler_read_prev"])
    Handler_read_prev2 = long(mysqlstatus2["Handler_read_prev"])
    # 缓冲池利用率
    Innodb_buffer_pool_pages_total1 = long(mysqlstatus1["Innodb_buffer_pool_pages_total"])
    Innodb_buffer_pool_pages_total2 = long(mysqlstatus2["Innodb_buffer_pool_pages_total"])
    Innodb_buffer_pool_pages_free1 = long(mysqlstatus1["Innodb_buffer_pool_pages_free"])
    Innodb_buffer_pool_pages_free2 = long(mysqlstatus2["Innodb_buffer_pool_pages_free"])

    ###计算参数###################################################################
    Uptimes1 = str(interval) + "s"
    Uptimes2 = f_sec2dhms(Uptime2)
    # QPS = Questions / Seconds
    QPS1 = str(round((Questions2-Questions1) * 1.0 / interval, 2))
    QPS2 = str(round(Questions2* 1.0 / Uptime2, 2))

    TPS1 = str(round((Com_commit2 + Com_rollback2-Com_commit1 - Com_rollback1) * 1.0 / interval, 2))
    TPS2 = str(round((Com_commit2 + Com_rollback2)* 1.0 / Uptime2, 2))

    Read1 = Com_select2 + Qcache_hits2-Com_select1 - Qcache_hits1
    Read2 = Com_select2 + Qcache_hits2
    ReadS1 = str(round(Read1 * 1.0 / interval, 2))
    ReadS2 = str(round(Read2* 1.0 / Uptime2, 2))

    Write1 = Com_insert2 + Com_update2 + Com_delete2 + Com_replace2-Com_insert1 - Com_update1 - Com_delete1 - Com_replace1
    Write2 = Com_insert2 + Com_update2 + Com_delete2 + Com_replace2
    WriteS1 = str(round(Write1 * 1.0 / interval, 2))
    WriteS2 = str(round(Write2* 1.0 / Uptime2, 2))
    # Read/Write Ratio
    if Write1<>0:
        rwr1 = str(round(Read1 * 1.0 / Write1,2))
    else:
        rwr1 ='0.0%'

    if Write2<>0:
        rwr2 = str(round(Read2 * 1.0 / Write2,2))
    else:
        rwr2 ='0.0%'

    Slow_queries_per_second1 = str(round((Slow_queries2-Slow_queries1) * 1.0 / interval, 2))
    Slow_queries_per_second2 = str(round(Slow_queries2 * 1.0 / Uptime2, 2))
    #Slow_queries / Questions
    SQ1 = str(round(((Slow_queries2-Slow_queries1) * 1.0 / (Questions2-Questions1)) * 100, 2)) + "%"
    SQ2 = str(round((Slow_queries2 * 1.0 / Questions2) * 100, 2)) + "%"

    if (Connections2-Connections1) <> 0:
        Thread_cache_hits1 = str(round((1 - (Threads_created2-Threads_created1)* 1.0 / (Connections2-Connections1)) * 100, 2)) + "%"
    else:
        Thread_cache_hits1 = '0.0%'
    Thread_cache_hits2 = str(round((1 - Threads_created2 * 1.0 / Connections2) * 100, 2)) + "%"

    if (Innodb_buffer_pool_read_requests2-Innodb_buffer_pool_read_requests1) <> 0:
        Innodb_buffer_read_hits1 = str(round((1 - (Innodb_buffer_pool_reads2-Innodb_buffer_pool_reads1) * 1.0 / (Innodb_buffer_pool_read_requests2-Innodb_buffer_pool_read_requests1)) * 100, 2)) + "%"
    else:
        Innodb_buffer_read_hits1 = '0.0%'
    Innodb_buffer_read_hits2 = str(round((1 - Innodb_buffer_pool_reads2* 1.0 / Innodb_buffer_pool_read_requests2) * 100, 2)) + "%"

    Innodb_buffer_pool_utilization1 = str(round((Innodb_buffer_pool_pages_total1 - Innodb_buffer_pool_pages_free1) * 1.0 / Innodb_buffer_pool_pages_total1 * 100,2)) + "%"
    Innodb_buffer_pool_utilization2 = str(round((Innodb_buffer_pool_pages_total2 - Innodb_buffer_pool_pages_free2) * 1.0 / Innodb_buffer_pool_pages_total2 * 100,2)) + "%"

    if (Key_read_requests2-Key_read_requests1) <> 0:
        Key_buffer_read_hits1 = str(round((1 - (Key_reads2-Key_reads1) * 1.0 / (Key_read_requests2-Key_read_requests1)) * 100, 2)) + "%"
    else:
        Key_buffer_read_hits1 = '0.0%'
    if Key_read_requests2 <> 0:
        Key_buffer_read_hits2 = str(round((1 - Key_reads2* 1.0 / Key_read_requests2) * 100, 2)) + "%"
    else:
        Key_buffer_read_hits2 = '0.0%'

    if (Key_write_requests2-Key_write_requests1)<>0:
        Key_buffer_write_hits1 = str(round((1 - (Key_writes2-Key_writes1)* 1.0 / (Key_write_requests2-Key_write_requests1)) * 100, 2)) + "%"
    else:
        Key_buffer_write_hits1 = '0.0%'
    if Key_write_requests2<>0:
        Key_buffer_write_hits2 = str(round((1 - Key_writes2* 1.0 / Key_write_requests2) * 100, 2)) + "%"
    else:
        Key_buffer_write_hits2 = '0.0%'

    if (Qcache_hits2 + Qcache_inserts2-Qcache_hits1 - Qcache_inserts1) > 0:
        Query_cache_hits1 = str(round((((Qcache_hits2-Qcache_hits1)* 1.0 / (Qcache_hits2 + Qcache_inserts2-Qcache_hits1 - Qcache_inserts1)) * 100), 2)) + "%"
    else:
        Query_cache_hits1 = '0.0%'
    if (Qcache_hits2 + Qcache_inserts2) > 0:
        Query_cache_hits2 = str(round(((Qcache_hits2* 1.0 / (Qcache_hits2 + Qcache_inserts2)) * 100), 2)) + "%"
    else:
        Query_cache_hits2 = '0.0%'

    if (Select_full_join2-Select_full_join1) > 0:
        Select_full_join_per_second1 = str(round((Select_full_join2-Select_full_join1) * 1.0 / interval, 2))
    else:
        Select_full_join_per_second1 = '0.0%'
    Select_full_join_per_second2 = str(round(Select_full_join2 * 1.0 / Uptime2, 2))

    if (Com_select2-Com_select1) > 0:
        full_select_in_all_select1 = str(round(((Select_full_join2-Select_full_join1) * 1.0 / (Com_select2-Com_select1)) * 100, 2)) + "%"
    else:
        full_select_in_all_select1 = '0.0%'
    full_select_in_all_select2 = str(round((Select_full_join2 * 1.0 / Com_select2) * 100, 2)) + "%"

    #((Handler_read_rnd_next + Handler_read_rnd) / (Handler_read_rnd_next + Handler_read_rnd + Handler_read_first + Handler_read_next + Handler_read_key + Handler_read_prev)).
    if (Handler_read_rnd_next2 -Handler_read_rnd_next1+ Handler_read_rnd2-Handler_read_rnd1 + Handler_read_first2 -Handler_read_first1+ Handler_read_next2-Handler_read_next1 + Handler_read_key2-Handler_read_key2 + Handler_read_prev2-Handler_read_prev1) > 0:
        full_table_scans1=str(round((Handler_read_rnd_next2 + Handler_read_rnd2-Handler_read_rnd_next1 - Handler_read_rnd1)* 1.0 / (Handler_read_rnd_next2 -Handler_read_rnd_next1+ Handler_read_rnd2-Handler_read_rnd1 + Handler_read_first2 -Handler_read_first1+ Handler_read_next2-Handler_read_next1 + Handler_read_key2-Handler_read_key2 + Handler_read_prev2-Handler_read_prev1)* 100, 2)) + "%"
    else:
        full_table_scans1 = '0.0%'
    full_table_scans2=str(round((Handler_read_rnd_next2 + Handler_read_rnd2)* 1.0 / (Handler_read_rnd_next2 + Handler_read_rnd2 + Handler_read_first2 + Handler_read_next2 + Handler_read_key2 + Handler_read_prev2)* 100, 2)) + "%"

    if (Table_locks_immediate2-Table_locks_immediate1) > 0:
        lock_contention1 = str(round(((Table_locks_waited2-Table_locks_waited1) * 1.00 / (Table_locks_immediate2-Table_locks_immediate1)) * 100, 2)) + "%"
    else:
        lock_contention1 = '0.0%'
    lock_contention2 = str(round((Table_locks_waited2 * 1.00 / Table_locks_immediate2) * 100, 2)) + "%"

    if (Created_tmp_tables2-Created_tmp_tables1) > 0:
        Temp_tables_to_disk1 = str(round(((Created_tmp_disk_tables2-Created_tmp_disk_tables1) * 1.0 / (Created_tmp_tables2-Created_tmp_tables1)) * 100, 2)) + "%"
    else:
        Temp_tables_to_disk1 = '0.0%'
    Temp_tables_to_disk2 = str(round((Created_tmp_disk_tables2 * 1.0 / Created_tmp_tables2) * 100, 2)) + "%"

    ###打印参数###################################################################
    title = "MySQL Overview"
    style = {1: 'Key,40,l', 2: 'In '+Uptimes1+',20,r', 3: 'Total,20,r'}
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
          ["Key buffer read hits(99.3% - 99.9%)",str(Key_buffer_read_hits1), str(Key_buffer_read_hits2)],
          ["Key buffer write hits(99.3% - 99.9%)", str(Key_buffer_write_hits1), str(Key_buffer_write_hits2)],
          ["Query Cache Hits", Query_cache_hits1, Query_cache_hits2],
          ["Select full join per second", Select_full_join_per_second1, Select_full_join_per_second2],
          ["full select in all select", full_select_in_all_select1, full_select_in_all_select2],
          ["full table scans", full_table_scans1, full_table_scans2],
          ["MyISAM Lock waiting ratio", lock_contention1, lock_contention2],
          ["Current open tables", str(Open_tables1), str(Open_tables2)],
          ["Accumulative open tables", str(Opened_tables1), str(Opened_tables2)],
          ["Temp tables to disk(<10%)", Temp_tables_to_disk1, Temp_tables_to_disk2]
          ]

    f_print_table(rows, title, style,save_as)

if __name__=="__main__":
    dbinfo=["127.0.0.1","root","","mysql",3306] #host,user,passwd,db,port
    config_file=""
    mysql_version=""
    option = []
    save_as = "txt"

    opts, args = getopt.getopt(sys.argv[1:], "p:s:")
    for o,v in opts:
        if o == "-p":
            config_file = v
        elif o == "-s":
            save_as = v

    config = ConfigParser.ConfigParser()
    config.readfp(open(config_file,"rb"))
    dbinfo[0] = config.get("database","host")
    dbinfo[1] = config.get("database","user")
    dbinfo[2] = config.get("database","passwd")
    dbinfo[3] = config.get("database","db")
    dbinfo[4] = config.get("database", "port")
    interval  = long(config.get("option", "interval"))

    conn = f_get_conn(dbinfo)
    query ="select @@version"
    mysql_version = f_get_query_value(conn, query)
    f_print_caption(dbinfo,mysql_version,save_as)

    if "5.7" in mysql_version:
        perfor_or_infor = "performance_schema"
    else:
        perfor_or_infor = "information_schema"
        
    sys_schema_exist = f_is_sys_schema_exist(conn)

    if config.get("option","linux_overview")=='ON':
        f_print_linux_status(save_as)

    if config.get("option","mysql_overview")=='ON':
        f_print_mysql_status(conn,interval,save_as)

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
        style = {1: 'parameter_name,40,l', 2: 'value,30,r'}
        f_print_query_table(conn, title, query, style,save_as)
        f_print_optimizer_switch(conn,save_as,perfor_or_infor)

    if config.get ( "option", "replication" ) == 'ON':
        title = "Replication"
        query = """SELECT USER,HOST,command,CONCAT(FLOOR(TIME/86400),'d',FLOOR(TIME/3600)%24,'h',FLOOR(TIME/60)%60,'m',TIME%60,'s') TIMES,state
                   FROM information_schema.processlist WHERE COMMAND = 'Binlog Dump' OR COMMAND = 'Binlog Dump GTID'"""
        style = {1: 'USER,10,l', 2: 'HOST,20,l', 3: 'command,16,l', 4: 'TIMES,13,r', 5: 'state,61,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "connect_count" ) == 'ON':
        title = "Connect Count"
        query = """SELECT SUBSTRING_INDEX(HOST,':',1) HOSTS,USER,db,command,COUNT(*),SUM(TIME)
                   FROM information_schema.processlist
                   WHERE Command !='' AND DB !='information_schema'
                   GROUP BY HOSTS,USER,db,command"""
        style = {1: 'HOSTS,15,l', 2: 'USER,20,l', 3: 'db,20,l', 4: 'command,7,l', 5: 'COUNT(*),8,r', 6: 'SUM(TIME),9,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "avg_query_time" ) == 'ON' and ("5.7" in mysql_version):
        title = "Avg Query Time"
        query = """SELECT schema_name,SUM(count_star) COUNT, ROUND((SUM(sum_timer_wait)/SUM(count_star))/1000000) avg_microsec
                   FROM performance_schema.events_statements_summary_by_digest
                   WHERE schema_name IS NOT NULL
                   GROUP BY schema_name"""
        style = {1: 'schema_name,30,l', 2: 'COUNT,15,r', 3: 'avg_microsec,15,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "slow_query_top10" ) == 'ON' and sys_schema_exist:
        title = "Slow Query Top10"
        query = "SELECT QUERY,db,exec_count,total_latency,max_latency,avg_latency FROM sys.statements_with_runtimes_in_95th_percentile LIMIT 10"
        style = {1: 'QUERY,70,l', 2: 'db,15,r', 3: 'exec_count,10,r', 4: 'total_latency,13,r', 5: 'max_latency,11,r', 6: 'avg_latency,11,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "err_sql_count" ) == 'ON' and ("5.7" in mysql_version):
        title = "Err Sql Count"
        query = """SELECT schema_name,SUM(sum_errors) err_count
                   FROM performance_schema.events_statements_summary_by_digest
                   WHERE sum_errors > 0
                   GROUP BY schema_name"""
        style = {1: 'schema_name,30,l', 2: 'err_count,15,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "err_sql_top10" ) == 'ON' and sys_schema_exist:
        title = "Err SQL Top10"
        query = "SELECT QUERY,db,exec_count,ERRORS FROM sys.statements_with_errors_or_warnings ORDER BY ERRORS DESC LIMIT 10"
        style = {1: 'QUERY,70,l', 2: 'db,15,r', 3: 'exec_count,10,r', 4: 'ERRORS,10,r'}
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
        style = {1: 'table_schema,30,l', 2: 'Table Size,15,r', 3: 'Index Size,15,r', 4: 'DB Size,15,r'}
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
        style = {1:'object_type,30,l',2: 'COUNT,10,r'}
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
        style = {1: 'table_name,40,l', 2: 'engine,10,l', 3: 'format,10,l', 4: 'table_rows,10,r', 5: 'avg_row,10,r',
                 6: 'data_mb,10,r', 7: 'index_mb,10,r', 8: 'total_mb,10,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get ( "option", "index_info" ) == 'ON':
        title = "Index Info"
        query = """select index_name,non_unique,seq_in_index,column_name,collation,cardinality,nullable,index_type
                   from information_schema.statistics
                   where table_schema='""" + dbinfo[3] + "'"
        style = {1: 'index_name,40,l', 2: 'non_unique,10,l', 3: 'seq_in_index,12,l', 4: 'column_name,30,r',
                 5: 'collation,10,r', 6: 'cardinality,11,r', 7: 'nullable,10,r', 8: 'index_type,10,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "schema_unused_indexes") == 'ON' and sys_schema_exist:
        title = "Schema Unused Indexes"
        query = "SELECT object_schema,object_name,index_name FROM sys.schema_unused_indexes where object_schema='" +  dbinfo[3] + "'"
        style = {1: 'object_schema,30,l', 2: 'object_name,40,l', 3: 'index_name,50,l'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary") == 'ON' and sys_schema_exist:
        title = "host_summary"
        #host 监听连接过的主机 statements 当前主机执行的语句总数 statement_latency 语句等待时间（延迟时间） statement_avg_latency 执行语句平均延迟时间 table_scans 表扫描次数
        #file_ios io时间总数 file_io_latency 文件io延迟 current_connections 当前连接数 total_connections 总链接数 unique_users 该主机的唯一用户数 current_memory 当前账户分配的内存
        #total_memory_allocated 该主机分配的内存总数
        query = """SELECT host,statements,statement_latency,statement_avg_latency,table_scans,file_ios,file_io_latency,current_connections,
                    total_connections,unique_users,current_memory,total_memory_allocated
                    FROM sys.host_summary"""
        style = {1: 'host,15,l', 2: 'statements,10,r', 3: 'st_ltc,10,r', 4: 'st_avg_ltc,10,r', 5: 'table_scan,10,r',
                 6: 'file_ios,10,r', 7: 'f_io_ltc,10,r', 8: 'cur_conns,10,r', 9: 'total_conn,10,r',
                 10: 'unq_users,10,r', 11: 'cur_mem,10,r', 12: 'tal_mem_alc,11,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_file_io_type") == 'ON' and sys_schema_exist:
        title = "host_summary_by_file_io_type"
        #•host 主机 event_name IO事件名称 total 该主机发生的事件 total_latency 该主机发生IO事件总延迟时间 max_latency 该主机IO事件中最大的延迟时间
        query = """SELECT host,event_name,total,total_latency,max_latency
                    FROM sys.host_summary_by_file_io_type"""
        style = {1: 'host,15,l', 2: 'event_name,40,r', 3: 'total,10,r', 4: 'total_ltc,10,r', 5: 'max_ltc,10,r'}
        f_print_query_table(conn, title, query, style,save_as)

    if config.get("option", "host_summary_by_file_io_type") == 'ON' and sys_schema_exist:
        title = "host_summary_by_file_io_type"
        #•host 主机 event_name IO事件名称 total 该主机发生的事件 total_latency 该主机发生IO事件总延迟时间 max_latency 该主机IO事件中最大的延迟时间
        query = """SELECT host,event_name,total,total_latency,max_latency
                    FROM sys.host_summary_by_file_io_type"""
        style = {1: 'host,15,l', 2: 'event_name,40,r', 3: 'total,10,r', 4: 'total_ltc,10,r', 5: 'max_ltc,10,r'}
        f_print_query_table(conn, title, query, style,save_as)
    conn.close()

    if save_as == "txt":
        f_print_title('--@--  End  --@--')
    elif save_as == "html":
        print """
<p />
End of Report
</body></html>
        """




