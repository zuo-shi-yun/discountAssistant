from pkg.plugin.host import EventContext, PluginHost
from pkg.plugin.models import *

"""
自动筛选、发送淘宝、京东优惠券
"""


# 注册插件
@register(name="discountAssistant", description="自动筛选、发送淘宝、京东优惠券", version="1.0", author="zuoShiYun")
class DiscountAssistant(Plugin):
    def __init__(self, plugin_host: PluginHost):
        self.host = plugin_host

    # 处理群、个人指令
    @on(PersonNormalMessageReceived)
    @on(GroupNormalMessageReceived)
    def handle_normal_cmd(self, event: EventContext, **kwargs):
        pass

    # 处理群、个人指令-cmd形式
    @on(PersonCommandSent)
    @on(GroupCommandSent)
    def handle_cmd(self, event: EventContext, **kwargs):
        pass

    # 筛选优惠券
    @on(GroupMessageReceived)
    @on(PersonMessageReceived)
    def group_normal_message_received(self, **kwargs):
        pass

    # 插件卸载时触发
    def __del__(self):
        pass
