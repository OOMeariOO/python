# -*- coding:utf-8 -*-
import sys
import os
import psycopg2
import time
import commands

prefixdir = '/ETL/work'
DIRDELI = '/'
PGTABLE = 'dss_pstat.etl_bak_recv_task_stat'
DB = sys.argv[1]
USER = sys.argv[2]
PASSWD = sys.argv[3]
HOST = sys.argv[4]
PORT = int(sys.argv[5])
filenamelist = sys.argv[6]
hdfsdirlist = sys.argv[7]
task_id = int(sys.argv[8])
etl_host = sys.argv[9]
# DB = 'DW_DATA'
# USER = 'sys_etl_batch'
# PASSWD = 'anquandiyi'
# HOST = '10.5.30.1'
# PORT = 5432
# filenamelist = ['/ETL/DATA/prod_data/midt/all_midt/201607/ttl_all_midt_20160701_20160710.Z',
#                 '/ETL/DATA/prod_data/midt/all_midt/201607/ttl_all_midt_20160711_20160720.Z',
#                 '/ETL/DATA/prod_data/midt/all_midt/201608/*']
# hdfsdirlist = ['/data/GP/ETL_BAK/10.6.142.38/ETL/DATA/prod_data/midt/all_midt/201607.1499159280',
#                '/data/GP/ETL_BAK/10.6.142.38/ETL/DATA/prod_data/midt/all_midt/201607.1499159280',
#                '/data/GP/ETL_BAK/10.6.142.38/ETL/DATA/prod_data/midt/all_midt/201608.1499159315']
# task_id = 1
# etl_host =  '10.6.142.38'
ISOTIMEFORMAT = '%Y-%m-%d %X'
nodate = time.strftime('%Y%m%d', time.localtime(time.time()))
logfiledir = '/ETL/LOG/MAN/%s' % nodate
logfile = 'ETL_COMP_DEL_%s.log' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))


def nowtime():
    return time.strftime(ISOTIMEFORMAT, time.localtime(time.time()))


def myprinttodouble(message):
    print message
    with open(logfiledir + DIRDELI + logfile, "a+") as f:
        f.write(message)
        f.write('\n')
        f.close()


def myprinttofile(message):
    with open(logfiledir + DIRDELI + logfile, "a+") as f:
        f.write(message)
        f.write('\n')
        f.close()


def updatepgdata(task_id, status, error_message='null'):
    conn = ''
    cur = ''
    try:
        conn = psycopg2.connect(database=DB, user=USER, password=PASSWD, host=HOST, port=PORT)
        cur = conn.cursor()
    except Exception, e:
        myprinttodouble('[%s] connect pg fail!' % nowtime())
        myprinttodouble(str((Exception, ':', nowtime(), e)))
        os._exit(-1)
    try:
        cur.execute('UPDATE %s SET exec_stat = %s, error_comment = %s WHERE task_id = %d' % (PGTABLE, status,
                                                                                             error_message, task_id))
        conn.commit()
    except Exception, e:
        myprinttodouble('[%s] update data fail!' % nowtime())
        myprinttodouble(str((Exception, ':', nowtime(), e)))
        os._exit(-1)
    finally:
        cur.close()
        conn.close()


def main(filename, hdfsdir, sourcedir):
    localdir = prefixdir + sourcedir
    if os.path.exists(localdir):
        pass
    else:
        os.system('mkdir -p %s' % localdir)
    if filename == '*':
        (status, output) = commands.getstatusoutput('hdfs dfs -get %s/* %s' % (hdfsdir, localdir))
        if status == 0 and output == '':
            myprinttofile('[%s] get file success!' % nowtime())
        else:
            myprinttodouble('[%s] get file fail!' % nowtime())
            myprinttodouble(output)
            return output
    else:
        (status, output) = commands.getstatusoutput('hdfs dfs -get %s/%s %s' % (hdfsdir, filename, localdir))
        if status == 0 and output == '':
            myprinttofile('[%s] get file success!' % nowtime())
        else:
            myprinttodouble('[%s] get file fail!' % nowtime())
            myprinttodouble(output)
            return output


if __name__ == '__main__':
    error_command = ''
    all_error_command = ''
    count = len(filenamelist)
    sys.path.append('/usr/java/jdk1.7.0_67-cloudera/bin')
    os.environ['HADOOP_USER_NAME'] = 'BDATA_GP_ADM'
    PATH = os.environ['PATH']
    os.environ['PATH'] = '/usr/java/jdk1.7.0_67-cloudera/bin:%s' % PATH
    os.environ['JAVA_HOME'] = '/usr/java/jdk1.7.0_67-cloudera'
    if os.path.exists(logfiledir):
        pass
    else:
        os.system('mkdir -p %s' % logfiledir)
    for i in range(count):
        filenamedir = filenamelist[i]
        filename = filenamedir.split('/')[-1]
        hdfsdir = hdfsdirlist[i]
        sourcefiledir = hdfsdir.split('/data/GP/ETL_BAK/%s' % etl_host)[1][:-11]
        error_command = main(filename, hdfsdir, sourcefiledir)
        if error_command is None:
            pass
        else:
            all_error_command += error_command
    all_error_command = "'" + all_error_command.replace("'", "''") + "'"
    print all_error_command
    if all_error_command == '':
        stat = "'SUCCESS'"
        updatepgdata(task_id, stat)
    else:
        stat = "'FAILURE'"
        updatepgdata(task_id, stat, all_error_command)
