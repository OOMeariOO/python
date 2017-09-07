# -*- coding:utf-8 -*-

import time
import os
import sys
import re
import commands
import psycopg2
import xml.dom.minidom

DIRDELI = '/'
CONSIDER = '0'
todaystr = sys.argv[1]
configfile = sys.argv[2]
MetaDataLogBk = '/ETL/LOG/MetaDataLogBk'
USER = sys.argv[3]
PASSWD = sys.argv[4]
stamp = sys.argv[5]
HOST = sys.argv[6]
PORT = sys.argv[7]
ETL_HOST = sys.argv[8]
DB = sys.argv[9]
HDFSDIR = '/data/GP/ETL_BAK/%s' % ETL_HOST
ISOTIMEFORMAT = '%Y-%m-%d %X'
ETLDATAEXE = '/ETL/bin/EtlDate.exe'
PGTABLE = 'dss_pstat.etl_bak_recv'
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


def beforedate(todstr, offset):
    return os.popen("%s %s -%s" % (ETLDATAEXE, todstr, offset)).read().strip('\n')


def isvailddate(date):
    try:
        time.strptime(date, "%Y%m%d")
        return True
    except ValueError:
        return False


def getdirdate(filefullpath):
    datedir = ''
    count = 0
    dirlist = filefullpath.split(DIRDELI)
    if os.path.isfile(filefullpath):
        count = len(dirlist) - 1
    elif os.path.isdir(filefullpath):
        count = len(dirlist)
    for i in range(1, count):
        if dirlist[i].isdigit():
            datedir = dirlist[i]
            if len(datedir) == 8:
                pass
            elif len(datedir) == 6:
                datedir += '01'
            elif len(datedir) == 4:
                datedir = '20' + datedir + '01'
            if isvailddate(datedir):
                return datedir, i
            else:
                # print datedir
                myprinttodouble('[%s] the string is not a date! %s' % (nowtime(), filefullpath))
                # os._exit(-1)
        else:
            datedirlist = re.findall(r"\d\d\d\d+", dirlist[i])
            if datedirlist:
                datedir = datedirlist[0]
                if len(datedir) == 4:
                    datedir = '20' + datedir + '01'
                elif len(datedir) == 6:
                    datedir += '01'
                elif len(datedir) == 8:
                    pass
                # print 'dir' + datedir
                if isvailddate(datedir):
                    return datedir, i
                else:
                    datedir = ''

    if datedir == '':
        datedirlist = re.findall(r"\d\d\d\d+", dirlist[-1])
        if datedirlist:
            datefile = datedirlist[-1]
            if len(datefile) == 4:
                datefile = '20' + datefile + '01'
            elif len(datefile) == 6:
                datefile += '01'
            elif len(datefile) == 8:
                pass
            else:
                # print filefullpath + 'this file have not useful date'
                return '', 0
            # print 'file' + datefile
            if isvailddate(datefile):
                return datefile, -1
            else:
                myprinttodouble('[%s] the string is not a date! %s' % (nowtime(), filefullpath))
                # os._exit(-1)
        else:
            # print filefullpath + 'this file have not useful date'
            return '', 0


def rmemptydir(dirsplitlist, i, datedirnum):
    i -= 1
    dirpaths = ''
    for j in range(1, i + 1):
        dirpaths += DIRDELI + dirsplitlist[j]
    filelist = os.listdir(dirpaths)
    if not filelist:
        if i >= datedirnum != -1:
            try:
                (status, output) = commands.getstatusoutput('rmdir %s' % dirpaths)
                if status == 0 and output == '':
                    myprinttofile('[%s] dir %s is empty, rm it success!' % (nowtime(), dirpaths))
                    # Loop to determine whether the upper directory is empty directory
                    rmemptydir(dirsplitlist, i, datedirnum)
            except Exception, e:
                myprinttodouble('[%s] rm dir %s fail,please find the reasons!' % (nowtime(), dirpaths))
                myprinttodouble(str((Exception, ':', nowtime(), e)))


def gzipfiles(dirpaths, files, lasttmdict):
    filefullpath = dirpaths + DIRDELI + files
    # filename = ''
    if filefullpath[-3:] == '.gz' or filefullpath[-4:] == '.zip' or filefullpath[-2:] == '.Z':
        filename = files
        # print 'the file of put in  ' + filefullpath
        lasttm = int(os.stat(filefullpath)[8])
        # print 'already compression %d' % lasttm
        lasttmdict[filefullpath] = lasttm
        return filename
    else:
        # print 'the file of put in ' + filefullpath
        lasttm = int(os.stat(filefullpath)[8])
        # print 'not compression %d' % lasttm
        lasttmdict[filefullpath + '.gz'] = lasttm
        try:
            (status, output) = commands.getstatusoutput('gzip %s' % filefullpath)
            if status == 0 and output == '':
                # if the file is already compression,the filename's suffix will add .gz
                filename = files + '.gz'
                myprinttofile('[%s] gzip file %s success!' % (nowtime(), filefullpath))
                return filename
        except Exception, e:
            myprinttodouble('[%s] gzip file %s fail!' % (nowtime(), filefullpath))
            myprinttodouble(str((Exception, ':', nowtime(), e)))


def creatandputhdfs(hdfsbakdir, dirpaths, filename, lasttmdict, deleteflag, datedirnum, cur, conn):
    try:
        filefullpath = dirpaths + DIRDELI + filename
    except Exception, e:
        myprinttodouble(str((dirpaths, DIRDELI, filename)))
        myprinttodouble(str((Exception, ':', nowtime(), e)))
        return
    lst_tm = lasttmdict[filefullpath]
    stampnow = timestamp()
    file_size = os.stat(filefullpath)[6]
    try:
        (status, output) = commands.getstatusoutput('hdfs dfs -mkdir -p %s' % hdfsbakdir)
        if status == 0 and output == '':
            myprinttofile('[%s] creat dir %s success!' % (nowtime(), dirpaths))
            try:
                cur.execute('''INSERT INTO %s (etl_host, file_name, bak_url, bak_tm, hdfs_url, lst_tm, run_tm, file_size)
                                VALUES ('%s', '%s', '%s', to_timestamp(%d), '%s',
                                to_timestamp(%d), to_timestamp(%d), %d); ''' % (PGTABLE, ETL_HOST, filename, dirpaths,
                                                                                int(stamp), hdfsbakdir, int(lst_tm),
                                                                                int(stampnow), file_size))
                conn.commit()
            except Exception, e:
                myprinttodouble('[%s] insert data %s fail!' % (nowtime(), filefullpath))
                myprinttodouble(str((Exception, ':', nowtime(), e)))
                os._exit(-1)
                # put the file in hdfs and add the Timestamp with the filename
            try:
                (status, output) = commands.getstatusoutput('hdfs dfs -put %s/%s %s/%s' %
                                                            (dirpaths, filename, hdfsbakdir, filename))
                if status == 0 and output == '':
                    myprinttofile('[%s] put file %s success!' % (nowtime(), filefullpath))
                    if deleteflag == 1:
                        myprinttodouble('[%s] the dir %s is only backed,not delete!' % (nowtime(), dirpaths))
                    # delete it
                    else:
                        rmfiles(dirpaths, filename, datedirnum)
            except Exception, e:
                myprinttodouble('[%s] put file %s fail!' % (nowtime(), filefullpath))
                myprinttodouble(str((Exception, ':', nowtime(), e)))
                os._exit(-1)
    except Exception, e:
        myprinttodouble('[%s] creat dir %s fail!' % (nowtime(), dirpaths))
        myprinttodouble(str((Exception, ':', nowtime(), e)))
        os._exit(-1)


def rmfiles(dirpaths, filename, datedirnum):
    filefullpath = dirpaths + DIRDELI + filename
    try:
        (status, output) = commands.getstatusoutput('rm %s' % filefullpath)
        if status == 0 and output == '':
            myprinttofile('[%s] rm file %s success!' % (nowtime(), filefullpath))
            filelist = os.listdir(dirpaths)
            if not filelist:
                dirsplitlist = dirpaths.split(DIRDELI)
                for i in range(1, len(dirsplitlist)):
                    if dirsplitlist[i] == dirsplitlist[-1]:
                        if i >= datedirnum != -1:
                            try:
                                (status, output) = commands.getstatusoutput('rmdir %s' % dirpaths)
                                if status == 0 and output == '':
                                    myprinttofile('[%s] dir %s is empty, rm it success!' % (nowtime(), dirpaths))
                                    # Loop to determine whether the upper directory is empty directory
                                    rmemptydir(dirsplitlist, i, datedirnum)
                            except Exception, e:
                                myprinttodouble('[%s] rm dir %s fail,please find the reasons!' % (nowtime(), dirpaths))
                                myprinttodouble(str((Exception, ':', nowtime(), e)))
    except Exception, e:
        myprinttodouble('[%s] rm file %s fail!' % (nowtime(), filefullpath))
        myprinttodouble(str((Exception, ':', nowtime(), e)))


def delemptydir(dirpaths, datedirnum):
    dirsplitlist = dirpaths.split(DIRDELI)
    for i in range(1, len(dirsplitlist)):
        if dirsplitlist[i] == dirsplitlist[-1]:
            if i >= datedirnum != -1:
                try:
                    (status, output) = commands.getstatusoutput('rmdir %s' % dirpaths)
                    if status == 0 and output == '':
                        myprinttofile('[%s] dir %s is empty, rm it success!' % (nowtime(), dirpaths))
                        # Loop to determine whether the upper directory is empty directory
                        rmemptydir(dirsplitlist, i, datedirnum)
                except Exception, e:
                    myprinttodouble('[%s] rm dir %s fail,please find the reasons!' % (nowtime(), dirpaths))
                    myprinttodouble(str((Exception, ':', nowtime(), e)))


def timestamp():
    return str(int(time.time()))


def process(dirpaths, files, lasttm_format, deletedate, gzipdate,
            lasttmdict, datedirnum, conn, cur):
    filename = ''
    # delete file switch
    deleteflag = 0
    # gzip file switch
    gzipfalg = 0
    # creat dir on the hdfs and put file in it switch
    puthdfsflag = 0
    fullfilename = dirpaths + DIRDELI + files
    # file's lasttime less than or equal to gzipdate, gzip it
    if int(lasttm_format) <= int(gzipdate):
        if gzipfalg == 0:
            filename = gzipfiles(dirpaths, files, lasttmdict)
        # if file's lasttime less than or equal to gzipdate and deletedate, put it in hdfs and rm it
        if int(lasttm_format) <= int(deletedate):
            hdfsbakdir = HDFSDIR + dirpaths + '.' + stamp
            if puthdfsflag == 0:
                # creat the dir on the hdfs
                creatandputhdfs(hdfsbakdir, dirpaths, filename, lasttmdict, deleteflag, datedirnum, cur, conn)
    else:
        myprinttofile('[%s] the file %s is not process now' % (nowtime(), fullfilename))


def GetXmlData(prantnode, Lstchildattr):
    configdict = {}
    doc = xml.dom.minidom.parse(configfile)
    rootnode = doc.documentElement
    nodes = rootnode.getElementsByTagName(prantnode)
    for node in nodes:
        configdict[node.getAttribute(Lstchildattr[0])] = [node.getAttribute(Lstchildattr[1]),
                                                          node.getAttribute(Lstchildattr[2]),
                                                          node.getAttribute(Lstchildattr[3])]
    return configdict


def GetXmlfile(prantnode, Lstchildattr):
    configlist = []
    count = len(Lstchildattr)
    doc = xml.dom.minidom.parse(configfile)
    rootnode = doc.documentElement
    nodes = rootnode.getElementsByTagName(prantnode)
    for node in nodes:
        for i in range(count):
            configlist.append(node.getAttribute(Lstchildattr[i]))
    return configlist


def main():
    ordinarydirdict = GetXmlData('ordinarydir', ['path', 'deletedays', 'gzipdays', 'consider'])
    specialdirdict = GetXmlData('specialdir', ['spath', 'sdeletedays', 'sgzipdays', 'sconsider'])
    notprocessfilelist = GetXmlfile('notprocessfile', ['filename', 'filename1', 'filename2', 'filename3'])
    notprocessdirlist = GetXmlfile('notprocessdir', ['dir'])
    # connect pg
    conn = ''
    cur = ''
    forflag = 0
    try:
        conn = psycopg2.connect(database=DB, user=USER, password=PASSWD, host=HOST, port=int(PORT))
        cur = conn.cursor()
    except Exception, e:
        myprinttodouble('[%s] connect pg fail!' % nowtime())
        myprinttodouble(str((Exception, ':', nowtime(), e)))
        os._exit(-1)
    # Convert the special directory into a normal directory
    for specialdir in specialdirdict.keys():
        deldate = beforedate(todaystr, '7')
        specialdir1 = specialdir.replace('YYYYMMDD', deldate)
        for j in range(1, 9):
            num = '0' + str(j)
            specialdir2 = specialdir1.replace('XX', num)
            ordinarydirdict[specialdir2] = specialdirdict[specialdir]

    for dirpath in ordinarydirdict.keys():
        delpoint = ordinarydirdict[dirpath][0]
        gzippoint = ordinarydirdict[dirpath][1]
        switchs = ordinarydirdict[dirpath][2]
        deletedate = beforedate(todaystr, delpoint)
        gzipdate = beforedate(todaystr, gzippoint)
        for dirpaths, dirnames, filenames in os.walk(dirpath):
            # not process dir
            for i in notprocessdirlist:
                if i in dirpaths:
                    myprinttodouble('[%s] not process the dir %s' % (nowtime(), dirpaths))
                    forflag = 1
            if forflag == 1:
                forflag = 0
                continue
            # rm empty dir
            if not filenames and not dirnames:
                dirdate, datedirnum = getdirdate(dirpaths)
                if dirdate == '' and datedirnum == 0:
                    myprinttodouble('[%s] the empty dir %s have no useful date,not process!' % (nowtime(), dirpaths))
                    continue
                delemptydir(dirpaths, datedirnum)
            # process file
            elif filenames:
                for files in filenames:
                    lasttmdict = {}
                    filefullpath = dirpaths + DIRDELI + files
                    dirdate, datedirnum = getdirdate(filefullpath)
                    if dirdate == '' and datedirnum == 0:
                        myprinttodouble(nowtime() + ' ' + filefullpath + ' file have no useful date,not process!')
                        continue
                    for i in notprocessfilelist:
                        if files[:4] == i or files[-4:] == i or files[-7:] == i:
                            myprinttofile('[%s] %s file not process!' % (nowtime(), i))
                            forflag = 1
                    if forflag == 1:
                        forflag = 0
                        continue
                    if switchs == CONSIDER:
                        # print 'this is CONSIDER'
                        lasttm_format = time.strftime('%Y%m%d', time.localtime(int(os.stat(filefullpath)[8])))
                    else:
                        # print 'this is not CONSIDER'
                        lasttm_format = dirdate
                    process(dirpaths, files, lasttm_format, deletedate, gzipdate,
                            lasttmdict, datedirnum, conn, cur)
    cur.close()
    conn.close()

if __name__ == '__main__':
    os.system('dos2unix %s' % configfile)
    if os.path.exists(logfiledir):
        pass
    else:
        os.system('mkdir -p %s' % logfiledir)
    sys.path.append('/usr/java/jdk1.7.0_67-cloudera/bin')
    os.environ['HADOOP_USER_NAME'] = 'BDATA_GP_ADM'
    PATH = os.environ['PATH']
    os.environ['PATH'] = '/usr/java/jdk1.7.0_67-cloudera/bin:%s' % PATH
    myprinttodouble(os.environ['PATH'])
    os.environ['JAVA_HOME'] = '/usr/java/jdk1.7.0_67-cloudera'
    myprinttodouble('[%s] start process all file and dir!' % nowtime())
    myprinttodouble('Time stamp when running the program : %s' % stamp)
    main()
    myprinttodouble('[%s] all file and dir is process over!' % nowtime())
