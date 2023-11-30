import logging
import os
import sys

import requests

from . import config

sys.path.append('plugins/discountAssistant')  # 添加模块搜索路径


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

    url = 'https://cdn-lfs.huggingface.co/shibing624/text2vec-base-chinese' \
          '/54ff3a857e3efa0b8114eb5e7a9e7e2b6230b4ddb083254a751e44772bb99075?response-content-disposition=attachment' \
          '%3B+filename*%3DUTF-8%27%27pytorch_model.bin%3B+filename%3D%22pytorch_model.bin%22%3B&response-content' \
          '-type=application%2Foctet-stream&Expires=1701417569&Policy' \
          '=eyJTdGF0ZW1lbnQiOlt7IkNvbmRpdGlvbiI6eyJEYXRlTGVzc1RoYW4iOnsiQVdTOkVwb2NoVGltZSI6MTcwMTQxNzU2OX19LCJSZXNvdXJjZSI6Imh0dHBzOi8vY2RuLWxmcy5odWdnaW5nZmFjZS5jby9zaGliaW5nNjI0L3RleHQydmVjLWJhc2UtY2hpbmVzZS81NGZmM2E4NTdlM2VmYTBiODExNGViNWU3YTllN2UyYjYyMzBiNGRkYjA4MzI1NGE3NTFlNDQ3NzJiYjk5MDc1P3Jlc3BvbnNlLWNvbnRlbnQtZGlzcG9zaXRpb249KiZyZXNwb25zZS1jb250ZW50LXR5cGU9KiJ9XX0_&Signature=G9i5ysy0imZJ38pCu1nLIpn87MLunRhJN%7EuUQIVhKQHd22R0f%7EnApRkXflH3mqBVn3CVtQ-YPbk3wehXFj7sU2sTocysI5dj3xjPbJ%7E93s%7EwFRDDstP6NAjqcJAmMquOgskej6hp3GnDcy2q0NmjpBLG6%7EAUyIvycV7iD-gsBbYTIlqa062izZ1nC0JkRWNv4sW7ZP5wGl%7EpIhtHOI9mR96j2y1aYnE0tlfx36uVQ%7Ez43TySdoq0kIrltvmg8Det5AwLkjV1NS55TC-up8RVPa5qv6Za1feILr8aBQDU4NSTtNBiZY3bOyvir62p%7E1qGGrlA754UI5Zqo9wqMsHkWQ__&Key-Pair-Id=KVTP0A1DKRTAX'
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
    from utils.database import DatabaseManager
    DatabaseManager().init_database()  # 初始化数据库

    # 执行数据库维护工作
    from utils.clear import Clear
    Clear(cfg.discount_message_save_day, cfg.all_message_save_day, cfg.clear_time, cfg.clear_report)


main()

if __name__ == '__main__':
    main()
