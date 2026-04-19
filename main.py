# -*- coding: UTF-8 -*-
import json
import http.client
import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from contextlib import contextmanager

# ====================== SQLite 数据库配置 ======================
DB_FILE = "configs.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    finally:
        conn.close()

def init_db():
    with get_db() as c:
        c.execute('''
        CREATE TABLE IF NOT EXISTS anchors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            anchor_name TEXT UNIQUE NOT NULL,
            room TEXT NOT NULL,
            uid TEXT NOT NULL
        )
        ''')
        try:
            c.execute("INSERT OR IGNORE INTO anchors (anchor_name, room, uid) VALUES (?, ?, ?)", 
                      ("守护茶茶", "1440094", "37946996"))
        except:
            pass

init_db()

app = FastAPI(title="B站主播粉丝查询API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ====================== SQLite 配置操作（新增删除） ======================
def save_config(room, uid, anchor_name):
    with get_db() as c:
        c.execute('''
        INSERT OR REPLACE INTO anchors (anchor_name, room, uid)
        VALUES (?, ?, ?)
        ''', (anchor_name, room, uid))

def load_config():
    with get_db() as c:
        c.execute("SELECT anchor_name, room, uid FROM anchors")
        rows = c.fetchall()
        return [
            {"anchor_name": name, "room": room, "uid": uid}
            for name, room, uid in rows
        ]

def search_anchor(keyword):
    with get_db() as c:
        c.execute('''
        SELECT anchor_name, room, uid FROM anchors
        WHERE anchor_name LIKE ?
        ''', (f"%{keyword}%",))
        rows = c.fetchall()
        return [
            {"anchor_name": name, "room": room, "uid": uid}
            for name, room, uid in rows
        ]

# 新增：删除主播配置
def delete_anchor(anchor_name):
    with get_db() as c:
        c.execute("DELETE FROM anchors WHERE anchor_name = ?", (anchor_name,))
        return c.rowcount > 0  # 删除成功返回 True

# ====================== 查询逻辑 ======================
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
        except Exception:
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
    except Exception:
        return None
    return None

# ====================== API 接口（新增删除接口） ======================
class SearchRequest(BaseModel):
    roomid: str
    ruid: str
    keyword: str

class SaveConfigRequest(BaseModel):
    room: str
    uid: str
    anchor_name: str

class AnchorSearchRequest(BaseModel):
    keyword: str

# 新增：删除主播请求模型
class DeleteAnchorRequest(BaseModel):
    anchor_name: str

@app.get("/api/configs")
def api_get_configs():
    return {"data": load_config()}

@app.post("/api/save-config")
def api_save_config(req: SaveConfigRequest):
    save_config(req.room, req.uid, req.anchor_name)
    return {"msg": "保存成功"}

@app.post("/api/search")
def api_search(req: SearchRequest):
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

@app.post("/api/search-anchor")
def api_search_anchor(req: AnchorSearchRequest):
    keyword = req.keyword.strip()
    if not keyword:
        return {"data": load_config()}
    return {"data": search_anchor(keyword)}

# 新增：删除主播接口
@app.post("/api/delete-anchor")
def api_delete_anchor(req: DeleteAnchorRequest):
    if delete_anchor(req.anchor_name):
        return {"msg": "删除成功"}
    else:
        raise HTTPException(404, "主播不存在，删除失败")

@app.get("/")
def root():
    return {"msg": "B站查询API运行正常"}
