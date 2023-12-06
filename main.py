from pkg.plugin.host import EventContext, PluginHost
from pkg.plugin.models import *
from plugins.discountAssistant.utils.cmd import HandleCmd
from plugins.discountAssistant.utils.message import HandleMessage

from . import config

"""
自动筛选、发送淘宝、京东优惠券
"""


# 注册插件
@register(name="discountAssistant", description="自动筛选、发送淘宝、京东优惠券", version="1.0", author="zuoShiYun")
class DiscountAssistant(Plugin):
    def __init__(self, plugin_host: PluginHost):
        self.host = plugin_host
        self.cfg = config.Config()

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


if __name__ == 'main':
    pass
