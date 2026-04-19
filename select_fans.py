# -*- coding: UTF-8 -*-
import json
import http.client
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

# 配置文件
CONFIG_FILE = "user_config.json"
app = FastAPI(title="B站主播粉丝查询API")

# 允许跨域（小程序必须）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== 配置保存/加载 ======================
def save_config(room, uid, anchor_name=""):
    config_path = Path(CONFIG_FILE)
    configs = []
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                if not isinstance(configs, list):
                    configs = []
        except:
            configs = []

    exists = False
    for config in configs:
        if config.get("anchor_name") == anchor_name:
            config["room"] = room
            config["uid"] = uid
            exists = True
            break

    if not exists:
        configs.append({
            "room": room,
            "uid": uid,
            "anchor_name": anchor_name
        })

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(configs, f, ensure_ascii=False)

def load_config():
    config_path = Path(CONFIG_FILE)
    default_config = [{"room": 1440094, "uid": 37946996, "anchor_name": "守护茶茶"}]

    if not config_path.exists():
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, ensure_ascii=False)
            return default_config
        except:
            return default_config

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            configs = json.load(f)
            if isinstance(configs, list) and len(configs) > 0:
                return configs
    except:
        return default_config
    return default_config

# ====================== 核心查询逻辑 ======================
def http_request(url):
    conn = http.client.HTTPSConnection("api.live.bilibili.com")
    conn.request("GET", url)
    res = conn.getresponse()
    return json.loads(res.read().decode('utf-8'))

def get_funs(user_name, ruid, flag=1):
    page = 0
    while True:
        page += 1
        page_size = 30
        url = f"/xlive/general-interface/v1/rank/getFansMembersRank?ruid={ruid}&page={page}&page_size={page_size}"
        try:
            ret = http_request(url)
            if not ret.get("data") or not ret["data"].get("item"):
                return None
            c_list = ret["data"]["item"]
            for data in c_list:
                uname = str(data.get("name", ""))
                uuid = str(data.get("uid", ""))
                if (flag == 1 and (user_name in uname or user_name == uuid)) or \
                   (flag == 0 and (user_name == uname or user_name == uuid)):
                    return data
        except Exception as e:
            return None
    return None

def get_captain(user_name, roomid, ruid, flag=1):
    try:
        page = 1
        page_size = 30
        url = f"/xlive/app-room/v2/guardTab/topList?roomid={roomid}&page={page}&ruid={ruid}&page_size={page_size}"
        ret = http_request(url)
        if not ret.get("data"):
            return None

        c_list = ret["data"].get("list", []) + ret["data"].get("top3", [])
        for data in c_list:
            uname = str(data.get("username", ""))
            uuid = str(data.get("uid", ""))
            if (flag == 1 and (user_name in uname or user_name == uuid)) or \
               (flag == 0 and (user_name == uname or user_name == uuid)):
                return data

        while True:
            page += 1
            url = f"/xlive/app-room/v2/guardTab/topList?roomid={roomid}&page={page}&ruid={ruid}&page_size={page_size}"
            ret = http_request(url)
            tmp_list = ret["data"].get("list", [])
            if not tmp_list:
                break
            for data in tmp_list:
                uname = str(data.get("username", ""))
                uuid = str(data.get("uid", ""))
                if (flag == 1 and (user_name in uname or user_name == uuid)) or \
                   (flag == 0 and (user_name == uname or user_name == uuid)):
                    return data
    except Exception as e:
        return None
    return None

# ====================== API 接口 ======================
class SearchRequest(BaseModel):
    roomid: str
    ruid: str
    keyword: str

class SaveConfigRequest(BaseModel):
    room: str
    uid: str
    anchor_name: str

@app.get("/api/configs")
def api_get_configs():
    """获取所有主播配置"""
    return {"data": load_config()}

@app.post("/api/save-config")
def api_save_config(req: SaveConfigRequest):
    """保存主播配置"""
    save_config(req.room, req.uid, req.anchor_name)
    return {"msg": "保存成功"}

@app.post("/api/search")
def api_search(req: SearchRequest):
    """查询用户信息"""
    keyword = req.keyword.strip()
    roomid = req.roomid.strip()
    ruid = req.ruid.strip()

    if not keyword or not roomid or not ruid:
        raise HTTPException(400, "参数不能为空")

    captain = get_captain(keyword, roomid, ruid)
    fans = get_funs(keyword, ruid)

    result = {
        "name": keyword,
        "uid": "",
        "captain_rank": "不是舰长",
        "fans_name": "",
        "medal_level": "",
        "fans_rank": "不在粉丝团或牌子已灰"
    }

    if captain:
        result["name"] = captain.get("username", keyword)
        result["uid"] = str(captain.get("uid", ""))
        result["captain_rank"] = str(captain.get("rank", ""))
        medal = captain.get("medal_info", {})
        result["fans_name"] = medal.get("medal_name", "")
        result["medal_level"] = str(medal.get("medal_level", ""))

    if fans:
        result["name"] = fans.get("name", result["name"])
        result["uid"] = str(fans.get("uid", result["uid"]))
        result["fans_name"] = fans.get("medal_name", result["fans_name"])
        result["medal_level"] = str(fans.get("level", result["medal_level"]))
        result["fans_rank"] = str(fans.get("user_rank", ""))

    return result

@app.get("/")
def root():
    return {"msg": "B站查询API运行正常"}
