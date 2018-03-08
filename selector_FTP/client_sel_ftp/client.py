#_author_ : duany_000
#_date_ : 2018/3/7
import socket
import selectors
import sys
import os
import json
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class SeletFTPServer(object):
    def __init__(self):
        self.args = sys.argv
        if len(self.args)> 1:
            self.ip_port = (self.args[1], int(self.args[2]))
        else:
            self.ip_port = ('127.0.0.1',8080)
        self.create_socket()
        self.command_faout()

    def create_socket(self):
        try:
            self.sock = socket.socket()
            self.sock.connect(self.ip_port)
            print("连接服务器端成功")
        except Exception as e:
            print("error:",e)


    def command_faout(self):
        while True:
            cmd_obj = input(">>>").strip()
            if len(cmd_obj) == 0:continue
            elif cmd_obj.upper() == "Q":break
            cmd, file = cmd_obj.split()
            if hasattr(self,cmd):
                func = getattr(self, cmd)
                func(cmd,file)
            else:
                print("错误命令。。。")

    def post(self,cmd, file):
        abs_file_path = os.path.join(BASE_DIR, file)
        if os.path.exists(abs_file_path):
            file_name = os.path.basename(abs_file_path)
            file_size = os.stat(abs_file_path).st_size
            data = {
                'cmd':'post',
                'abs_file_path':abs_file_path,
                'file_name':file_name,
                'file_size':file_size,
            }
            self.sock.sendall(json.dumps(data).encode('utf8'))
            recv_status = self.sock.recv(1024)
            print(recv_status)
            has_send = 0
            if str(recv_status,encoding='utf8') == 'ok':
                f = open(abs_file_path,'rb')
                while has_send < file_size:
                    data = f.read(1024)
                    self.sock.sendall(data)
                    has_send += len(data)
                    s = str(int(has_send/file_size*100))+'%'
                    print('文件%s已上传%s'%(file_name,s))
                print('文件%s上传完毕'%file_name)

        else:
            print("该文件不存在。。。")

    def load(self, cmd, file):
        pass


if __name__ == '__main__':
    SeletFTPServer()
