"""
处理数据库操作。实现数据库CRUD逻辑
"""
import io
import logging
import re
import sqlite3
from datetime import datetime
from sqlite3 import Cursor
from typing import List

import numpy as np


class DatabaseManager:
    """数据库"""

    conn = None
    cursor = None

    def __init__(self, database_name: str = None):
        self.reconnect()
        self.database = database_name

    # 连接到数据库文件
    def reconnect(self):
        """连接到数据库"""
        self.conn = sqlite3.connect('plugins/discountAssistant/database.db', check_same_thread=False)
        # self.conn = sqlite3.connect('database.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # 当插入数据的时候将array转换为text插入
        sqlite3.register_adapter(np.ndarray, self.adapt_array)

        # 当查询数据的时候将text转换为array
        sqlite3.register_converter("array", self.convert_array)
        self.cursor = self.conn.cursor()

    def __execute__(self, *args, **kwargs) -> Cursor:
        c = self.cursor.execute(*args, **kwargs)
        self.conn.commit()
        return c

    def insert(self, insert_data: dict) -> Cursor:
        """插入数据"""
        insert_key = '`' + '` ,`'.join(list(insert_data.keys())) + '`'
        # insert_value = ', '.join((f'"{v}"' if isinstance(v, str) else f'{v}') for v in insert_data.values())
        insert_value = ', '.join(['?' for i in range(len(insert_data))])
        sql = f"insert into {self.database} ({insert_key}) values ({insert_value})"
        return self.__execute__(sql, tuple(insert_data.values()))

    def update(self, update_data: dict, where_data: dict) -> Cursor:
        """更新数据"""
        # update_data = [(f'`{k}`="{v}"' if isinstance(v, str) else f'`{k}`={v}') for k, v in update_data.items()]
        update_data_sql = [f'`{k}`=?' for k, v in update_data.items()]
        update_data_sql = ' ,'.join(update_data_sql)
        where_data_sql = [f'`{k}`=?' for k, v in where_data.items()]
        where_data_sql = ' and '.join(where_data_sql)
        sql = f"update {self.database} set {update_data_sql} where {where_data_sql}"
        return self.__execute__(sql, tuple(update_data.values()) + tuple(where_data.values()))

    def delete(self, where_delete: dict) -> Cursor:
        """删除数据"""
        where_delete_sql = [f'`{k}`=?' for k, v in where_delete.items()]
        where_delete_sql = ' and '.join(where_delete_sql)
        sql = f"delete from {self.database} where {where_delete_sql}"
        return self.__execute__(sql, tuple(where_delete.values()))

    def query(self, query_col: List[str], query_where: dict = None, reverse: bool = True) -> list:
        """查询数据.查询条件只实现了and关系"""
        # 构建查询列
        if len(query_col) == 1 and query_col[0] == '*':
            query_col_sql = '*'
        else:
            query_col_sql = '`' + '` ,`'.join(query_col) + '`'

        sql = f"select {query_col_sql} from {self.database}"

        # 构建查询条件
        if query_where:
            # 使用正则表达式代表模糊查询,正则的模式代表模糊查询模式
            query_where_sql = ' and '.join(
                [f'`{k}` like ?' if isinstance(v, re.Pattern)
                 else f'`{k}`=?'
                 for k, v in query_where.items()])
            sql += f" where {query_where_sql}"

        # 逆序
        if reverse:
            sql += ' order by id desc'

        if query_where:
            rows = self.__execute__(sql, tuple([v.pattern if isinstance(v, re.Pattern) else v
                                                for v in query_where.values()]))
        else:
            rows = self.__execute__(sql)

        res = []
        if len(query_col) == 1 and query_col[0] != '*':  # 只查询一行
            for row in rows:
                res.append(row[0])
        else:  # 查询多行
            for row in rows:  # 遍历行
                temp_res = {}
                for key in row.keys():  # 遍历列
                    temp_res[key] = row[key]  # 添加单元
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
        # 添加encode列
        try:
            self.__execute__("alter table saleMes add column encode array")
        except:  # 如果已经有该列则跳过
            pass

        # group_mes_control表
        self.__execute__("""
        create table if not exists  `groupMesControl` (
            `id` INTEGER PRIMARY KEY AUTOINCREMENT,
            `qq` int,
            `is_continuous_mes` int,
            `send_qq` text,
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

        logging.debug('数据库检测完毕')

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()

    def get_today_all_message(self) -> List[dict]:
        """得到当天的全部优惠卷信息"""
        month = datetime.now().month
        day = datetime.now().day

        return self.query(['mes', 'encode'], {'time': re.compile('{:02}-{:02} %:%'.format(month, day))})

    @staticmethod
    def adapt_array(arr):
        out = io.BytesIO()
        np.save(out, arr)
        out.seek(0)
        return sqlite3.Binary(out.read())

    @staticmethod
    def convert_array(text):
        out = io.BytesIO(text)
        out.seek(0)
        return np.load(out, allow_pickle=True)
