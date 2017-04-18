#coding: utf-8
import time
import subprocess
import datetime
import itertools
import os
import sys
import commands
import string
from time import strftime, localtime
from datetime import timedelta, date
import calendar
import re

confidfile = 'config.txt'
"""
/ETL/LOG,180
/ETL/DATA/fail/tkterror,180
/ETL/DATA/fail/bypass/{{SYSTEMNAME}},180
/ETL/DATA/fail/corrupt/{{SYSTEMNAME}},180
/ETL/DATA/fail/duplicate/{{SYSTEMNAME}},180
/ETL/DATA/fail/error/{{SYSTEMNAME}},180
/ETL/LOG/{{SYSTEMNAME}},180
/ETL/DATA/complete/{{SYSTEMNAME}},60
/ETL/DATA/export/{{YYYYMMDD}},60
/ETL/DATA/savehostf/{{YYYYMMDD}},60
/ETL/DATA/fail/unknown/{{YYYYMMDD}},180
/ETL/DATA/prod_data/bidt/{{YYYYMM}}
/ETL/DATA/prod_data/midt/all_midt/{{YYYYMM}}
/ETL/DATA/prod_data/midt/ua_{{YYMM}}
/ETL/DATA/prod_data/sond/crs/{{YYMM}}
/ETL/DATA/prod_data/sond/ics/{{YYMM}}
说明：
1.目录中没有日期的，需要加保留的天数，用逗号分隔，写完整路径（第1-2行）
2.目录中带有系统名的，需要加保留的天数，用逗号分隔，路径写到系统名即可（第3-8行）
3.目录中有日期，且日期为八位数的，需要加保留天数，用逗号分隔，路径写到日期目录（9-11行）
4.目录中有日期，且日期为四位或六位的，不需要加保留的天数，路径写到日期目录（12-16行）
"""
todaystr = sys.argv[1]
BEFOREYEAR = -12
BEFOREMON = -1
year = todaystr[0:4]
mon = todaystr[4:6]
day = todaystr[6:]

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
    return os.popen("/ETL/bin/EtlDate.exe %s -%s" % (todaystr, Offset)).read().strip('\n')

def havesystemname(line):
    dirpath = line.split('{{SYSTEMNAME}}')[0]
    dirlist = os.listdir(dirpath)
    if 'MetaDataLogBk' in dirlist:
        dirlist.remove('MetaDataLogBk')
        print 'MetaDataLogBk目录不作处理'
    befordays = line.split(',')[1]
    for systemname in dirlist:
        systempath = dirpath + systemname
        if os.path.isdir(systempath):
            deletedate = BeforeDate(todaystr, befordays)
            gzipdirpath = systempath + '/' + todaystr
            deletepath = systempath + '/' + deletedate
            if os.path.exists(gzipdirpath):

                print '开始压缩目录%s' % gzipdirpath
                (status, output) = commands.getstatusoutput('gzip %s/*'%gzipdirpath)
                if status == 0 and output == '':
                    print '压缩%s成功！' % gzipdirpath
                    (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                    if status == 0 and output == '':
                        print '删除%s成功！' % deletepath
                    else:
                        print '删除%s失败！' % deletepath
                else:
                    print '压缩%s失败,该目录的文件可能已经压缩，或者不存在！' % gzipdirpath
                    (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
                    if status == 0 and output == '':
                        print '删除%s成功！' % deletepath
                    else:
                        print '删除%s失败！' % deletepath
            else:
                print '目录%s不存在，无法处理！' % gzipdirpath


def have4or6date(dirpath, slicehead):
    deletedate = get_today_month(BEFOREYEAR)
    deletedatemon = deletedate[slicehead:6]
    lastmonth = get_today_month(BEFOREMON)
    lastmondate = lastmonth[slicehead:6]
    gzipdirpath = dirpath + lastmondate
    deletepath = dirpath + deletedatemon
    if os.path.exists(gzipdirpath):
        print '开始压缩目录%s' % gzipdirpath
        (status, output) = commands.getstatusoutput('gzip %s/*' % gzipdirpath)
        if status == 0 and output == '':
            print '压缩%s成功！' % gzipdirpath
            (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
            if status == 0 and output == '':
                print '删除%s成功！' % deletepath
            else:
                print '删除%s失败！' % deletepath
        else:
            print '压缩%s失败,该目录的文件可能已经压缩，或者不存在！' % gzipdirpath
            (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
            if status == 0 and output == '':
                print '删除%s成功！' % deletepath
            else:
                print '删除%s失败！' % deletepath
    else:
        print '目录%s不存在，无法处理！' % gzipdirpath


def have8date(line):
    dirpath = line.split('{{YYYYMMDD}}')[0]
    befordays = line.split(',')[1]
    deletedate = BeforeDate(todaystr, befordays)
    gzipdirpath = dirpath + todaystr
    deletepath = dirpath + deletedate
    if os.path.exists(gzipdirpath):
        print '开始压缩目录%s' % gzipdirpath
        (status, output) = commands.getstatusoutput('gzip %s/*' % gzipdirpath)
        if status == 0 and output == '':
            print '压缩%s成功！' % gzipdirpath
            (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
            if status == 0 and output == '':
                print '删除%s成功！' % deletepath
            else:
                print '删除%s失败！' % deletepath
        else:
            print '压缩%s失败,该目录的文件可能已经压缩，或者不存在！' % gzipdirpath
            (status, output) = commands.getstatusoutput('rm -r %s' % deletepath)
            if status == 0 and output == '':
                print '删除%s成功！' % deletepath
            else:
                print '删除%s失败！' % deletepath
    else:
        print '目录%s不存在，无法处理！' % gzipdirpath

def havenodateandsystemname(dirpath, befordays):
    deletedate = BeforeDate(todaystr, befordays)

    for dirpaths, dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            if os.path.exists('%s/%s' % (dirpath,filename)):
                if todaystr in filename: #and filename[-3] != '.gz':
                    if filename[-3] != '.gz':
                        suffix = filename[-4:]
                        deletefile = filename[0:-12] + deletedate + suffix + '.gz'
                        (status, output) = commands.getstatusoutput('gzip %s/%s' % (dirpath, filename))
                        if status == 0 and output == '':
                            print '压缩文件%s/%s成功！' % (dirpath, filename)

                            (status, output) = commands.getstatusoutput('rm %s/%s' % (dirpath, deletefile))
                            if status == 0 and output == '':
                                print '删除文件%s/%s成功！' % (dirpath, deletefile)
                            else:
                                print '删除文件%s/%s失败！' % (dirpath, deletefile)
                        else:
                            print '压缩文件%s/%s失败！' % (dirpath, filename)
                    else:
                        suffix = filename[-7:-3]
                        deletefile = filename[0:-15] + deletedate + suffix + '.gz'
                        (status, output) = commands.getstatusoutput('rm %s/%s' % (dirpath, deletefile))
                        if status == 0 and output == '':
                            print '删除文件%s/%s成功！' % (dirpath, deletefile)
                        else:
                            print '删除文件%s/%s失败！' % (dirpath, deletefile)


fd = open(confidfile, 'r')

while True:
    current_time = time.localtime(time.time())
    line = fd.readline().split('\n')[0]
    if len(line) == 0:
        break
    if '{{SYSTEMNAME}}' in line:
        havesystemname(line)
    elif '{{YYYYMMDD}}' in line:
        have8date(line)

    elif line[0:-4] == '/ETL/LOG' or line[0:-4] == '/ETL/DATA/fail/tkterror':
        dirpath = line[0:-4]
        befordays = line.split(',')[1]
        havenodateandsystemname(dirpath, befordays)

    #每月1号才执行
    if current_time.tm_mday == 1: # and (current_time.tm_hour == 9) and (current_time.tm_min == 0) and (current_time.tm_sec == 0)):
        if '{{YYYYMM}}' in line :
            dirpath = line.split('{{YYYYMM}}')[0]
            have4or6date(dirpath, 0)

        elif '{{YYMM}}' in line:
            dirpath = line.split('{{YYMM}}')[0]
            have4or6date(dirpath, 2)
