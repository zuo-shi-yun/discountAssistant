import hashlib
import os

import requests
from plugins.discountAssistant import config
from plugins.discountAssistant.utils.cmd import HandleCmd
from plugins.discountAssistant.utils.message import HandleMessage
from requests.adapters import HTTPAdapter
from tqdm import tqdm

from pkg.plugin.host import EventContext, PluginHost
from pkg.plugin.models import *

"""
自动筛选、发送淘宝、京东优惠券
"""


# 注册插件
@register(name="discountAssistant", description="自动筛选、发送淘宝、京东优惠券", version="1.2", author="zuoShiYun")
class DiscountAssistant(Plugin):
    def __init__(self, plugin_host: PluginHost):
        self.host = plugin_host
        self.cfg = config.Config()
        check_plugin()  # 检查插件完整性

    # 处理群、个人指令-!cmd形式
    @on(PersonCommandSent)
    @on(GroupCommandSent)
    def handle_cmd(self, event: EventContext, **kwargs):
        handle = HandleCmd(self.cfg, kwargs['command'], kwargs['params'], **kwargs)

        # 判断是否是本插件处理指令
        if handle.had_handle_cmd:
            event.prevent_default()
            event.prevent_postorder()

            if handle.ret_msg:  # 发送回复信息
                event.add_return("reply", [handle.ret_msg])

            if handle.e:  # 显式报错
                raise handle.e

    # 处理群、个人指令-非!cmd形式
    @on(PersonNormalMessageReceived)
    @on(GroupNormalMessageReceived)
    def handle_normal_cmd(self, event: EventContext, **kwargs):
        if self.cfg.normal_cmd:  # 已开启非!cmd形式的命令
            text = kwargs['text_message'].split()  # 信息文本
            handle = HandleCmd(self.cfg, text[0], text[1::], **kwargs)

            # 判断是否是本插件处理指令
            if handle.had_handle_cmd:
                event.prevent_default()
                event.prevent_postorder()

                if handle.ret_msg:  # 发送回复信息
                    event.add_return("reply", [handle.ret_msg])

                if handle.e:  # 显式报错
                    raise handle.e

    # 筛选优惠券
    @on(GroupMessageReceived)
    @on(PersonMessageReceived)
    def group_normal_message_received(self, event: EventContext, **kwargs):
        handle = HandleMessage(self.cfg, **kwargs)  # 处理监听群信息

        # 判断是否需要阻止默认事件、是否为监听群
        if self.cfg.prevent_listen_qq_msg and handle.had_handle_msg:
            event.prevent_default()  # 屏蔽默认事件

    # 插件卸载时触发
    def __del__(self):
        pass


# 检查文本向量化模型是否存在
def check_model_exit() -> bool:
    """
    检测模型是否完整
    :return: 完整返回True
    """
    if os.path.exists('plugins/discountAssistant/model/pytorch_model.bin'):
        return True
    else:
        return False


# 下载文本向量化模型
def download_model():
    """
    下载模型
    :return:
    """

    url = 'https://huggingface.co/shibing624/text2vec-base-chinese/resolve/main/pytorch_model.bin?download=true'
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=2))  # 重试两次
    r = session.get(url, stream=True)
    mode_path = 'plugins/discountAssistant/model/pytorch_model.bin'
    total_size = int(r.headers.get('content-length'), 0)
    with open(mode_path, 'wb') as f:
        with tqdm(total=total_size, unit='B', unit_scale=True, desc='Downloading', colour='#12a10e') as pbar:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    pbar.update(len(chunk))


# 计算文件hash
def calculate_file_hash(file_path):
    # 创建一个SHA256哈希对象
    sha256_hash = hashlib.sha256()

    # 打开文件并逐块读取内容更新哈希值
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            sha256_hash.update(chunk)

    # 返回计算得到的哈希值
    return sha256_hash.hexdigest()


# 重新下载模型
def re_download_model():
    os.remove('plugins/discountAssistant/model/pytorch_model.bin')  # 删除文件
    logging.info('删除旧模型文件')
    download_model()  # 重新下载
    logging.info('开始完整性校验')
    check_model()  # 完整性校验


# 检查模型是否存在
def check_model():
    if not check_model_exit():  # 没有模型
        try:
            logging.critical('模型下载中...请耐心等待')
            download_model()
            logging.critical('模型下载成功')
        except Exception as e:
            logging.error(
                '模型下载失败!请尝试重新下载或从readme文件中的下载链接手动下载pytorch_model.bin文件并放入plugins/discountAssistant/model目录下')
            raise e

    local_mode_hash = calculate_file_hash('plugins/discountAssistant/model/pytorch_model.bin')  # 本地模型hash
    real_mode_hash = '54ff3a857e3efa0b8114eb5e7a9e7e2b6230b4ddb083254a751e44772bb99075'  # 模型hash
    if local_mode_hash == real_mode_hash:
        logging.info('文本相似度模型已存在')
    else:
        logging.critical('文本相似度模型已损坏!将重新下载模型')
        re_download_model()


# 检查配置文件
def check_config():
    """
    检查配置文件是否完整
    :return:
    """

    cfg = config.Config()

    if not hasattr(cfg, 'similarity'):
        raise ValueError('没有similarity配置项')
    elif cfg.similarity <= 0 or cfg.similarity >= 1:
        raise ValueError('similarity配置项值不正确')

    if not hasattr(cfg, 'suspicious_mes'):
        raise ValueError('没有suspicious_mes配置项')
    elif not isinstance(cfg.suspicious_mes, int):
        raise ValueError('suspicious_mes配置项值不正确')

    if not hasattr(cfg, 'relate_message_num'):
        raise ValueError('没有relate_message_num配置项')
    elif not isinstance(cfg.relate_message_num, int):
        raise ValueError('relate_message_num配置项值不正确')

    if not hasattr(cfg, 'max_relate_message_time'):
        raise ValueError('没有max_relate_message_time配置项')
    elif not isinstance(cfg.max_relate_message_time, int):
        raise ValueError('max_relate_message_time配置项值不正确')

    if not hasattr(cfg, 'effect_message_time'):
        raise ValueError('没有effect_message_time配置项')
    elif not isinstance(cfg.effect_message_time, int):
        raise ValueError('effect_message_time配置项值不正确')

    if not hasattr(cfg, 'normal_cmd'):
        raise ValueError('没有normal_cmd配置项')
    elif not isinstance(cfg.normal_cmd, bool):
        raise ValueError('normal_cmd配置项值不正确')

    if not hasattr(cfg, 'prevent_listen_qq_msg'):
        raise ValueError('prevent_listen_qq_msg')
    elif not isinstance(cfg.prevent_listen_qq_msg, bool):
        raise ValueError('prevent_listen_qq_msg配置项值不正确')

    if not hasattr(cfg, 'discount_message_save_day'):
        raise ValueError('没有discount_message_save_day配置项')
    elif not isinstance(cfg.discount_message_save_day, int):
        raise ValueError('discount_message_save_day配置项值不正确')

    if not hasattr(cfg, 'all_message_save_day'):
        raise ValueError('没有all_message_save_day配置项')
    elif not isinstance(cfg.all_message_save_day, int):
        raise ValueError('all_message_save_day配置项值不正确')

    if not hasattr(cfg, 'clear_time'):
        raise ValueError('没有clear_time配置项')
    elif not isinstance(cfg.clear_time, int) or cfg.clear_time < 0 or cfg.clear_time > 23:
        raise ValueError('effect_message_time配置项值不正确')

    if not hasattr(cfg, 'clear_report'):
        raise ValueError('clear_report')
    elif not isinstance(cfg.clear_report, bool):
        raise ValueError('clear_report配置项值不正确')

    logging.debug('配置项检测完毕')

    return cfg


def check_plugin():
    cfg = check_config()  # 检查配置项
    # 检查数据库
    from plugins.discountAssistant.utils.database import DatabaseManager
    DatabaseManager().init_database()  # 初始化数据库

    # 执行数据库维护工作
    from plugins.discountAssistant.utils.clear import Clear
    Clear(cfg.discount_message_save_day, cfg.all_message_save_day, cfg.clear_time, cfg.clear_report)

    # 检查模型
    check_model()


if __name__ == 'main':
    pass
