"""
处理优惠券信息的流程代码。实现筛选优惠券逻辑
"""
import json
import logging
import re
import threading
import time
from datetime import datetime
from typing import List, Tuple

import numpy as np
import torch
from mirai import Plain, Image
from plugins.discountAssistant.utils.database import DatabaseManager
from text2vec import SentenceModel, cos_sim

from pkg.plugin.host import PluginHost

sale_mes_lock = threading.Lock()  # 消息锁


class HandleMessage:
    def __init__(self, config, **kwargs):
        self.host = PluginHost()
        self.cfg = config

        self.mes_chain = kwargs.get('message_chain', None)  # 消息链
        self.qq = kwargs.get('launcher_id', None)  # 发起者id,用户qq号或群qq号
        self.sender_id = kwargs.get('sender_id', None)  # 发送者id
        self.launcher_type = kwargs.get('launcher_type', None)  # 消息类型
        self.mes_plain = '\n'.join([i.text for i in (self.mes_chain[Plain] if self.mes_chain else [])])  # 文字信息
        self.image = '\n'.join([i.url for i in (self.mes_chain[Image] if self.mes_plain else [])])  # 图片url

        self.had_handle_msg = self.handle()  # 处理流程

    # 优惠券处理流程
    def handle(self) -> bool:
        """处理优惠券信息"""
        svc_listen_qq = DatabaseManager('listenQQ')
        listen_qq = svc_listen_qq.query(['listen_qq'])  # 监听QQ
        if self.qq not in listen_qq:  # 不在监听群返回False不做后续处理
            return False

        if not len(self.mes_chain[Plain]):  # 空信息返回不做后续处理
            return True

        Message.back_up_msg(self.mes_plain, self.image, self.qq)  # 备份信息
        # 判断是否是连续信息后续信息
        svc_group_control = DatabaseManager('groupMesControl')
        is_continuous_mes = svc_group_control.query(['is_continuous_mes'], {'QQ': self.qq})[0]  # 是否是连续信息的后续信息
        # 优惠券相关信息
        introduce, code = self.get_mes_info(self.mes_plain, self.cfg.suspicious_mes)  # 优惠券介绍,代码

        # 当是非连续消息并且是连续消息的非后续消息时进入
        if not (is_continuous_mes and self.handle_continuous_late_message(self.mes_plain, svc_group_control, introduce,
                                                                          code)):
            has_keyword, keywords, send_qq, qq_type = self.get_keyword_qq(self.mes_plain)  # 需要发送优惠券的qq相关信息
            last_mes_no = svc_group_control.query(['context_num'], {'qq': self.qq})[0]  # 判断是否是可疑信息后续
            if has_keyword:  # 信息含有有关键字
                with sale_mes_lock:  # 加锁
                    logging.info(f'开始处理{self.qq}优惠信息')

                    need_get_more_message = False  # 是否需要触发可疑信息机制
                    svc_message = DatabaseManager('saleMes')  # 优惠券数据库
                    is_effect_info_last_info = self.is_effect_info_last_info(keywords, svc_message)  # 是否是有效信息的后续信息
                    if not code:  # 当没有检测到代码时则触发可疑信息机制
                        if is_effect_info_last_info:  # 当是有效信息的后续有效信息时直接返回
                            return True
                        # 获得介绍
                        need_get_more_message = True
                        introduce = self.mes_plain

                    today_all_mes = DatabaseManager('saleMes').get_today_all_message() or [
                        {'mes': '', 'encode': None}]  # 当天的全部筛选到的优惠卷消息
                    # 判断是否是重复消息、多步骤消息的重复消息
                    is_repeat, mes_emd = self.is_repeat_message(today_all_mes, introduce, svc_message, code)
                    is_contain = self.is_contain_message(today_all_mes, introduce, svc_message, code)

                    if not is_repeat and not is_contain:  # 不是重复信息
                        # 是否是多步骤消息第一步消息
                        if re.match(r'^\d[.、]', introduce):
                            last_no = svc_group_control.query(['last_no'], {'qq': self.qq})[0]
                            if int(re.match(r'^(\d)[.、]', introduce).group(1)) == last_no + 1:  # 满足序号递增条件
                                # 更新多步骤数据库
                                svc_group_control.update(
                                    {'is_continuous_mes': 1, 'send_qq': ' '.join([str(i) for i in send_qq]),
                                     'last_no': last_no + 1}, {'qq': self.qq})
                        # 普通消息处理流程
                        self.handle_normal_message(code, keywords, introduce, self.mes_plain, send_qq, svc_message,
                                                   qq_type, need_get_more_message, svc_group_control, mes_emd)
            elif last_mes_no:  # 是可疑信息后续信息
                mes_time = svc_group_control.query(['last_time'], {'qq': self.qq})[0]
                # 获得原数据
                src_mes = svc_group_control.query(['last_mes'], {'qq': self.qq})[0] or ''
                src_url = svc_group_control.query(['mes_image_url'], {'qq': self.qq})[0] or ''
                # 在时间内则更新
                if self.is_time_limit_exceeded(self.cfg.max_relate_message_time,
                                               mes_time) or last_mes_no == 1:  # 最后一条消息或已超时
                    all_mes = src_mes.split('$')  # 获得可疑消息相关信息文本
                    all_mes.append(self.mes_plain)  # 可疑信息相关信息文本

                    all_url = src_url.split('$')
                    all_url.append(self.image)  # 可疑信息图片

                    # qq号及类型
                    send_qq = [int(i) for i in svc_group_control.query(['context_qq'], {'qq': self.qq})[0].split()]
                    qq_type = [int(i) for i in svc_group_control.query(['qq_type'], {'qq': self.qq})[0].split()]
                    # 可疑信息id
                    mes_id = svc_group_control.query(['mes_id'], {'qq': self.qq})[0]
                    # 发送信息
                    Message(self.cfg).send_context_message(all_mes[1:], send_qq, qq_type, mes_id, all_url[1:])
                    # 恢复数据库
                    svc_group_control.update({'last_mes': '', 'context_num': 0, 'last_time': '',
                                              'mes_image_url': '', 'context_qq': '', 'qq_type': '', 'mes_id': ''},
                                             {'qq': self.qq})
                else:  # 处理可疑信息相关信息
                    new_line = '$'  # 拼接分隔符
                    svc_group_control.update(
                        {'last_mes': f"{src_mes or ''}{new_line}{self.mes_plain}",
                         'mes_image_url': f"{src_url or ''}{new_line}{self.image}",
                         'context_num': last_mes_no - 1}, {'qq': self.qq})
        return True

    # 获得优惠券的介绍和代码
    @classmethod
    def get_mes_info(cls, mes, suspicious_mes):
        """获得优惠券的介绍和代码"""
        introduce = ''  # 简化后的优惠卷信息
        code = ''  # 优惠券代码
        if '.jd.' in mes:  # 京东卷
            introduce = [i.strip() for i in re.split(r'https://u.jd.c.+', mes)]
            if '查券' in introduce[-1]:  # 去掉无用信息——部分qq群特殊对待
                introduce[-1] = re.search(r'(.*)-----------\n----------.+', introduce[-1], re.S).group(1).strip()
            introduce = '\n'.join([i for i in introduce if i]).strip()
            code = '\n'.join(re.findall(r'https://u.jd.c.+', mes, re.MULTILINE))
        else:  # 淘宝卷
            mes_lines = mes.split('\n')
            temp_code = []  # 临时代码
            for i in mes_lines:
                if cls.get_char_num_cnt(i) >= suspicious_mes or 'http' in i:  # 符合有效信息标准或有链接则为优惠券代码
                    temp_code.append(i)

            if len(temp_code) != 0:
                introduce = '\n'.join(mes_lines[:mes_lines.index(temp_code[0])])
                code = '\n'.join(temp_code)

        return introduce, code

    # 处理多步骤信息
    def handle_continuous_late_message(self, mes, svc_continuous, introduce, code):
        """处理多步骤消息后续消息"""
        if re.match(r'^\d[.、]', mes):  # 以数字序号开头
            last_no = svc_continuous.query(['last_no'], {'qq': self.qq})[0]  # 上条信息序号
            if int(re.match(r'^(\d)[.、]', mes).group(1)) == last_no + 1:  # 序号递增则为连续信息后续信息
                svc_continuous.update({'last_no': last_no + 1}, {'qq': self.qq})  # 更新序号
                svc_message = DatabaseManager('saleMes')  # 优惠券数据库
                table = svc_message.query(['*'])
                for row in table:
                    if f'{self.qq}' in row['receive_qq']:
                        # 数据库中追加多步骤消息
                        src_introduce = row['mes']  # 更新前信息
                        src_code = row['code']  # 更新前优惠码
                        src_src = row['src_mes']  # 更新前原信息

                        update_data = {'code': src_code + '\n' + code,
                                       'src_mes': src_src + '\n' + mes,
                                       'mes': src_introduce + '\n' + introduce}  # 更新内容
                        image_url = row['image_url'] + '\n' + self.image
                        update_data.update({'image_url': image_url})
                        svc_message.update(update_data, {'id': row['id']})  # 更新优惠卷数据库

                        # 发送QQ消息
                        send_qq = list(svc_continuous.query(['send_qq'], {'qq': self.qq})[0].split())
                        qq_type = []
                        svc_keyword = DatabaseManager('keyword')
                        # 获得qq类型
                        for qq in send_qq:
                            temp_type = svc_keyword.query(['qq_type'], {'qq': int(qq)})[0]
                            qq_type.append(temp_type)

                        text = f"""信息:{introduce}\n代码:{code}"""

                        mes_chain = Message.get_mes_chain(text, self.image)  # 信息链
                        Message(self.cfg).send_message(send_qq, qq_type, mes_chain)  # 发送信息

                        return True  # 是多步骤信息后续信息
            else:
                svc_continuous.update({'is_continuous_mes': 0, 'send_qq': '', 'last_no': 0}, {'qq': self.qq})  # 复原数据库
                return False
        else:  # 取消多步骤消息
            svc_continuous.update({'is_continuous_mes': 0, 'send_qq': '', 'last_no': 0}, {'qq': self.qq})  # 复原数据库
            return False

    # 获得优惠券关键字等信息
    @staticmethod
    def get_keyword_qq(mes):
        # 获得优惠券相关信息
        svc_keywords = DatabaseManager('keyword')
        key_words_all = svc_keywords.query(['*'])
        send_qq = []  # 发送qq
        find_keyword = []  # 关键字
        qq_type = []  # qq类型
        has_keyword = False  # 是否有关键字
        for key_words in key_words_all:  # 判断是否有关键字
            for key_word in list(key_words['keywords'].split()):
                if re.search(key_word, mes, re.IGNORECASE | re.S):  # 忽略大小写、多行匹配
                    # 添加推送QQ
                    if key_words['send_mes']:  # 需要信息通知时才通知
                        send_qq.append((key_words['qq']))
                        qq_type.append(key_words['qq_type'])
                        find_keyword.append(key_word)

                    has_keyword = True  # 有关键字
                    break

        return has_keyword, find_keyword, send_qq, qq_type

    # 是否是有效信息后续信息
    def is_effect_info_last_info(self, keywords, svc) -> bool:
        """是否是有效信息的后续信息"""
        table = svc.query(['*'])  # 优惠卷数据库
        last_time = None
        for raw in table:
            if f'{self.qq}' in raw['receive_qq']:
                find_keyword = False  # 标记是否找到对应可疑信息关键字的有效信息
                for keyword in keywords:
                    if keyword in raw['keyword'].split():  # 找到了
                        find_keyword = True
                        break
                if find_keyword:
                    last_time = raw['time']
                    break

        if last_time:  # 有有效信息
            return not self.is_time_limit_exceeded(self.cfg.effect_message_time, last_time)  # 判断是否超时
        else:
            return False  # 不是有效信息后续信息

    # 是否超时间限制
    @staticmethod
    def is_time_limit_exceeded(timeout: int, time_first: str, time_second=''):
        """是否超过时间"""
        time_first = datetime.strptime(time_first, "%m-%d %H:%M")
        time_first = time_first.replace(year=datetime.now().year)

        if not time_second:  # 若第二个参数为空
            time_second = datetime.now()  # 当前时间
        else:
            time_second = datetime.strptime(time_second, "%m-%d %H:%M")
            time_second = time_second.replace(year=datetime.now().year)

        time_diff = abs(time_second - time_first)
        minutes_diff = time_diff.total_seconds() / 60

        # 在时间内则更新
        if minutes_diff > timeout:  # 最后一条消息或已超时
            return True
        else:
            return False

    # 得到文字向量化结果
    @staticmethod
    def get_msg_encode(msg):
        """得到文字向量化结果"""
        model = SentenceModel(r"plugins/discountAssistant/model")  # 模型
        return model.encode(msg)

    # 比较相似度
    @staticmethod
    def is_repeat_text(all_mes_embeddings, mes_embeddings, all_mes, mes, similarity):
        """比较相似度"""
        # 信息相似度
        cosine_scores = cos_sim(all_mes_embeddings, mes_embeddings)
        # 比较相似度
        for i in range(len(cosine_scores)):
            # 高于设定值判定为重复文本
            if float(re.search(r'tensor\(\[(.*)]\)', str(cosine_scores[i])).group(1)) > similarity:
                return True, all_mes[i], cosine_scores[i]
        else:
            return False, mes, 0

    # 是否是重复信息
    def is_repeat_message(self, today_all_mes: List[dict], mes: str, svc_message, code) -> tuple:
        """判断是否是重复优惠券"""
        # 向量化
        embeddings1 = []
        embeddings2 = self.get_msg_encode(mes)

        for i in today_all_mes:
            if i['encode']:
                embeddings1.append(np.array(json.loads(i['encode'])))
            else:  # 兼容旧版本
                embeddings1.append(self.get_msg_encode(i['mes']))
        embeddings1 = torch.Tensor(np.array(embeddings1)).to(torch.float32)

        # 是否是重复文本
        is_repeat_mes, mes, similarity = self.is_repeat_text(np.array(embeddings1), embeddings2, today_all_mes, mes,
                                                             self.cfg.similarity)

        if is_repeat_mes:
            logging.info(f'文本相似度审查未通过,重复文本: {mes},相似度:{similarity}')
            self.handle_repeat_message(svc_message, mes, code)  # 处理重复信息流程
        else:
            logging.debug(f'文本相似度审查通过,文本: {mes}')

        return is_repeat_mes, embeddings2

    # 是否是多步骤信息的重复信息
    def is_contain_message(self, today_all_mes, introduce, svc_message, code) -> bool:
        """判断是否是重复的多步骤优惠卷"""
        for i in today_all_mes:  # 判断是否是重复信息
            if introduce in i:  # 重复
                self.handle_repeat_message(svc_message, i, code)
                return True
        else:
            return False

    # 处理重复信息
    def handle_repeat_message(self, svc_message, src_mes, code):
        """处理重复优惠券"""
        # 更新代码
        src_code = svc_message.query(['code'], {'mes': src_mes})
        src_code = src_code[0] if len(src_code) else ''
        svc_message.update({'code': src_code + '\n' + '新:' + code + '\n'}, {'mes': src_mes})
        # 更新QQ
        src_qq = svc_message.query(['receive_qq'], {'mes': src_mes})[0]
        svc_message.update({'receive_qq': f'{src_qq} {self.qq}'}, {'mes': src_mes})
        # 更新时间
        local_time = time.localtime(time.time())
        mes_time = time.strftime("%m-%d %H:%M", local_time)
        svc_message.update({'time': mes_time}, {'mes': src_mes})

    # 处理普通信息
    def handle_normal_message(self, code, keywords, introduce, mes, send_qq, svc_message, qq_type,
                              need_get_more_message: bool, svc_context, mes_emd):
        """处理普通信息"""
        local_time = time.localtime(time.time())
        mes_time = time.strftime("%m-%d %H:%M", local_time)
        # 优惠券数据
        insert_data = {'receive_qq': self.qq, 'mes': introduce, 'keyword': ' '.join(keywords),
                       'time': mes_time, 'code': code, 'src_mes': mes, 'send_qq': ' '.join([str(i) for i in send_qq]),
                       'image_url': self.image, 'encode': json.dumps(mes_emd.tolist())}
        svc_message.insert(insert_data)  # 更新数据库
        mes_id = svc_message.query(['id'], {'src_mes': mes})[0]  # 优惠券id

        # 判断是否是可疑信息
        more_mes = []  # 可疑信息相关信息
        image_url = []
        if need_get_more_message:
            more_mes, image_url = self.get_more_message(mes, svc_context)

        # 构建信息链
        for i in range(len(send_qq)):
            # 发送可疑信息附近信息
            if need_get_more_message:
                Message(self.cfg).send_context_message(more_mes, [send_qq[i]], [qq_type[i]], mes_id, image_url,
                                                       reverse=True)
                # 同步上下文数据库
                svc_context.update(
                    {'context_qq': ' '.join([str(i) for i in send_qq]), 'qq_type': ' '.join([str(i) for i in qq_type]),
                     'mes_id': mes_id}, {'qq': self.qq})

                time.sleep(1.5)  # 保证顺序
            # 发送普通QQ消息
            text = f"""关键字:{keywords[i]}\n消息:{introduce}\n代码:{code}\nID:{mes_id}"""

            mes_chain = Message.get_mes_chain(text, self.image)  # 得到信息链
            Message(self.cfg).send_message(send_qq[i], qq_type[i], mes_chain)  # 发送信息

    # 判断是否是可疑信息
    def get_more_message(self, mes: str, svc_context) -> Tuple[List, List[str]]:
        """判断是否是可疑信息"""
        cnt = self.get_char_num_cnt(mes)
        if cnt < self.cfg.suspicious_mes and 'http' not in mes:  # 是可疑信息
            logging.info(f'{self.qq}的{mes}被判定为可疑信息')
            svc_all_message = DatabaseManager('allMes')
            all_message = svc_all_message.query(['mes', 'time', 'image_url'], {'receive_qq': self.qq})  # 备份信息
            context_num = self.cfg.relate_message_num  # 相关信息数量限制
            max_context_time = self.cfg.max_relate_message_time  # 相关信息时间限制
            local_time = time.localtime(time.time())
            mes_time = time.strftime("%m-%d %H:%M", local_time)  # 当前时间
            svc_context.update({'context_num': context_num, 'last_time': mes_time}, {'qq': self.qq})  # 更新数据库
            # 获取当前时间
            more_mes = []
            url = []
            for i in all_message[1:1 + context_num]:
                # 计算分钟差
                relate_mes_time = i['time']
                # 是否超出时间限制
                if self.is_time_limit_exceeded(max_context_time, relate_mes_time, mes_time):  # 已超时
                    break
                more_mes.append(i['mes'])
                url.append(i['image_url'])
            return more_mes, url
        else:
            return [], []

    # 获得英文字符数量
    @staticmethod
    def get_char_num_cnt(mes):
        uppercase_count = sum(1 for char in mes if char.isupper())  # 大写
        lowercase_count = sum(1 for char in mes if char.islower())  # 小写
        num_count = sum(1 for char in mes if char.isdigit())  # 数字
        cnt = uppercase_count + lowercase_count + num_count  # 英文字符+数字数量
        return cnt


class Message:
    """处理信息链"""

    def __init__(self, config):
        self.host = PluginHost()
        self.cfg = config

    # 备份信息
    @staticmethod
    def back_up_msg(mes_plain, image, qq):
        """
        备份当前信息
        :return:
        """
        local_time = time.localtime(time.time())
        mes_time = time.strftime("%m-%d %H:%M", local_time)  # 时间
        # 备份
        svc_all_msg = DatabaseManager('allMes')
        svc_all_msg.insert({'mes': mes_plain, 'time': mes_time, 'image_url': image, 'receive_qq': qq})

    # 发送可疑信息相关信息
    def send_context_message(self, mes: List[str], qq: list, qq_type: list, mes_id: str,
                             image_url: List[str],
                             reverse=False) -> bool:
        """发送可疑信息相关信息"""
        direction = '下' if not reverse else '上'
        if reverse:
            mes.reverse()
            image_url.reverse()

        mes_chain = []
        # 构建信息链
        for i in range(len(mes)):
            mes_chain.extend(Message.get_mes_chain(mes[i], image_url[i],
                                                   divide='\n------------------------------------------------------------------\n'))  # 构建信息链
        if len(mes_chain):
            mes_chain.pop()  # 去掉多余的分隔
        # 发送信息
        self.send_message(qq, qq_type, mes_chain)

        return True

    # 得到可疑信息相关信息
    @staticmethod
    def get_context_message(qq: str, src_mes: str, message_cnt: int) -> Tuple[List, List]:
        """得到可疑信息相关信息"""
        svc = DatabaseManager('allMes')
        mes = svc.query(['mes', 'image_url'], {'receive_qq': qq})
        forward = [[], []]
        later = [[], []]
        for i in mes:
            if i['mes'] == src_mes:
                index = mes.index(i)
                # 构建前后信息链
                for j in range(max(0, index - message_cnt), index):
                    later[0].append(mes[j]['mes'])
                    later[1].append(mes[j]['image_url'])
                for j in range(index + 1, min(len(mes), index + message_cnt + 1)):
                    forward[0].append(mes[j]['mes'])
                    forward[1].append(mes[j]['image_url'])
                break

        return forward, later

    # 得到信息链
    @staticmethod
    def get_mes_chain(plain_text: str, image_url: str, divide: str = '') -> List:
        """得到一条信息的的信息链"""
        # 分隔图片url
        image_url = image_url or ''
        image_url = image_url.split()
        # 构建信息链
        ret = [Plain(plain_text or '')]
        for i in image_url:  # 图片
            if isinstance(i, str) and 'http' in i:  # 是有效url
                ret.append(Image(url=i))

        ret.append(Plain(divide))
        return ret

    # 根据QQ类型发送信息
    def send_message(self, qq: List[int], qq_type: List[int], mes_chain):
        """根据QQ类型发送信息"""
        # 避免误传
        if not isinstance(qq, list):
            qq = [qq]
        if not isinstance(qq_type, list):
            qq_type = [qq_type]

        for i in range(len(qq)):  # 遍历qq号
            if qq_type[i] == 0 or qq_type[i] == '0':  # 个人信息
                self.host.send_person_message(qq[i], mes_chain)
            elif qq_type[i] == 1 or qq_type[i] == '1':  # 群信息
                self.host.send_group_message(qq[i], mes_chain)
            else:  # 报错
                logging.warning(f'无法识别的qq类型:{qq_type[i]}:{qq[i]}')
