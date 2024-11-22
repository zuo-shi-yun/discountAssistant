from .. import aamgr


@aamgr.AbstractCommandNode.register(
    parent=None,
    name="cmd",
    description="显示命令列表",
    usage="!cmd\n!cmd <命令名称>",
    aliases=[],
    privilege=1
)
class CmdCommand(aamgr.AbstractCommandNode):
    @classmethod
    def process(cls, ctx: aamgr.Context) -> tuple[bool, list]:
        command_list = aamgr.__command_list__

        reply = []

        if len(ctx.params) == 0:
            reply_str = "[bot]当前所有命令:\n\n"

            # 遍历顶级命令
            for key in command_list:
                command = command_list[key]
                if command['parent'] is None:
                    reply_str += "!{} - {}\n".format(key, command['description'])

            reply_str += "\n请使用 !cmd <命令名称> 来查看命令的详细信息"

            reply = [reply_str]
        else:
            command_name = ctx.params[0]
            if command_name in command_list:
                reply = [command_list[command_name]['cls'].help()]
            else:
                reply = ["[bot]命令 {} 不存在".format(command_name)]

        return True, reply
    