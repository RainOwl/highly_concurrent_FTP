# _author_ : duany_000
# _date_ : 2018/3/5
import optparse
import socket
import json
import os
import time
import sys

STATUS_CODE = {
    250: "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251: "Invalid cmd ",
    252: "Invalid auth data",
    253: "Wrong username or password",
    254: "Passed authentication",

    300 : "already home_dir",

    400 : "dir_exists",
    401 : "mkdir_success!",
    402 : "rm_success!",
    403 : "the file or dir does not exist!",

    800: "the file exist,but not enough ,is continue? ",
    801: "the file exist !",
    802: " ready to receive datas",

    900: "md5 valdate success"

}


class ArgvHandler(object):
    def __init__(self):
        self.opt = optparse.OptionParser()

        self.opt.add_option("-s", "--host", dest="host", help="client_sel_ftp IP address")
        self.opt.add_option("-P", "--port", dest="port", help="client_sel_ftp port")
        self.opt.add_option("-u", "--username", dest="username", help="username")
        self.opt.add_option("-p", "--password", dest="password", help="password")

        self.options, self.args = self.opt.parse_args()
        self.verify_argv()
        self.make_connection()

        self.mainPath = os.path.dirname(os.path.abspath(__file__))

    def verify_argv(self):
        if int(self.options.port) > 0 and int(self.options.port) < 65535:
            return True
        else:
            exit("Err:host port must in 0-65535")

    def make_connection(self):
        self.sock = socket.socket()
        self.sock.connect((self.options.host, int(self.options.port)), )

    def interactive(self):
        if self.authenticate():
            print("---start interactive with you ...")
            while True:
                cmd_info = input("[%s]"%self.current_path).strip()
                if len(cmd_info)== 0:break
                cmd_list = cmd_info.split()
                if hasattr(self, "_%s"%cmd_list[0]):
                    func = getattr(self, "_%s"%cmd_list[0])
                    func(*cmd_list)
                else:
                    print("Invalid cmd")

    def authenticate(self):
        if self.options.username and self.options.password:
            return self.get_auth_result(self.options.username, self.options.password)
        else:
            username = input("input your username>>>").strip()
            password = input("input your password>>>").strip()
            return self.get_auth_result(username, password)

    def get_auth_result(self, user, pwd):
        data = {
            'action': 'auth',
            'username': user,
            'password': pwd,
        }
        self.sock.send(json.dumps(data).encode('utf8'))
        response = self.get_response()
        print("response", response)
        if response.get('status_code')==254:
            print("Passed authentication!")
            self.user = user
            self.current_path = "/"+user
            return True
        else:
            print(response.get("status_msg"))

    def get_response(self):
        resp_data = self.sock.recv(1024)
        resp_data = json.loads(resp_data.decode('utf8'))
        return resp_data

    def _post(self,*cmd_list):
        # post 1.jpg image
        action, local_path, target_path = cmd_list
        print("action, local_path, target_path",action, local_path, target_path)
        """
        [/lili]post img/1.jpg image/img
        action, local_path, target_path post img/1.jpg image/img
        """
        if "/" in local_path:
            local_path = os.path.join(self.mainPath,*(local_path.split("/")))
        else:
            local_path = os.path.join(self.mainPath, local_path)
        print("local_path",local_path)
        file_name = os.path.basename(local_path)
        file_size = os.stat(local_path).st_size

        # local_path为绝对路径

        data = {
            'action': 'post',
            'file_name': file_name,
            'file_size': file_size,
            'local_path':local_path,
            'target_path': target_path
        }

        self.sock.send(json.dumps(data).encode('utf8'))

        result_exist = str(self.sock.recv(1024), "utf8")

        has_sent = 0
        if result_exist == '800':
            choice = input("the file exist ,is_continue?[Y/N]").strip()
            if choice.upper() == 'Y':
                self.sock.send(b'Y')
                result_continue_pos = str(self.sock.recv(1024), "utf8")
                has_sent = int(result_continue_pos)
            else:
                self.sock.sendall(bytes("N","utf8"))

        elif result_exist == "801":
            print(STATUS_CODE[801])
            return

        file_obj = open(local_path, "rb")
        file_obj.seek(has_sent)
        start = time.time()
        while has_sent < file_size:
            data = file_obj.read(1024)
            self.sock.sendall(data)
            has_sent += len(data)

            self.progress_percent(has_sent, file_size)

        file_obj.close()
        end = time.time()
        print("cost %s s" % (end - start))
        print("post success!")

    def progress_percent(self,has, total):
        rate = float(has) / float(total)
        print_num = int(rate * 100)
        rate_num = int(rate * 70)

        # if self.last != rate_num:
        sys.stdout.write("%s%% %s\r" % (print_num, "#" * rate_num))

        # self.last = rate_num

    def _ls(self,*cmd_list):

        data = {
            'action':'ls',
            # 'user_current_path':self.current_path,
        }
        self.sock.send(json.dumps(data).encode())
        data = self.sock.recv(1024)
        print(data.decode("utf8"))

    def _pwd(self,cmd_list):

        data_header = {
            'action':'pwd',
         }

        self.sock.send(json.dumps(data_header).encode())
        data = self.sock.recv(1024)
        print(data.decode("utf8"))

    def _cd(self,*cmd_list):
        data = {
            'action': 'cd',
            'to_path': cmd_list[1],
            'user_current_path': self.current_path,
        }
        self.sock.send(json.dumps(data).encode())

        data = self.sock.recv(1024)
        # print(str(data,"utf8"))
        data = str(data,"utf8")
        if data == '300':
            print(STATUS_CODE[int(data)])
        else:
            self.current_path = '/' + os.path.basename(data)
        # print(self.current_path)  # /img

    def _mkdir(self,*cmd_list):
        data = {
            'action': 'mkdir',
            'dirname': cmd_list[1]
        }

        self.sock.send(json.dumps(data).encode('utf8'))
        data = self.sock.recv(1024)
        data = str(data, "utf8")
        print(STATUS_CODE[int(data)])

    def _rmdir(self,*cmd_list):
        data = {
            'action': 'rm',
            'target_path': cmd_list[1]
        }
        self.sock.send(json.dumps(data).encode('utf8'))
        data = self.sock.recv(1024)
        data = str(data, "utf8")
        print(STATUS_CODE[int(data)])




ch = ArgvHandler()
ch.interactive()
