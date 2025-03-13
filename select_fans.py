

import os
import tkinter as tk
from tkinter import ttk
import http.client
import json
import base64
from PIL import ImageTk
from pathlib import Path

ICON_DATA = "AAABAAEAEBAAAAEAGABoAwAAFgAAACgAAAAQAAAAIAAAAAEAGAAAAAAAAAAAAMQOAADEDgAAAAAAAAAAAABzM/5zM/5zM/5zM/5yMv1zM/5zM/5yMv1yMv1zM/5yMv1zM/5yMv1zM/5zM/52M/91Nv52N/91Nv51Nf9zM/5zM/5zMv9zMv9zMv9zM/5zMv9zM/5zM/5zM/51Nf91Nv54Ov53Of11Nv51Nf9yMv1zNPxzNflzM/50M/tzNPxzM/5zM/5zNftzMv9zM/54Ov56Pv54PPx5Pf2PX/uQXv+PXvyOXP2OXP2UXv+RX/+QXv+OXP2MWf18RfZ5Pf16Pv6BQvyBQvyQX/2IVPx6Pv57Qf56Pv56Pv57P/16Pv58QP97Qf5+RP2QX/17P/2BQf6FSP5/Rvz9/f39/f17S9l9SOyBRf2hgs2CSPr9/f337f6ARvl8UsmaZP57ROGDRvyGSf+CSv3+/v6BQ+n9/f359Pb89vv8/fucZ/T//f3l1Pb8/fn17PmbedB6RdKGSf+ITfuJTv36/viET96NUvr+//X6+vr+//udfdaCU9eFT+mMUfmMacCbceZ7TNCETfyNVP2HU/r++v+JUPmfb/378/37/vy9rM389P6ldf2fb/2igdyHU+egd+qGUOqNVP2PV/ySXPv89PuPVviNU/+MVvX9+/qQVP/+//uNVP2NU/+NU/+ie+mjd/qNVP2PV/yTXf6je+v59P2QXvKQWP2NVfqRWPqQWvv//fyPV/yQWP2QWfyRX/OofP6QWP2SXPuVYfuWYvyXYfqpff+pff+pff+pfv2nfPumev2ne/2pfv2pff+ofP6ZavaVX/6VYfuXZPuXZviZZf+VYfuYZf2XafKtgfyca/eaa/epgPqlePeWY/uXY/2XY/2XY/2XZPuaafmWaP6cZ/6cZv+cZ/6thP2icvqYZf2cZ/6ca/2ngPqZZv2cZ/6cZ/6cZ/6aafmcaviaaviebf2dbP6ca/udbP6ca/ucbPqca/2aav6ebf2ebf+cbPqgb/+ca/ucbfmcbfmcbfmcbfmeb/ucbfmcbfmeb/ucbfmcbfmcbfmcbfmcbfmeb/ucbfmeb/uecPkAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
CONFIG_FILE = "user_config.json"

def save_config(room, uid):
    """ 保存配置到JSON文件 """
    data = {"room": room, "uid": uid}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)

def load_config():
    """ 加载配置文件 """
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except:
            return {"room": "", "uid": ""}
    return {"room": "", "uid": ""}


class BiliQueryApp:
    def __init__(self, master):
        self.master = master
        self.screenwidth = self.master.winfo_screenwidth()
        self.screenheight = self.master.winfo_screenheight()
        self.width = 450
        self.height = 400
        self.ck_str = '%dx%d+%d+%d' % (self.width, self.height, (self.screenwidth-self.width)/2, (self.screenheight-self.height)/2)

        master.title("B站主播粉丝查询工具")
        master.geometry(self.ck_str)
        master.resizable(False, False)
        self.config = load_config()
        
        # 初始化界面
        self.create_widgets()
        self.setup_styles()
        
        # 测试数据
        self.test_data = {
            'name': "",
            'uid': "",
            'captain_rank': "",
            'medal_level': "",
            'fans_rank': "",
            'fans_name': ""
        }

    def setup_styles(self):
        """配置界面样式"""
        style = ttk.Style()
        style.configure('Title.TLabel', font=('微软雅黑', 14, 'bold'), padding=5)
        style.configure('Result.TLabel', 
                       foreground='#333333',
                       background='#FFFFFF',
                       font=('Consolas', 10),
                       padding=5,
                       relief='groove')

    def create_widgets(self):
        """创建界面组件"""
        # 主容器
        main_frame = ttk.Frame(self.master, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        row1_frame = ttk.Frame(main_frame)
        row1_frame.pack(fill=tk.BOTH, expand=True)
        validate_cmd = row1_frame.register(self.validate_digit)

        # 创建标签和输入框组
        tk.Label(row1_frame, text="房间号:").pack(side=tk.LEFT, pady=5)
        self.room_entry = tk.Entry(row1_frame, validate="key", validatecommand=(validate_cmd, '%S'), width=20)
        self.room_entry.insert(0, self.config.get("room", "")) 
        self.room_entry.pack(side=tk.LEFT,pady=5)

        tk.Label(row1_frame, text="主播UID:").pack(side=tk.LEFT, pady=5)
        self.uid_entry = tk.Entry(row1_frame, validate="key", validatecommand=(validate_cmd, '%S'), width=20)
        self.uid_entry.insert(0, self.config.get("uid", "")) 
        self.uid_entry.pack(side=tk.LEFT, pady=5)

        # 输入区域
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=5)
        
        self.search_entry = ttk.Entry(input_frame, width=30)
        self.search_entry.pack(side=tk.LEFT)
        
        search_btn = ttk.Button(
            input_frame,
            text="查询",
            command=self.on_search
        )
        search_btn.pack(side=tk.LEFT)

        # 结果展示区
        result_frame = ttk.LabelFrame(main_frame, text="查询结果")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # 结果项定义
        self.result_labels = {
            'name': self.create_result_row(result_frame, 0, "用户名"),
            'uid': self.create_result_row(result_frame, 1, "UID"),
            'captain_rank': self.create_result_row(result_frame, 2, "舰长排名"),
            'fans_name': self.create_result_row(result_frame, 3, "粉丝牌"),
            'medal_level': self.create_result_row(result_frame, 4, "粉丝牌等级"),
            'fans_rank': self.create_result_row(result_frame, 5, "粉丝团排名")
        }

        # 状态栏
        self.status_var = tk.StringVar()
        ttk.Label(main_frame, textvariable=self.status_var,
                relief=tk.SUNKEN).pack(fill=tk.X)

    def create_result_row(self, parent, row, title):
        """创建单行结果展示组件"""
        ttk.Label(parent, text=title+":", width=10, anchor=tk.E).grid(
            row=row, column=0, padx=5, pady=3, sticky=tk.E)
        
        result_var = tk.StringVar()
        label = ttk.Label(parent, textvariable=result_var, 
                        style='Result.TLabel', width=25)
        label.grid(row=row, column=1, padx=5, pady=3, sticky=tk.W)
        return result_var

    def validate_digit(self, char):
        return char.isdigit() or char == ""  # 允许退格操作

    def on_search(self):
        """查询按钮回调"""
        roomid = self.room_entry.get().strip()
        ruid = self.uid_entry.get().strip()
        if not roomid:
            self.status_var.set("请输入房间号")
            return 
        if not ruid:
            self.status_var.set("请输入主播uid")
            return 

        save_config(roomid, ruid)
        keyword = self.search_entry.get().strip()
        if not keyword:
            self.status_var.set("请输入查询条件(uid或b站用户名)")
            return
        
        # 模拟查询过程
        self.status_var.set("查询中...")
        self.clear_results()
    
        self.master.update_idletasks() 

        # 使用测试数据更新界面
        ret = self.get_captain(keyword, roomid, ruid)
        fun_ret = self.get_funs(keyword, roomid, ruid)
        if not ret:
            self.test_data["captain_rank"] = "不是舰长"
            if fun_ret:
                self.test_data["name"] = fun_ret["name"]
                self.test_data["uid"] = fun_ret["uid"]
                self.test_data["medal_level"] = fun_ret["level"]
                self.test_data["fans_rank"] = fun_ret["user_rank"]
                self.test_data["fans_name"] = fun_ret["medal_name"]
            else:
                self.test_data["name"] = keyword
                self.test_data["fans_rank"] = "不在粉丝团或牌子已灰"
        else:
            self.test_data["name"] = ret["username"]
            self.test_data["uid"] = ret["uid"]
            self.test_data["captain_rank"] = ret["rank"]
            self.test_data["medal_level"] = ret["medal_info"]["medal_level"]
            self.test_data["fans_name"] = ret["medal_info"]["medal_name"]
            if fun_ret:
                self.test_data["fans_rank"] = fun_ret["user_rank"]
            else:
                self.test_data["fans_rank"] = "不在粉丝团或牌子已灰"

        self.update_results(self.test_data)
        self.status_var.set("查询完成")

    def clear_results(self):
        """清空结果"""
        for var in self.result_labels.values():
            var.set("")

    def update_results(self, data):
        """更新结果显示"""
        print("[DEBUG] 更新数据:", data)  # 调试输出
        
        # 直接通过字典键更新
        self.result_labels['name'].set(data.get('name', '无记录'))
        self.result_labels['uid'].set(data.get('uid', '无记录'))
        self.result_labels['fans_name'].set(data.get('fans_name', '无记录'))
        self.result_labels['captain_rank'].set(data.get('captain_rank', '无记录'))
        self.result_labels['medal_level'].set(data.get('medal_level', '无记录'))
        self.result_labels['fans_rank'].set(data.get('fans_rank', '无记录'))

        # 强制界面刷新
        self.master.update_idletasks()

    def http_request(self, url):
        """统一请求处理"""
        conn = http.client.HTTPSConnection("api.live.bilibili.com")
        conn.request("GET", url)
        res = conn.getresponse()
        return json.loads(res.read())

    def get_funs(self, user_name, roomid, ruid, flag=1):
        page = 0
        while True:
            c_list = []
            page += 1
            page_size = 30
            url = "https://api.live.bilibili.com/xlive/general-interface/v1/rank/getFansMembersRank?ruid=%s&page=%s&page_size=%s"%(ruid, page, page_size)
            ret = self.http_request(url)
            c_list = ret["data"]["item"]
            if not c_list or len(c_list) == 0:
                break
            for data in c_list:
                print(data)
                if flag == 1:
                    if user_name.strip() in data["name"] or user_name.strip() == str(data["uid"]):
                        return data
                elif flag == 0:
                    if user_name.strip() == data["name"] or user_name.strip() == str(data["uid"]):
                        return data 
        return False


    def get_captain(self, user_name, roomid, ruid, flag=1):
        c_list = []
        page = 1
        page_size = 30
        url = "https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topList?roomid=%s&page=%s&ruid=%s&page_size=%s"%(roomid, page, ruid, page_size)
        ret = self.http_request(url)
        tmp_list = ret["data"]["list"]
        c_list = c_list + tmp_list
        tmp_list = ret["data"]["top3"]
        c_list = c_list + tmp_list
        for data in c_list:
            print(data)
            if flag == 1:
                if user_name.strip() in data["username"] or user_name.strip() == str(data["uid"]):
                    return data
            elif flag == 0:
                if user_name.strip() == data["username"] or user_name.strip() == str(data["uid"]):
                    return data

        while True:
            c_list = []
            page += 1
            url = "https://api.live.bilibili.com/xlive/app-room/v2/guardTab/topList?roomid=%s&page=%s&ruid=%s&page_size=%s"%(roomid, page, ruid, page_size)
            ret = self.http_request(url)
            tmp_list = ret["data"]["list"]
            if len(tmp_list) == 0:
                break
            c_list = c_list + tmp_list
            for data in c_list:
                print(data)
                if flag == 1:
                    if user_name.strip() in data["username"] or user_name.strip() == str(data["uid"]):
                        return data
                elif flag == 0:
                    if user_name.strip() == data["username"] or user_name.strip() == str(data["uid"]):
                        return data

        return False


if __name__ == "__main__":
    root = tk.Tk()
    app = BiliQueryApp(root)
    tmp = open("tmp.ico", "wb")
    tmp.write(base64.b64decode(ICON_DATA))
    tmp.close()
    root.iconbitmap("tmp.ico")
    os.remove("tmp.ico") 
    root.mainloop()
