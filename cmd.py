"""处理用户指令。实现用户与系统交互逻辑"""
from pkg.plugin.host import PluginHost


class HandleCmd:
    def __init__(self, host: PluginHost, cmd: str, param: list, **kwargs):
        self.host = host

        self.mes_chain = kwargs.get('message_chain')  # 消息链
        self.qq = kwargs.get('launcher_id')  # 发起者id,用户qq号或群qq号
        self.sender_id = kwargs.get('sender_id')  # 发送者id
        self.launcher_type = kwargs.get('launcher_type')  # 消息类型

        self.cmd = cmd  # 用户命令
        self.param = param  # 命令参数

        self.had_handle_cmd = self.handle()  # 处理流程

    def handle(self) -> bool:
        return True
