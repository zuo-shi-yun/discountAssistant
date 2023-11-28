"""
数据库管理模块
"""
import sqlite3
from sqlite3 import Cursor


class DatabaseManager:
    """封装数据库底层操作，并提供方法给上层使用"""

    conn = None
    cursor = None

    def __init__(self):
        self.reconnect()

    # 连接到数据库文件
    def reconnect(self):
        """连接到数据库"""
        self.conn = sqlite3.connect('plugins/discountAssistant/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

    def __execute__(self, *args, **kwargs) -> Cursor:
        c = self.cursor.execute(*args, **kwargs)
        self.conn.commit()
        return c

    def init_database(self):
        # listen_qq表
        self.__execute__("""
        create table if not exists  `listenQQ` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
           `listen_qq` int
           )""")

        # keyword表
        self.__execute__("""
        create table if not exists  `keyword`(
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `qq` int,
            `keywords` text,
            `send_mes` int,
            `qq_type` int
        )
        """)

        # sale_mes表
        self.__execute__("""
        create table if not exists  `saleMes` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `mes` text,
            `keyword` text,
            `code` text,
            `time` text,
            `src_mes` text,
            `receive_qq` text,
            `send_qq` text,
            `image_url` text            
        )
        """)

        # group_mes_control表
        self.__execute__("""
        create table if not exists  `groupMesControl` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `group_qq` int,
            `send_qq` ,
            `last_no` int,
            `context_num` int,
            `last_mes` text,
            `last_time` text, 
            `mes_image_url` text,
            `context_qq` text,
            `qq_type` text,
            `mes_id` text                               
        )
        """)

        # all_mes表
        self.__execute__("""
        create table if not exists  `allMes` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `mes` text,
            `time` text,
            `receive_qq` int,
            `image_url` text
        )
        """)

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()
