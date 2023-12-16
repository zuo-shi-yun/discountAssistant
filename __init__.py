import logging

from . import config


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
