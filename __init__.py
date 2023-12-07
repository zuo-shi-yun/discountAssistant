import logging
import os

import requests

from . import config


# 检查文本向量化模型是否存在
def check_model() -> bool:
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
    r = requests.get(url, stream=True)
    with open('plugins/discountAssistant/model/pytorch_model.bin', 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


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


def main():
    if not check_model():
        try:
            logging.critical('模型下载中...该过程约1分钟,请耐心等待')
            download_model()
            logging.critical('模型下载成功')
        except Exception as e:
            logging.error(
                '模型下载失败!请尝试重新下载或从readme文件中的下载链接手动下载pytorch_model.bin文件并放入plugins/discountAssistant/model目录下')
            raise e
    else:
        logging.info('文本相似度模型已存在')

    cfg = check_config()  # 检查配置项
    # 检查数据库
    from plugins.discountAssistant.utils.database import DatabaseManager
    DatabaseManager().init_database()  # 初始化数据库

    # 执行数据库维护工作
    from plugins.discountAssistant.utils.clear import Clear
    Clear(cfg.discount_message_save_day, cfg.all_message_save_day, cfg.clear_time, cfg.clear_report)


main()

if __name__ == '__main__':
    main()
