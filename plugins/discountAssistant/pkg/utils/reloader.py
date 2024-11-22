import logging
import importlib
import pkgutil
import asyncio

from . import context
from ..plugin import host as plugin_host


def walk(module, prefix='', path_prefix=''):
    """遍历并重载所有模块"""
    for item in pkgutil.iter_modules(module.__path__):
        if item.ispkg:

            walk(__import__(module.__name__ + '.' + item.name, fromlist=['']), prefix + item.name + '.', path_prefix + item.name + '/')
        else:
            logging.info('reload module: {}, path: {}'.format(prefix + item.name, path_prefix + item.name + '.py'))
            plugin_host.__current_module_path__ = "plugins/" + path_prefix + item.name + '.py'
            importlib.reload(__import__(module.__name__ + '.' + item.name, fromlist=['']))


def reload_all(notify=True):
    # 解除bot的事件注册
    import pkg
    context.get_qqbot_manager().unsubscribe_all()
    # 执行关闭流程
    logging.info("执行程序关闭流程")
    import main
    main.stop()

    # 删除所有已注册的命令
    import pkg.qqbot.cmds.aamgr as cmdsmgr
    cmdsmgr.__command_list__ = {}
    cmdsmgr.__tree_index__ = {}

    # 重载所有模块
    context.context['exceeded_keys'] = context.get_openai_manager().key_mgr.exceeded
    this_context = context.context
    walk(pkg)
    importlib.reload(__import__("config-template"))
    importlib.reload(__import__('config'))
    importlib.reload(__import__('main'))
    importlib.reload(__import__('banlist'))
    importlib.reload(__import__('tips'))
    context.context = this_context

    # 重载插件
    import plugins
    walk(plugins)

    # 初始化相关文件
    main.check_file()

    # 执行启动流程
    logging.info("执行程序启动流程")

    context.get_thread_ctl().reload(
        admin_pool_num=4,
        user_pool_num=8
    )

    def run_wrapper():
        asyncio.run(main.start_process(False))

    context.get_thread_ctl().submit_sys_task(
        run_wrapper
    )

    logging.info('程序启动完成')
    if notify:
        context.get_qqbot_manager().notify_admin("重载完成")
