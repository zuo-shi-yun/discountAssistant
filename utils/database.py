"""
处理数据库操作。实现数据库CRUD逻辑
"""
import logging
import re
import sqlite3
from datetime import datetime
from sqlite3 import Cursor
from typing import List


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
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def __execute__(self, *args, **kwargs) -> Cursor:
        c = self.cursor.execute(*args, **kwargs)
        self.conn.commit()
        return c

    def insert(self, insert_data: dict) -> Cursor:
        """插入数据"""
        insert_key = '`' + '` ,`'.join(list(insert_data.keys())) + '`'
        insert_value = ', '.join((f'"{v}"' if isinstance(v, str) else f'{v}') for v in insert_data.values())
        sql = f"insert into {self.database} ({insert_key}) values ({insert_value})"
        return self.__execute__(sql)

    def update(self, update_data: dict, where_data: dict) -> Cursor:
        """更新数据"""
        update_data = [(f'`{k}`="{v}"' if isinstance(v, str) else f'`{k}`={v}') for k, v in update_data.items()]
        update_data = ' ,'.join(update_data)
        where_data = [(f'`{k}`="{v}"' if isinstance(v, str) else f'`{k}`={v}') for k, v in where_data.items()]
        where_data = ' and '.join(where_data)
        sql = f"update {self.database} set {update_data} where {where_data}"
        return self.__execute__(sql)

    def delete(self, where_delete: dict) -> Cursor:
        """删除数据"""
        where_delete = [(f'`{k}`="{v}"' if isinstance(v, str) else f'`{k}`={v}') for k, v in where_delete.items()]
        where_delete = ' and '.join(where_delete)
        sql = f"delete from {self.database} where {where_delete}"
        return self.__execute__(sql)

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
            query_where = ' and '.join(
                [f'`{k}` like "{v.pattern}"' if isinstance(v, re.Pattern)
                 else f'`{k}`="{v}"' if isinstance(v, str) else f'`{k}`={v}'
                 for k, v in query_where.items()])
            sql += f" where {query_where}"

        # 逆序
        if reverse:
            sql += ' order by id desc'

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

        logging.info('数据库初始化成功')

    def close(self):
        self.conn.close()

    def __del__(self):
        self.close()

    def get_today_all_message(self) -> List[str]:
        """得到当天的全部优惠卷信息"""
        month = datetime.now().month
        day = datetime.now().day
        sql = "select mes from saleMes where `time` like '{:02}-{:02} %:%'".format(month, day)
        c = self.__execute__(sql)
        ret = []
        for i in c:
            ret.append(i[0])
        return ret
