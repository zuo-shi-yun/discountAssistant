from pkg.plugin.models import require_ver
from pkg.qqbot.cmds.system.cconfig import config_operation
from pkg.utils.context import context


# 判断是否是旧版本
def is_old_version():
    try:
        require_ver("v2.5.1", "v2.6.6")  # 不超过2.6.6使用老方法获得admin_qq
        return True
    except:  # 高于该版本使用新方法
        return False


class HostConfig:
    """处理系统配置"""
    is_old_version = is_old_version()

    @classmethod
    def get(cls, key: str):
        if cls.is_old_version:
            return getattr(context.get_config(), key)
        else:
            return context.get_config_manager().data[key]

    @classmethod
    def put(cls, key: str, value):
        config_operation('', [key, value])
