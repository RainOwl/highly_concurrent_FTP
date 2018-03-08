#_author_ : duany_000
#_date_ : 2018/3/7
import socket
import selectors
import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
class SeletFTPServer(object):
    def __init__(self):
        self.dic = {}
        self.hasReceived = 0
        self.sel = selectors.DefaultSelector()
        self.create_socket()
        self.handler()

    def create_socket(self):
        self.sock = socket.socket()
        self.sock.bind(('localhost', 8090))
        self.sock.listen(100)
        self.sock.setblocking(False)

        self.sel.register(self.sock, selectors.EVENT_READ, self.accept)
        print("服务端已启动，等待客户端连接。。。")

    def handler(self):
        while True:
            events = self.sel.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj, mask)

    def accept(self):
        conn, addr = self.sock.accept()  # Should be ready
        print('accepted', conn, 'from', addr)
        conn.setblocking(False)
        self.sel.register(conn, selectors.EVENT_READ, self.read)

        self.dic[conn]={}

    def read(self,conn, mask):
        try:
            if not self.dic[conn]:
                data = conn.recv(1024)
                data = json.loads(data.decode('utf8'))
                print("data:", data)
                cmd = data['cmd']
                abs_file_path  = data['abs_file_path']
                file_name = data['file_name']
                file_size = data['file_size']

                self.dic[conn] = {
                    'cmd': cmd,
                    'abs_file_path': abs_file_path,
                    'file_name': file_name,
                    'file_size': file_size,
                }
                if cmd == 'post':
                    conn.send(b'ok')
                if cmd == 'load':
                    file_path = os.path.join(BASE_DIR,'download','file_name')
                    if os.path.exists(file_path):
                        file_size = os.stat(file_path).st_size
                        send_info = "%s|%s"% ("YES",file_size)
                        conn.send(bytes(send_info,encoding='utf8'))
                    else:
                        send_info = "%s|%s"% ("NO",0)
                        conn.send(bytes(send_info, encoding='utf8')
            else:
                if self.dic[conn]['cmd']:
                    cmd = self.dic[conn]['cmd']
                    if hasattr(self,cmd):
                        func = getattr(self, cmd)
                        func(conn)
                    else:
                        print('erro cmd')
                        conn.close()

        except Exception as e:
            print("error:",e)
            self.sel.unregister(conn)
            conn.close()

    def post(self,conn):
        file_name = self.dic[conn]['file_name']
        file_size = self.dic[conn]['file_size']
        file_path_from = self.dic[conn]['abs_file_path']
        file_path_to = os.path.join(BASE_DIR,'upload',file_name)

        recv_data = conn.recv(1024)
        with open(file_path_to,'wb') as f:
            f.write(recv_data)
            self.hasReceived += len(recv_data)
        if has_recv == self.hasReceived:
            if conn in self.dic.keys():
                self.dic[conn] = {}
            print("上传完毕")

    def load(self,conn):
        pass

if __name__ == '__main__':
    SeletFTPServer()
