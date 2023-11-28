"""
数据库管理模块
"""
import sqlite3
from sqlite3 import Cursor
from typing import List


class DatabaseManager:
    """封装数据库底层操作，并提供方法给上层使用"""

    conn = None
    cursor = None

    def __init__(self, database_name: str = None):
        self.reconnect()
        self.database = database_name

    # 连接到数据库文件
    def reconnect(self):
        """连接到数据库"""
        self.conn = sqlite3.connect('plugins/discountAssistant/database.db', check_same_thread=False)
        self.cursor = self.conn.cursor()

    def __execute__(self, *args, **kwargs) -> Cursor:
        c = self.cursor.execute(*args, **kwargs)
        self.conn.commit()
        return c

    def insert(self, insert_data: dict) -> Cursor:
        """插入数据"""
        insert_key = '`' + '` ,`'.join(list(insert_data.keys())) + '`'
        insert_value = "'" + "' ,'".join(list(insert_data.values())) + "'"
        sql = f"insert into {self.database} ({insert_key}) values ({insert_value})"
        return self.__execute__(sql)

    def update(self, update_data: dict, where_data: dict) -> Cursor:
        """更新数据"""
        update_data = [f'`{k}`="{v}"' for k, v in update_data.items()]
        update_data = ' ,'.join(update_data)
        where_data = [f'`{k}`="{v}"' for k, v in where_data.items()]
        where_data = ' and '.join(where_data)
        sql = f"update {self.database} set {update_data} where {where_data}"
        return self.__execute__(sql)

    def delete(self, where_delete: dict) -> Cursor:
        """删除数据"""
        where_delete = [f'`{k}`="{v}"' for k, v in where_delete.items()]
        where_delete = ' and '.join(where_delete)
        sql = f"delete from {self.database} where {where_delete}"
        return self.__execute__(sql)

    def query(self, query_col: List[str], query_where: dict = None) -> list:
        """查询数据"""
        query_col_sql = '`' + '` ,`'.join(query_col) + '`'
        query_where = ' and '.join([f'`{k}`="{v}"' for k, v in query_where.items()])

        sql = f"select {query_col_sql} from {self.database}"
        if query_where:
            sql += f" where {query_where}"
            
        c = self.__execute__(sql)

        res = []
        if len(query_col) == 1:  # 只查询一行
            for i in c:
                res.append(i[0])
        else:  # 查询多行
            temp_res = {}
            for i in c:
                for col in range(len(query_col)):
                    temp_res[query_col[col]] = i[col]
                res.append(temp_res)

        return res

    # 初始化数据库
    def init_database(self):
        """
        初始化数据库
        :return:
        """
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
