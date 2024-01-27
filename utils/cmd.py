"""处理用户指令。实现用户与系统交互逻辑"""
import base64
import re
import time
from threading import Thread

from mirai import Image, Plain
from plugins.discountAssistant.utils.HostConfig import HostConfig
from plugins.discountAssistant.utils.clear import clear_task
from plugins.discountAssistant.utils.database import DatabaseManager
from plugins.discountAssistant.utils.md.data_source import md_to_pic
from plugins.discountAssistant.utils.message import Message, HandleMessage

from pkg.plugin.host import PluginHost


class HandleCmd:
    """处理用户指令"""

    def __init__(self, config, cmd: str, param: list, **kwargs):
        self.host = PluginHost()
        self.cfg = config

        self.mes_chain = kwargs.get('message_chain')  # 消息链
        self.qq = kwargs.get('launcher_id')  # 发起者id,用户qq号或群qq号
        self.sender_id = kwargs.get('sender_id')  # 发送者id
        self.launcher_type = 0 if kwargs.get('launcher_type') == 'person' else 1  # 消息类型:0个人1群
        self.ret_msg = ''
        self.e = None  # 异常

        self.cmd = cmd  # 用户命令
        self.param = param  # 命令参数

        self.had_handle_cmd = self.handle()  # 处理流程

    # 处理指令
    def handle(self) -> bool:
        """处理指令"""
        handle_func = {
            '优惠': self.help,
            '添加群': self.insert_group,
            '添加关键字': self.insert_keyword,
            '查询优惠券': self.query_sale_message,
            '查询优惠卷': self.query_sale_message,
            '查询优惠劵': self.query_sale_message,
            '查询所有信息': self.query_all_message,
            '查询关键字': self.query_keywords,
            '打开发送': self.open_message,
            '查询原信息': self.query_src_mes,
            '查询相关信息': self.query_context_mes,
            '关闭发送': self.close_message,
            '删除群': self.delete_group,
            '删除关键字': self.delete_keyword,
            '删除关键字序号': self.delete_keyword_by_no,
            '清理数据库': self.clear_database
        }

        if self.cmd in handle_func:  # 是本插件处理指令
            handle_func[self.cmd]()  # 处理指令
            return True
        else:
            return False

    # 异常包裹器
    @staticmethod
    def exception_decorator(func):
        def wrapper(self, *args, **kwargs):  # self is the instance of class A
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                self.ret_msg = f'失败!{e}'
                self.e = e

        return wrapper

    # 帮助
    @exception_decorator
    def help(self):
        """帮助"""
        md_image = md_to_pic(md_path=r'plugins\discountAssistant\HELP.md', width=1050)
        b64_img = base64.b64encode(md_image).decode()
        self.ret_msg = Image(base64=b64_img, width=1050, height=5000)

    # 添加监听群
    @exception_decorator
    def insert_group(self):
        # 添加监听群数据库
        svc_listen_qq = DatabaseManager('listenQQ')
        src_qq_group = svc_listen_qq.query(['listen_qq'])  # 已有监听群
        # 是否已经监听该群
        if int(self.param[0]) not in src_qq_group:  # 没有监听
            svc_listen_qq.insert({'listen_qq': self.param[0]})
            # 添加群管理数据库
            svc_group_control = DatabaseManager('groupMesControl')
            svc_group_control.insert({'qq': self.param[0], 'is_continuous_mes': 0, 'last_no': 0, 'context_num': 0})
            self.ret_msg = f'成功,请确保已请将我邀请进这个QQ群^_^\n本系统目前共在{len(src_qq_group) + 1}个群中搜索,本系统具有基于文本相似度算法的去重功能,不必担心消息重复'
        else:
            self.ret_msg = '我已经监听了这个群,无需重复添加'

    @classmethod
    def get_keyword_re(cls, param, src_keywords):
        ret_msg = ''
        # 构建关键字re
        if len(param) >= 2:  # 多关键字情况
            if param[1] == '不包含':  # 不包含某关键字
                ban_keyword = ''  # 不包含关键字re表达式
                for i in range(2, len(param)):  # 构建re
                    ban_keyword += f'(?!.*{param[i]})'
                keyword = f'^{ban_keyword}.*{param[0]}.*$'  # 最终关键字re
                if keyword in src_keywords:  # 已经监听了关键字
                    ret_msg = '我已经监听了这个关键字,无需重复添加'
                    return False, '', ret_msg
            elif param[1] == '同时包含':  # 同时包含某关键字:
                include_keyword = f'(?=.*{param[0]})'
                for i in range(2, len(param)):
                    include_keyword += f'(?=.*{param[i]})'
                keyword = include_keyword  # 最终关键re
                if keyword in src_keywords:  # 已经监听关键字
                    ret_msg = '我已经监听了这个关键字,无需重复添加'
                    return False, '', ret_msg
            else:  # 一次性添加多个关键字
                keyword = []  # 关键字
                ret_mes = ''
                for i in param:  # 遍历关键字
                    if i in src_keywords:
                        ret_mes += f'我已经监听了关键字{i},无需重复添加\n'
                    else:
                        ret_mes += f'成功添加关键字:{i}\n'
                        keyword.append(i)
                ret_mes += '若筛选到含有关键字的消息将自动发送给你,若不希望自动发送,请发送“关闭发送”'
                ret_msg = ret_mes
                keyword = ' '.join(keyword)  # 最终关键字
        else:  # 只添加一个关键字
            if param[0] in src_keywords:
                ret_msg = '我已经监听了这个关键字,无需重复添加'
                return False, '', ret_msg
            keyword = f'{param[0]}'  # 最终关键字

        return True, keyword, ret_msg

    # 添加关键字
    @exception_decorator
    def insert_keyword(self):
        """添加关键字"""
        svc = DatabaseManager('keyword')  # 关键字数据库
        qq_list = svc.query(['QQ'])  # 已有发送qqqq号列表
        if self.qq in qq_list:  # 如果该qq号已经添加过关键字
            src_keywords = svc.query(['keywords'], {'QQ': self.qq})[0].split()  # 已有关键字
        else:
            src_keywords = []

        flag_insert_keyword, keyword, self.ret_msg = self.get_keyword_re(self.param, src_keywords)

        if flag_insert_keyword:  # 需要插入新关键字
            # 更新数据库
            if self.qq in qq_list:  # 如果该qq号已经添加过关键字
                new_keyword = svc.query(['keywords'], {'qq': self.qq})[0] + ' ' + keyword
                svc.update({'keywords': new_keyword}, {'qq': self.qq})  # 更新数据库
            else:
                svc.insert({'qq': self.qq, 'keywords': keyword, 'send_mes': 1, 'qq_type': self.launcher_type})
        # 若已有回复信息则使用原有信息
        self.ret_msg = self.ret_msg or f'成功,若筛选到含有关键字的消息将自动发送给你,若不希望自动发送,请发送“关闭发送”\n检索关键字为:{keyword}'

    # 查询优惠券信息
    @exception_decorator
    def query_sale_message(self):
        """查询优惠卷信息"""
        svc = DatabaseManager('saleMes')  # 优惠券数据库
        msgs = svc.query(['mes', 'code', 'time', 'image_url', 'id'],
                         {"keyword": re.compile(f'%{self.param[0]}%')})  # 查询有该关键字的优惠卷信息

        for msg in msgs:
            text = f"关键字:{self.param[0]}\n信息:{msg['mes']}\n时间:{msg['time']}\n代码:{msg['code']}\nID:{msg['id']}"
            mes_chain = Message.get_mes_chain(text, msg['image_url'])  # 信息链
            # 发送信息
            Message(self.cfg).send_message([self.qq], [self.launcher_type], mes_chain)

        self.ret_msg = '' if len(msgs) else f'没有找到对应{self.param[0]}的优惠券,请确保关键字已添加,或过一段时间再来!'

    # 查询含有关键字的所有信息
    @exception_decorator
    def query_all_message(self):
        """在全部信息中查询含有关键字的信息"""

        def main():
            svc = DatabaseManager('allMes')  # 全部信息数据库
            all_mes = svc.query(['mes', 'time', 'image_url', 'id'])  # 获得全部信息

            have_filter_mes = False
            send_mes = ['']
            send_mes_emd = [HandleMessage.get_msg_encode('')]  # 默认一条空信息
            send_id = []  # 已经发送了的id，尝试解决稀奇古怪的bug
            src_process_message_timeout = HostConfig.get('process_message_timeout')
            # HostConfig.put('process_message_timeout', f'{60 * 60}')  # 更改超时时间
            for i in all_mes:
                _, keyword, _ = self.get_keyword_re(self.param, '')
                if re.search(keyword, i['mes'], re.IGNORECASE | re.S):  # 符合正则
                    introduce, _ = HandleMessage.get_mes_info(i['mes'], self.cfg.suspicious_mes)
                    introduce_emd = HandleMessage.get_msg_encode(introduce)
                    is_repeat_mes, _, _ = HandleMessage.is_repeat_text(send_mes_emd, introduce_emd, send_mes, introduce,
                                                                       self.cfg.similarity)
                    if not is_repeat_mes and i['id'] not in send_id:  # 不是重复信息
                        # 发送信息
                        mes = f"信息:{i['mes']}\n时间:{i['time']}\nID:{i['id']}"
                        image_url = i['image_url'] or ''
                        mes_chain = Message(self.cfg).get_mes_chain(mes, image_url)  # 信息链
                        Message(self.cfg).send_message([self.qq], [self.launcher_type], mes_chain)  # 发送信息
                        # 更改已发送信息列表
                        send_mes.append(introduce)
                        send_mes_emd.append(introduce_emd)
                        have_filter_mes = True
                        send_id.append(i['id'])

            # HostConfig.put('process_message_timeout', f'{src_process_message_timeout}')  # 复原设置

            # 发送信息
            if have_filter_mes:
                Message(self.cfg).send_message(self.qq, [self.launcher_type], [Plain(f'筛选结束')])
            else:
                Message(self.cfg).send_message(self.qq, [self.launcher_type],
                                               [Plain(f'没有找到对应{self.param[0]}的信息')])

        thread = Thread(target=main)
        thread.start()

    # 查询关键字
    @exception_decorator
    def query_keywords(self):
        """查询关键字"""
        svc = DatabaseManager('keyword')  # 关键字数据库

        keywords = svc.query(['keywords'], {'qq': self.qq})[0].split()  # 关键字
        ret_mess = ''  # 回复信息
        cnt = 1  # 序号
        # 构建回复信息
        for keyword in keywords:
            ret_mess += f'{cnt}.{keyword}\n'
            cnt += 1

        self.ret_msg = ret_mess

    # 打开实时发送
    @exception_decorator
    def open_message(self):
        """打开实时发送"""
        svc = DatabaseManager('keyword')
        svc.update({'send_mes': 1}, {'qq': self.qq})
        self.ret_msg = '成功,后续消息将实时发送'

    # 关闭实时发送
    @exception_decorator
    def close_message(self):
        """关闭实时发送"""
        svc = DatabaseManager('keyword')
        svc.update({'send_mes': 0}, {'qq': self.qq})
        self.ret_msg = '成功,后续消息将不会实时发送。\n可以通过“查询优惠券 关键字”指令查询相关优惠券'

    # 删除监听群
    @exception_decorator
    def delete_group(self):
        """删除监听群"""
        svc_listen_qq = DatabaseManager('listenQQ')  # 监听群数据库
        key_qq = svc_listen_qq.query(['listen_qq'])  # 监听群qq列表

        if int(self.param[0]) in key_qq:  # 在监听列表
            svc_listen_qq.delete({'listen_qq': int(self.param[0])})  # 删除监听qq
            svc_group_control = DatabaseManager('groupMesControl')  # 群控制数据库
            svc_group_control.delete({'qq': int(self.param[0])})  # 删除控制qq
            self.ret_msg = '成功'
        else:
            self.ret_msg = '我本来就没有检测这个群'

    # 删除关键字
    @exception_decorator
    def delete_keyword(self):
        """删除关键字"""
        svc = DatabaseManager('keyword')  # 关键字数据库
        keywords = svc.query(['keywords'], {'qq': self.qq})[0].split()  # 已经检测的关键字

        if self.param[0] in keywords:  # 有这个关键字
            keywords.remove(self.param[0])
            svc.update({'keywords': ' '.join(keywords)}, {'qq': self.qq})  # 更新数据库
            self.ret_msg = '成功'
        else:
            self.ret_msg = '我本来就没有检测这个关键字'

    # 通过关键字删除序号
    @exception_decorator
    def delete_keyword_by_no(self):
        """通过关键字删除序号"""
        svc = DatabaseManager('keyword')  # 关键字数据库
        keywords = svc.query(['keywords'], {'qq': self.qq})[0].split()  # 已经检测的关键字
        delete_no = int(self.param[0])  # 删除序号
        if 0 < delete_no <= len(keywords):  # 在范围内
            del keywords[delete_no - 1]  # 删除序号
            svc.update({'keywords': ' '.join(keywords)}, {'QQ': self.qq})  # 更新数据库
            self.ret_msg = '成功'
        else:
            self.ret_msg = '序号错误'

    # 查询原信息
    @exception_decorator
    def query_src_mes(self):
        """查询原信息"""
        svc = DatabaseManager('saleMes')  # 优惠券数据库
        mes = svc.query(['src_mes', 'image_url'], {'id': int(self.param[0])})  # 查询原信息
        find_src_mes = False
        for i in mes:  # 实际上最多执行一次
            text = f'{i["src_mes"]}'
            mes_chain = Message.get_mes_chain(text, i['image_url'])  # 信息链
            find_src_mes = True  # 找到了原信息
            # 发送信息
            Message(self.cfg).send_message([self.qq], [self.launcher_type], mes_chain)

        if not find_src_mes:
            self.ret_msg = f'没有找到对应{self.param[0]}的优惠券,请确保ID输入正确!'

    # 查询可疑信息相关信息信息
    @exception_decorator
    def query_context_mes(self):
        """查询可疑信息相关信息"""
        svc = DatabaseManager('saleMes')  # 优惠卷数据库
        qq = svc.query(['receive_qq'], {'id': self.param[0]})[0].split()[0]  # 只查询第一个qq
        src_mes = svc.query(['src_mes'], {'id': self.param[0]})[0]  # 原信息
        image_url = svc.query(['image_url'], {'id': self.param[0]})[0]

        # 获得上下文信息
        forward, later = Message.get_context_message(qq, src_mes, int(self.param[1]))
        later[0].reverse()
        later[1].reverse()
        # 发送原信息
        mes_chain = Message.get_mes_chain(src_mes, image_url)
        # 发送可疑信息相关信息
        Message(self.cfg).send_context_message(forward[0], [self.qq], [self.launcher_type], self.param[0], forward[1],
                                               reverse=True)
        time.sleep(1.5)  # 保证顺序
        Message(self.cfg).send_message([self.qq], [self.launcher_type], mes_chain)  # 发送原信息
        # 发送可疑信息相关信息信息
        time.sleep(1.5)  # 保证顺序
        Message(self.cfg).send_context_message(later[0], [self.qq], [self.launcher_type], self.param[0], later[1])

    # 清理数据库
    @exception_decorator
    def clear_database(self):
        """清理数据库"""
        admin_qq = HostConfig.get('admin_qq')  # 管理员QQ

        if not isinstance(admin_qq, list):
            admin_qq = [admin_qq]

        if self.qq not in admin_qq:  # 判断是不是管理员
            self.ret_msg = '该指令仅管理员可用'
            return

        if len(self.param):  # 自定义时间范围
            clear_task(int(self.param[0]), int(self.param[1]), self.cfg.clear_time, True, self.qq, False)
        else:  # 使用默认时间范围
            clear_task(self.cfg.discount_message_save_day, self.cfg.all_message_save_day, self.cfg.clear_time,
                       True, self.qq, False)
