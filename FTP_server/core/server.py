#_author_ : duany_000
#_date_ : 2018/3/5
import socketserver
import configparser
import json
import os
from conf import settings
import shutil

STATUS_CODE  = {
    250 : "Invalid cmd format, e.g: {'action':'get','filename':'test.py','size':344}",
    251 : "Invalid cmd ",
    252 : "Invalid auth data",
    253 : "Wrong username or password",
    254 : "Passed authentication",
    255 : "Filename doesn't provided",
    256 : "File doesn't exist on server_sel_ftp",
    257 : "ready to send file",
    258 : "md5 verification",

    300 : "already home_dir",

    400 : "dir_exists",
    401 : "mkdir_success!",
    402 : "rm_success!",
    403 : "the file or dir does not exist!",

    800 : "the file exist,but not enough ,is continue? ",
    801 : "the file exist !",
    802 : " ready to receive datas",

    900 : "md5 valdate success"

}

class ServerHandler(socketserver.BaseRequestHandler):
    def handle(self):
        while True:
            data = self.request.recv(1024).strip()
            # print("data-----", data)
            if not data:break

            data = json.loads(data.decode("utf8"))
            print("data:", data)

            '''
            data = {'action':'auth',
                    'username':user,
                    'password':password}
            '''
            if data.get('action'):
                if hasattr(self, "_%s"% data.get('action')):
                    func = getattr(self, "_%s"% data.get('action'))
                    func(**data)
                else:
                    print("Invalid cmd!")
                    self.send_response(251)
            else:
                print("invalid cmd format")
                self.send_response(250)

    def send_response(self, status_code, data=None):
        """向客户端返回数据"""
        """
        response = {
            "status_code":245,
            "status_msg":"...",
            "data":"..."
        }
        """
        response = {"status_code":status_code, "status_msg":STATUS_CODE[status_code]}
        if data:
            response['data'] = data
        self.request.send(json.dumps(response).encode('utf8'))

    def _auth(self,**data):
        if data.get("username") is None or data.get("password") is None:
            self.send_response(252)

        user = self.authenticate(data.get("username"), data.get("password"))
        print(user)

        if not user:
            print("该用户用户名或密码错误...")
            self.send_response(253)
        else:
            self.user=user
            print("passed authentication",user)
            self.send_response(254)
            self.mainPath=os.path.join(settings.BASE_DIR,"home",self.user)  # 验证成功后，指定用户所属路径

    def authenticate(self,username,passwd):
        cfp = configparser.ConfigParser()
        cfp.read(settings.ACCOUNT_PATH)

        if username in cfp.sections():
            # print(".....",cfp[username]["Password"])
            Password=cfp[username]["Password"]
            if Password == passwd:
                print("auth pass!")
                return username  # 验证成功返回用户名，不成功返回None

    def _post(self,**data):
        file_name = data.get("file_name")
        file_size = data.get("file_size")
        target_path = data.get("target_path")
        local_path = data.get("local_path")
        print("file_name, file_size,local_path, target_path>>",file_name, file_size,local_path, target_path)
        abs_file_from = local_path
        if "/"in target_path:
            abs_file_to = os.path.join(self.mainPath, *(target_path.split("/")), file_name)
        else:
            abs_file_to = os.path.join(self.mainPath, target_path, file_name)
        print("abs_path", abs_file_to)

        has_received = 0

        if os.path.exists(abs_file_to):
            has_received = os.stat(abs_file_to).st_size
            if has_received < file_size:  # 文件存在但不完整
                self.request.send(b'800')

                is_continue = str(self.request.recv(1024), "utf8")
                if is_continue == "Y":
                    self.request.sendall(bytes(str(has_received), "utf8"))
                    f = open(abs_file_to, "ab")

            else:  # 文件完整存在
                self.request.send(b'801')
                return
        else:  # 文件未存在
            self.request.send(b'802')
            f = open(abs_file_to,'wb')

        while has_received < file_size:
            data = self.request.recv(1024)
            f.write(data)
            has_received += len(data)

        f.close()

    def _ls(self,**data):
        # user_current_path = data.get('user_current_path')
        # abs_current_path = os.path.join(settings.BASE_DIR,'home',*(user_current_path.split("/")))
        file_list = os.listdir(self.mainPath)

        file_str = '\n'.join(file_list)
        if not file_list:
            file_str = "<empty directory>"
        self.request.send(file_str.encode("utf8"))

    def _cd(self,**data):
        user_current_path = data.get('user_current_path')
        to_path = data.get('to_path')
        if to_path == '..':
            abs_user_current_path = os.path.join(settings.BASE_DIR,'home',*(user_current_path.split("/")))
            if abs_user_current_path == self.mainPath:
                self.request.sendall(b'300')
                return
            else:
                self.mainPath = os.path.dirname(self.mainPath)
        else:
            self.mainPath = os.path.join(self.mainPath,*(to_path.split("/")))

        print("abs_to_path>>",self.mainPath)

        self.request.send(self.mainPath.encode("utf8"))

    def _mkdir(self, **data):
        dirname = data.get("dirname")
        target_path = os.path.join(self.mainPath, *(dirname.split("/")))
        if not os.path.exists(target_path):
            if "/" in dirname:
                os.makedirs(target_path)  # 创建多级目录
            else:
                os.mkdir(target_path) # 创建单级目录
            self.request.sendall(bytes('401', 'utf8'))
        else:
            self.request.sendall(bytes('400','utf8'))

    def _rmdir(self,**data):
        dirname =data.get("dirname")

        tar_path=os.path.join(self.mainPath,dirname)
        if os.path.exists(tar_path):
            if os.path.isfile(tar_path):
                os.remove(tar_path) # 删除文件
            else:
                shutil.rmtree(tar_path) #删除目录

            self.request.send(b"402")
        else:
            self.request.send(b"403")

    def _pwd(self,**data):
        self.request.send(self.mainPath.encode("utf8"))

    def _post_md5(self,**data):

        file_name=data.get("file_name")
        file_size=data.get("file_size")
        target_path=data.get("target_path")
        print(file_name,file_size,target_path)
        abs_path=os.path.join(self.mainPath,target_path,file_name)
        print("abs_path",abs_path)

        has_received=0


        if os.path.exists(abs_path):
            has_file_size=os.stat(abs_path).st_size
            if has_file_size <file_size:
               self.request.sendall(b"800")

               is_continue=str(self.request.recv(1024),"utf8")
               if is_continue=="Y":
                    self.request.sendall(bytes(str(has_file_size),"utf8"))
                    has_received+=has_file_size
                    f=open(abs_path,"ab")

               else:
                    f=open(abs_path,"wb")
            else:
                self.request.sendall(b"801")
                return #注意这个return必须有

        else:
            self.request.sendall(b"802")
            f=open(abs_path,"wb")


        if data.get('md5'):
                print("hhhhhhhhhhh")
                md5_obj = hashlib.md5()

                while has_received<file_size:

                    try:
                        data=self.request.recv(1024)
                        if not data:
                            raise Exception
                    except Exception:

                        break

                    f.write(data)
                    has_received+=len(data)
                    recv_file_md5=md5_obj.update(data)
                    print("mmmmmm")

                else:
                    self.request.sendall(b"ok")#解决粘包
                    send_file_md5=self.request.recv(1024).decode("utf8")
                    print("send_file_md5",send_file_md5)
                    self.request.sendall("900".encode("utf8"))

        else:

            while has_received<file_size:

                try:
                    data=self.request.recv(1024)
                    if not data:
                        raise Exception
                except Exception:

                    break
            f.write(data)
            has_received+=len(data)

        f.close()











