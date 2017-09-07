import os
import commands
import time
import re
import xml.dom.minidom
import sys


DIRDELI = '/'
ISOTIMEFORMAT = '%Y-%m-%d %X'
configfile = '/ETL/DATA/work/mlei/localfile/xmltest.txt'
todaystr = sys.argv[1]
ETLDATAEXE = '/ETL/bin/EtlDate.exe'
nodate = time.strftime('%Y%m%d', time.localtime(time.time()))
logfiledir = '/ETL/LOG/MAN/%s' % nodate
logfile = 'ETL_CLEAR_%s.log' % time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))


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


def isvailddate(date):
    try:
        time.strptime(date, "%Y%m%d")
        return True
    except ValueError:
        return False


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
                    # print datedir
                    myprinttodouble('[%s] the string is not a date! %s' % (nowtime(), filefullpath))
                    # os._exit(-1)
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


def GetXmlData(prantnode, Lstchildattr):
    configdict = {}
    doc = xml.dom.minidom.parse(configfile)
    rootnode = doc.documentElement
    nodes = rootnode.getElementsByTagName(prantnode)
    for node in nodes:
        configdict[node.getAttribute(Lstchildattr[0])] = [node.getAttribute(Lstchildattr[1]),
                                                          node.getAttribute(Lstchildattr[2])]
    return configdict


def beforedate(todstr, offset):
    return os.popen("%s %s -%s" % (ETLDATAEXE, todstr, offset)).read().strip('\n')


def gzipfiles(dirpaths, files):
    filefullpath = dirpaths + DIRDELI + files
    if filefullpath[-3:] == '.gz' or filefullpath[-4:] == '.zip' or filefullpath[-2:] == '.Z':
        return files
    else:
        try:
            (status, output) = commands.getstatusoutput('gzip %s' % filefullpath)
            if status == 0 and output == '':
                files += '.gz'
                myprinttofile('[%s] gzip file %s success!' % (nowtime(), filefullpath))
                return files
        except Exception, e:
            myprinttodouble('[%s] gzip file %s fail!' % (nowtime(), filefullpath))
            myprinttodouble(str((Exception, ':', nowtime(), e)))


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


def process(dirpaths, files, lasttm_format, deletedate, gzipdate, datedirnum):
    filename = ''
    # delete file switch
    deleteflag = 0
    # gzip file switch
    gzipfalg = 0
    # file's lasttime less than or equal to gzipdate, gzip it
    if int(lasttm_format) <= int(gzipdate):
        if gzipfalg == 0:
            filename = gzipfiles(dirpaths, files)
        # if file's lasttime less than or equal to gzipdate and deletedate, rm it
        if int(lasttm_format) <= int(deletedate):
            if deleteflag == 0:
                rmfiles(dirpaths, filename, datedirnum)


def main():
    cleardirdict = GetXmlData('cleardir', ['path', 'deletedays', 'gzipdays'])
    for dirpath in cleardirdict.keys():
        delpoint = cleardirdict[dirpath][0]
        gzippoint = cleardirdict[dirpath][1]
        deletedate = beforedate(todaystr, delpoint)
        gzipdate = beforedate(todaystr, gzippoint)
        print deletedate, gzipdate
        for dirpaths, dirnames, filenames in os.walk(dirpath):
            # rm empty dir
            if not filenames and not dirnames:
                dirdate, datedirnum = getdirdate(dirpaths)
                if dirdate == '' and datedirnum == 0:
                    myprinttodouble('[%s] the empty dir %s have no useful date,not process!' % (nowtime(), dirpaths))
                    continue
                delemptydir(dirpaths, datedirnum)
            elif filenames:
                for files in filenames:
                    filefullpath = dirpaths + DIRDELI + files
                    dirdate, datedirnum = getdirdate(filefullpath)
                    if dirdate == '' and datedirnum == 0:
                        myprinttodouble(nowtime() + ' ' + filefullpath + ' file have no useful date,not process!')
                        continue
                    lasttm_format = time.strftime('%Y%m%d', time.localtime(int(os.stat(filefullpath)[8])))
                    process(dirpaths, files, lasttm_format, deletedate, gzipdate, datedirnum)


if __name__ == '__main__':
    if os.path.exists(logfiledir):
        pass
    else:
        os.system('mkdir -p %s' % logfiledir)
    myprinttodouble('[%s] start process all file and dir!' % nowtime())
    main()
    myprinttodouble('[%s] all file and dir is process over!' % nowtime())
