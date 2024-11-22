# 定义不同接口请求的模型
import logging

import openai

from ...utils import context


class RequestBase:

    client: openai.Client

    req_func: callable

    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def _next_key(self):
        switched, name = context.get_openai_manager().key_mgr.auto_switch()
        logging.debug("切换api-key: switched={}, name={}".format(switched, name))
        self.client.api_key = context.get_openai_manager().key_mgr.get_using_key()

    def _req(self, **kwargs):
        """处理代理问题"""
        logging.debug("请求接口参数: %s", str(kwargs))
        config = context.get_config_manager().data

        ret = self.req_func(**kwargs)
        logging.debug("接口请求返回：%s", str(ret))

        if config['switch_strategy'] == 'active':
            self._next_key()

        return ret

    def __iter__(self):
        raise self

    def __next__(self):
        raise NotImplementedError
