#_author_ : duany_000
#_date_ : 2018/3/5
import optparse
import socketserver
from conf import settings
from core import server
"""
from optparse import OptionParser  
[...]  
parser = OptionParser()  
parser.add_option("-f", "--file", dest="filename",  
                  help="write report to FILE", metavar="FILE")  
parser.add_option("-q", "--quiet",  
                  action="store_false", dest="verbose", default=True,  
                  help="don't print status messages to stdout")  
  
(options, args) = parser.parse_args()  
"""
class ArgvHandler(object):
    def __init__(self):
        self.op=optparse.OptionParser()
        # op.add_option("-s","--host",dest="host",help="server_sel_ftp IP address")
        # op.add_option("-P","--port",dest="port",help="server_sel_ftp port")
        options, args = self.op.parse_args()
        # print(options,args)
        # print(options.host,options.port)
        self.verify_argv(options, args)

    def verify_argv(self,options, args): # python ftp_server.py start
        if hasattr(self, args[0]):
            func = getattr(self, args[0])
            func()
        else:
            self.op.print_help()

    def start(self):
        print('server_sel_ftp is working ....')
        ser = socketserver.ThreadingTCPServer((settings.IP,settings.PORT), server.ServerHandler)
        ser.serve_forever()



