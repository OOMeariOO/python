#coding: utf-8

# @Author: 米 雷
# @File: datamanagement.py
# @Time: 2017/5/3
# @Contact: 1262585769@qq.com
# @Description: ETL数据仓库中数据的备份和删除程序，把指定目录中的源数据文件和生成文件按一定规则备份删除压缩
#               删除以前先把要删除的文件被分到hdfs上。删除中有一个判断，如果是最近不得数，不删除！

import time
import os
import sys
import commands
from datetime import timedelta, date
import calendar

ETLDIR = 'ETL'
DATADIR = 'DATA'
DIRDELI = '/'
LOGFILEDIR = '/ETL/DATA/meari/DATA/LOG'
TKTERRORDIR = '/ETL/DATA/meari/DATA/fail/tkterror'
BIDTDATADIR = '/ETL/DATA/meari/DATA/prod_data/bidt_data/'
ETLDATAEXE = '/ETL/bin/EtlDate.exe'
SYSTEM = '{{SYSTEMNAME}}'
SYSTEM8DATE = '{{SYSTEMNAME}}/{{YYYYMMDD}}'
SYSTEM6DATE = '{{SYSTEMNAME}}/{{YYYYMM}}'
SYSTEM4DATE = '{{SYSTEMNAME}}/{{YYMM}}'
DATE8 = '{{YYYYMMDD}}'
DATE6 = '{{YYYYMM}}'
DATE4 = '{{YYMM}}'
HDFSDIR = '/data/GP/ETL_BAK'
CONSIDER = 0
configfile = '/ETL/DATA/meari/config.txt'
ISOTIMEFORMAT= '%Y-%m-%d %X'
todaystr = sys.argv[1]

BEFOREYEAR = -12
BEFOREMON = -1
year = todaystr[0:4]
mon = todaystr[4:6]
day = todaystr[6:]


def nowtime():

    return time.strftime( ISOTIMEFORMAT, time.localtime( time.time() ) )

def get_days_of_month(year, mon):
    """
    get days of month
    """
    return calendar.monthrange(year, mon)[1]

def addzero(n):
    """
    add 0 before 0-9
    return 01-09
    """
    nabs = abs(int(n))
    if (nabs < 10):
        return "0" + str(nabs)
    else:
        return nabs

def getyearandmonth(n=0):
    """
    get the year,month,days from today
    befor or after n months
    """
    thisyear = int(year)
    thismon = int(mon)
    totalmon = thismon + n
    if (n >= 0):
        if (totalmon <= 12):
            days = str(get_days_of_month(thisyear, totalmon))
            totalmon = addzero(totalmon)
            return (year, totalmon, days)
        else:
            i = totalmon / 12
            j = totalmon % 12
            if (j == 0):
                i -= 1
                j = 12
            thisyear += i
            days = str(get_days_of_month(thisyear, j))
            j = addzero(j)
            return (str(thisyear), str(j), days)
    else:
        if ((totalmon > 0) and (totalmon < 12)):
            days = str(get_days_of_month(thisyear, totalmon))
            totalmon = addzero(totalmon)
            return (year, totalmon, days)
        else:
            i = totalmon / 12
            j = totalmon % 12
            if (j == 0):
                i -= 1
                j = 12
            thisyear += i
            days = str(get_days_of_month(thisyear, j))
            j = addzero(j)
            return (str(thisyear), str(j), days)

def get_day_of_day(n=0):
    """
    if n>=0,date is larger than today
    if n<0,date is less than today
    date format = "YYYY-MM-DD"
    """
    if (n < 0):
        n = abs(n)
        return (date.today() - timedelta(days=n)).strftime("%Y%m%d")
    else:
        return (date.today() + timedelta(days=n)).strftime("%Y%m%d")

def get_today_month(n=0):
    """
    获取当前日期前后N月的日期
    if n>0, 获取当前日期前N月的日期
    if n<0, 获取当前日期后N月的日期
    date format = "YYYY-MM-DD"
    """
    (y, m, d) = getyearandmonth(n)
    arr = (y, m, d)
    if (int(day) < int(d)):
        arr = (y, m, day)
    return "".join("%s" % i for i in arr)

def BeforeDate(todaystr, Offset):
    return os.popen("%s %s -%s" % (ETLDATAEXE, todaystr, Offset)).read().strip('\n')


def havesystemname(line):
    dirpath = line.split(SYSTEM)[0]
    befordays = line.split(',')[1]
    gzipddays = line.split(',')[2]
    switchs = line.split(',')[3]
    dirlist = os.listdir(dirpath)
    gzipbegindate = get_day_of_day(-int(gzipddays))
    deletedate = BeforeDate(todaystr, befordays)

    if 'MetaDataLogBk' in dirlist:
        dirlist.remove('MetaDataLogBk')
        print '[' + nowtime() + '] ' + 'MetaDataLogBk目录不作处理'
    for systemname in dirlist:
        if os.path.isdir(dirpath + systemname):
            datedirlist = os.listdir(dirpath + systemname)
            for datedir in datedirlist:
                if os.path.isdir(dirpath + systemname + DIRDELI + datedir):

                    if datedir.isdigit() and len(datedir) == 8:
                        if (int(datedir) > int(deletedate)) and (int(datedir) <= int(gzipbegindate)):
                            filedirlist = os.listdir(dirpath + systemname + DIRDELI + datedir)
                            for files in filedirlist:
                                filename = dirpath + systemname + DIRDELI + datedir + DIRDELI + files
                                if os.path.isfile('%s' % filename):
                                    if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                                        pass
                                    else:
                                        (status, output) = commands.getstatusoutput('gzip %s' % filename)
                                        if status == 0 and output == '':
                                            print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                                        else:
                                            print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
                        elif int(datedir) <= int(deletedate):
                            deletepath = dirpath + systemname + DIRDELI + datedir
                            mkdirdeletepath = dirpath + systemname + DIRDELI
                            if int(switchs) == CONSIDER:
                                t = os.stat(deletepath)[8]
                                t = float(t)
                                t = time.strftime('%Y%m%d', time.gmtime(t))
                            else:
                                t = datedir
                            if int(t) > int(deletedate):
                                pass
                            elif int(t) <= int(deletedate):
                                commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                                commands.getstatusoutput('hdfs dfs -mkdir %s%s'%(HDFSDIR, deletepath))
                                hdfsdir = '%s%s'%(HDFSDIR, mkdirdeletepath)
                                commands.getstatusoutput('hdfs dfs -put %s %s'%(deletepath, hdfsdir))
                                (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                                if status == 0 and output == '':
                                    print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                                else:
                                    print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
                        else:
                            print '[' + nowtime() + '] ' + dirpath + systemname + DIRDELI + datedir + '暂时不压缩或者删除！'
                    elif datedir.isdigit() and len(datedir) == 6:
                        deletedate = deletedate[0:6]
                        gzipbegindate = gzipbegindate[0:6]
                        if (int(datedir) > int(deletedate)) and (int(datedir) <= int(gzipbegindate)):
                            filedirlist = os.listdir(dirpath + systemname + DIRDELI + datedir)
                            for files in filedirlist:
                                filename = dirpath + systemname + DIRDELI + datedir + DIRDELI + files
                                if os.path.isfile('%s' % filename):
                                    if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                                        pass
                                    else:
                                        (status, output) = commands.getstatusoutput('gzip %s' % filename)
                                        if status == 0 and output == '':
                                            print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                                        else:
                                            print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
                        elif int(datedir) <= int(deletedate):
                            deletepath = dirpath + systemname + DIRDELI + datedir
                            mkdirdeletepath = dirpath + systemname + DIRDELI
                            if int(switchs) == CONSIDER:
                                t = os.stat(deletepath)[8]
                                t = float(t)
                                t = time.strftime('%Y%m%d', time.gmtime(t))[0:6]
                            else:
                                t = datedir
                            if int(t) > int(deletedate):
                                pass
                            elif int(t) <= int(deletedate):
                                commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                                commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                                hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                                commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                                (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                                if status == 0 and output == '':
                                    print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                                else:
                                    print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
                        else:
                            print '[' + nowtime() + '] ' + dirpath + systemname + DIRDELI + datedir + '暂时不压缩或者删除！'
                    elif datedir.isdigit() and len(datedir) == 4:
                        deletedate = deletedate[0:4]
                        gzipbegindate = gzipbegindate[0:4]
                        if ((datedir) > int(deletedate)) and (int(datedir) <= int(gzipbegindate)):
                            filedirlist = os.listdir(dirpath + systemname + DIRDELI + datedir)
                            for files in filedirlist:
                                filename = dirpath + systemname + DIRDELI + datedir + DIRDELI + files
                                if os.path.isfile('%s' % filename):
                                    if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                                        pass
                                    else:
                                        (status, output) = commands.getstatusoutput('gzip %s' % filename)
                                        if status == 0 and output == '':
                                            print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                                        else:
                                            print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
                        elif int(datedir) <= int(deletedate):
                            deletepath = dirpath + systemname + DIRDELI + datedir
                            mkdirdeletepath = dirpath + systemname + DIRDELI
                            if int(switchs) == CONSIDER:
                                t = os.stat(deletepath)[8]
                                t = float(t)
                                t = time.strftime('%Y%m%d', time.gmtime(t))[2:6]
                            else:
                                t = datedir
                            if int(t) > int(deletedate):
                                pass
                            elif int(t) <= int(deletedate):
                                commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                                commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                                hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                                commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                                (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                                if status == 0 and output == '':
                                    print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                                else:
                                    print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
                        else:
                            print '[' + nowtime() + '] ' + dirpath + systemname + DIRDELI + datedir + '暂时不压缩或者删除！'




def have4or6date(dirpath, slicehead, deletemon, keepmon, switchs):
    deletedate = get_today_month(deletemon)
    deletedatemon = deletedate[slicehead:6]
    gzipbegindate = get_today_month(keepmon)
    gzipbeginmon = gzipbegindate[slicehead:6]
    if dirpath[-3:] == 'ua_':
        datedirlist = os.listdir(dirpath[0:-3])
        for datedir in datedirlist:
            if datedir[0:3] == 'ua_':
                if (int(datedir[3:]) > int(deletedatemon)) and (int(datedir[3:]) <= int(gzipbeginmon)):
                    filesdirlist = os.listdir(dirpath[0:-3] + datedir)
                    for files in filesdirlist:
                        filename = dirpath[0:-3] + datedir + DIRDELI + files
                        if os.path.isfile(filename):
                            if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                                pass
                            else:
                                (status, output) = commands.getstatusoutput('gzip %s' % filename)
                                if status == 0 and output == '':
                                    print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                                else:
                                    print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
                elif int(datedir[3:]) <= int(deletedatemon):
                    deletepath = dirpath[0:-3] + datedir
                    mkdirdeletepath = dirpath[0:-3]
                    if int(switchs) == CONSIDER:
                        t = os.stat(deletepath)[8]
                        t = float(t)
                        t = (time.strftime('%Y%m%d', time.gmtime(t)))[2:6]
                    else:
                        t = datedir[3:]
                    if int(t) > int(deletedatemon):
                        pass
                    elif int(t) <= int(deletedatemon):
                        commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                        commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                        hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                        commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                        (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                        if status == 0 and output == '':
                            print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                        else:
                            print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
                else:
                    print '[' + nowtime() + '] ' + dirpath[0:-3] + datedir + '暂时不压缩或者删除！'
    elif 'all_midt' in dirpath or 'bidt/' in dirpath or 'sond' in dirpath:
        dirlist = os.listdir(dirpath)
        for datedir in dirlist:
            if datedir.isdigit():
                if os.path.isdir(dirpath + datedir):
                    if (int(datedir) > int(deletedatemon)) and (int(datedir) <= int(gzipbeginmon)):
                        fileslist = os.listdir(dirpath + datedir)
                        for files in fileslist:
                            filename = dirpath + datedir + DIRDELI + files
                            if os.path.isfile(filename):
                                if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                                    pass
                                else:
                                    (status, output) = commands.getstatusoutput('gzip %s' % filename)
                                    if status == 0 and output == '':
                                        print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                                    else:
                                        print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
                    elif int(datedir) <= int(deletedatemon):
                        deletepath = dirpath + datedir
                        mkdirdeletepath = dirpath
                        if int(switchs) == CONSIDER:
                            t = os.stat(deletepath)[8]
                            t = float(t)
                            t = (time.strftime('%Y%m%d', time.gmtime(t)))[0:6]
                        else:
                            t = datedir
                        if int(t) > int(deletedatemon):
                            pass
                        elif int(t) <= int(deletedatemon):
                            commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                            commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                            hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                            commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                            (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                            if status == 0 and output == '':
                                print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                            else:
                                print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
                    else:
                        print '[' + nowtime() + '] ' + dirpath + datedir + '暂时不压缩或者删除！'

def bidt_data(dirpath, befordays, gzipdays, switchs):
    deletedate = BeforeDate(todaystr, befordays)
    gzipbegindate = BeforeDate(todaystr, gzipdays)
    dirlist = []
    for d in os.listdir(dirpath):
        if os.path.isdir(dirpath + d):
            if d.isdigit():
                dirlist.append(d)
    for dirs in dirlist:#循环list
        if (int(dirs) > int(deletedate)) and (int(dirs) <= int(gzipbegindate)):
            (status, output) = commands.getstatusoutput('gzip %s%s/*/*' % (dirpath, dirs))

            if status == 0 and output == '':
                print '[%s] 压缩目录%s%s成功！' % (nowtime(), dirpath, dirs)
            else:
                print '[%s] 压缩目录%s%s失败！可能该目录下的文件就是压缩文件！' % (nowtime(), dirpath, dirs)
        elif int(dirs) <= int(deletedate):
            deletepath = dirpath + dirs
            mkdirdeletepath = dirpath
            if int(switchs) == CONSIDER:
                t = os.stat(deletepath)[8]
                t = float(t)
                t = time.strftime('%Y%m%d', time.gmtime(t))
            else:
                t = dirs
            if int(t) > int(deletedate):
                pass
            elif int(t) <= int(deletedate):
                commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                if status == 0 and output == '':
                    print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                else:
                    print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
        else:
            print '[' + nowtime() + '] ' + dirpath + dirs + '暂时不压缩或者删除！'

def have8date(line):
    dirpath = line.split(DATE8)[0]#获取配置文件中的操作目录
    befordays = line.split(',')[1]#获取配置文件中删除天数
    gzipddays = line.split(',')[2]#获取配置文件中的压缩天数
    switchs = line.split(',')[3]
    gzipbegindate = get_day_of_day(-int(gzipddays))#截止压缩的日期
    deletedate = BeforeDate(todaystr, befordays)#需要删除的日期
    dirlist = []
    for d in os.listdir(dirpath):
        if os.path.isdir('%s%s' % (dirpath, d)):
            if d.isdigit():
                dirlist.append(d)#把操作目录下的所有目录放到list里
    for dirs in dirlist:#循环list
        if (int(dirs) > int(deletedate)) and (int(dirs) <= int(gzipbegindate)):#把压缩日期段的所有文件压缩
            for files in os.listdir('%s%s' % (dirpath, dirs)):
                filename = '%s%s/%s' % (dirpath, dirs, files)

                if os.path.isfile('%s' % filename):
                    if filename[-3:] == '.gz' or filename[-2:] == '.Z' or filename[-3:] == 'zip':
                        pass
                    else:
                        (status, output) = commands.getstatusoutput('gzip %s' % filename)
                        if status == 0 and output == '':
                            print '[%s] 压缩文件%s成功！' % (nowtime(), filename)
                        else:
                            print '[%s] 压缩文件%s失败！' % (nowtime(), filename)
        elif int(dirs) <= int(deletedate):
            deletepath = dirpath + dirs
            mkdirdeletepath = dirpath
            if int(switchs) == CONSIDER:
                t = os.stat(deletepath)[8]
                t = float(t)
                t = time.strftime('%Y%m%d', time.gmtime(t))

            else:
                t = dirs

            if int(t) > int(deletedate):
                pass
            elif int(t) <= int(deletedate):
                commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, deletepath))
                hdfsdir = '%s%s' % (HDFSDIR, mkdirdeletepath)
                commands.getstatusoutput('hdfs dfs -put %s %s' % (deletepath, hdfsdir))
                (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                if status == 0 and output == '':
                    print '[%s] 删除文件%s成功！' % (nowtime(), deletepath)
                else:
                    print '[%s] 删除文件%s失败！' % (nowtime(), deletepath)
        else:
            print '[%s] %s%s暂时不压缩或者删除' % (nowtime(), dirpath, dirs)

def havenodateandsystemname(dirpath, befordays, gzipdays, switchs):
    deletedate = BeforeDate(todaystr, befordays)
    gzipbegindate = BeforeDate(todaystr, gzipdays)

    for dirpaths, dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            if os.path.isfile(dirpath + DIRDELI + filename):
                if filename[-3:] != '.gz' and filename[-3:] != 'out' and filename[-2:] != '.Z' and filename[-3:] != 'zip':
                    filedate = filename[-12:-4]
                    if (int(filedate) > int(deletedate)) and (int(filedate) <= int(gzipbegindate)):
                        (status, output) = commands.getstatusoutput('gzip %s/%s' % (dirpath, filename))
                        if status == 0 and output == '':
                            print '[%s] 压缩文件%s%s成功！' % (nowtime(), dirpath, filename)
                        else:
                            print '[%s] 压缩文件%s%s失败！' % (nowtime(), dirpath, filename)
                    elif int(filedate) <= int(deletedate):
                        if int(switchs) == CONSIDER:
                            t = os.stat(dirpath+filename)[8]
                            t = float(t)
                            t = time.strftime('%Y%m%d', time.gmtime(t))
                        else:
                            t = filedate
                        if int(t) > int(deletedate):
                            pass
                        elif int(t) <= int(deletedate):
                            commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                            commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, dirpath))
                            hdfsdir = '%s%s' % (HDFSDIR, dirpath)
                            commands.getstatusoutput('hdfs dfs -put %s/%s %s/%s' % (dirpath, filename, hdfsdir, filename))
                            (status, output) = commands.getstatusoutput('rm %s/%s' % (dirpath, filename))
                            if status == 0 and output == '':
                                print '[%s] 删除文件%s%s成功！' % (nowtime(), dirpath, filename)
                            else:
                                print '[%s] 删除文件%s%s失败！' % (nowtime(), dirpath, filename)
                    else:
                        print '[' + nowtime() + '] ' + dirpath + DIRDELI + filename + '暂时不压缩或者删除！'
                elif filename[-3:] == '.gz':
                    filedate = filename[-15:-7]
                    if int(filedate) <= int(deletedate):
                        if int(switchs) == CONSIDER:
                            t = os.stat(dirpath+filename)[8]
                            t = float(t)
                            t = time.strftime('%Y%m%d', time.gmtime(t))
                        else:
                            t = filedate
                        if int(t) > int(deletedate):
                            pass
                        elif int(t) <= int(deletedate):
                            commands.getstatusoutput('export HADOOP_USER_NAME=BDATA_GP_ADM')
                            commands.getstatusoutput('hdfs dfs -mkdir %s%s' % (HDFSDIR, dirpath))
                            hdfsdir = '%s%s' % (HDFSDIR, dirpath)
                            commands.getstatusoutput('hdfs dfs -put %s/%s %s/%s' % (dirpath, filename, hdfsdir, filename))
                            (status, output) = commands.getstatusoutput('rm %s/%s' % (dirpath, filename))
                            if status == 0 and output == '':
                                print '[%s] 删除文件%s%s成功！' % (nowtime(), dirpath, filename)
                            else:
                                print '[%s] 删除文件%s%s失败！' % (nowtime(), dirpath, filename)
                    else:
                        print '[' + nowtime() + '] ' + dirpath + DIRDELI + filename + '暂时不压缩或者删除！'

def main():
    fd = open(configfile, 'r')



    while True:
        current_time = time.localtime(time.time())
        line = fd.readline().split('\n')[0]
        if len(line) == 0:
            break
        if SYSTEM8DATE in line or SYSTEM6DATE in line or SYSTEM4DATE in line:
            havesystemname(line)
        elif DATE8 in line and SYSTEM not in line and 'bidt_data' not in line:
            have8date(line)


        elif (line.split(',')[0] == LOGFILEDIR) or (line.split(',')[0] == TKTERRORDIR):
            dirpath = line.split(',')[0] + DIRDELI
            befordays = line.split(',')[1]
            gzipdays = line.split(',')[2]
            switchs = line.split(',')[3]
            havenodateandsystemname(dirpath, befordays, gzipdays, switchs)

        #每月1号才执行
        if current_time.tm_mday == 1: # and (current_time.tm_hour == 9) and (current_time.tm_min == 0) and (current_time.tm_sec == 0)):
            if DATE6 in line :
                dirpath = line.split(DATE6)[0]
                deletemon = -int(line.split(',')[1])
                keepmon = -int(line.split(',')[2])
                switchs = line.split(',')[3]
                have4or6date(dirpath, 0, deletemon, keepmon, switchs)

            elif DATE4 in line:
                dirpath = line.split(DATE4)[0]
                deletemon = -int(line.split(',')[1])
                keepmon = -int(line.split(',')[2])
                switchs = line.split(',')[3]
                have4or6date(dirpath, 2, deletemon, keepmon, switchs)

            elif line.split(DATE8)[0] == BIDTDATADIR:
                dirpath = line.split(DATE8)[0]
                befordays = line.split(',')[1]
                gzipdays = line.split(',')[2]
                switchs = line.split(',')[3]
                bidt_data(dirpath, befordays, gzipdays, switchs)



if len(sys.argv) == 2:
    stdout_backup = sys.stdout
    log_file = open("cpdelete%s.log" % time.strftime('%Y%m%d', time.localtime(time.time())), 'w')
    sys.stdout = log_file
    print '[%s] start process all file and dir!' % nowtime()
    main()
    print '[%s] all file and dir is process over!' % nowtime()
    log_file.close()
    sys.stdout = stdout_backup
else:
    print 'The args num is incorrect!!'

