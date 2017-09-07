# -*- coding:utf-8 -*-
from BaseHTTPServer import *
import commands
# import statvfs
# import os

whitelist = ['127.0.0.2']
programpath = '/ETL/work/mlei/localfile'
programname = 'recoverfile.py'


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        """Serve a GET request."""
        path = self.path
        if path == '/favicon.ico':
            pass
        else:
            argvlist = self.path.split('&')[1:]
            filenamelist = argvlist[0].split(',')
            hdfsdirlist = argvlist[1].split(',')
            task_id = argvlist[2]
            etl_host = argvlist[3]
            self.protocal_version = 'HTTP / 1.1'
            self.send_response(200)
            self.send_header("Welcome", "Contect")
            self.end_headers()
            if self.client_address[0] in whitelist:
                (status, output) = commands.getstatusoutput(
                    'python %s/%s %s %s %s %s %s %s %s %s %s' %
                    (programpath, programname, 'DW_DATA', 'sys_etl_batch', 'anquandiyi', '10.5.30.1', '5432',
                     filenamelist, hdfsdirlist, task_id, etl_host))
                if status == 0 and output == '':
                    self.wfile.write('Process the program success!')
                else:
                    self.wfile.write('Process the program fail!')
                self.wfile.write('You are VIP!You can do everything what you want to do!')
            else:
                self.wfile.write('You are not in whitelist! Can not access!')

    def do_HEAD(self):
        """Serve a HEAD request."""
        pass

    def do_POST(self):
        """Serve a POST request."""
        pass


def main():
    http_server = HTTPServer(('127.0.0.1', 8035), SimpleHTTPRequestHandler)
    http_server.serve_forever()


if __name__ == '__main__':
    main()
