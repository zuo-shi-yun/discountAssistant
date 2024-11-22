import datetime

from .. import aamgr


@aamgr.AbstractCommandNode.register(
    parent=None,
    name="last",
    description="切换前一次对话",
    usage="!last",
    aliases=[],
    privilege=1
)
class LastCommand(aamgr.AbstractCommandNode):
    @classmethod
    def process(cls, ctx: aamgr.Context) -> tuple[bool, list]:
        import pkg.openai.session
        session_name = ctx.session_name

        reply = []
        result = pkg.openai.session.get_session(session_name).last_session()
        if result is None:
            reply = ["[bot]没有前一次的对话"]
        else:
            datetime_str = datetime.datetime.fromtimestamp(result.create_timestamp).strftime(
                '%Y-%m-%d %H:%M:%S')
            reply = ["[bot]已切换到前一次的对话：\n创建时间:{}\n".format(datetime_str)]

        return True, reply
