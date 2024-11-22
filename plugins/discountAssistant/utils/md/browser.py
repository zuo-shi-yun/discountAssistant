# 使用oliverkirk-sudo的QChatMarkdown项目
# 项目地址:https://github.com/oliverkirk-sudo/QChatMarkdown

# -*- coding: utf-8 -*-

import logging
from typing import Optional

from playwright.sync_api import Page, Error, Browser, sync_playwright
from plugins.discountAssistant.utils.md.Config import Config


class ConfigError(Exception):
    pass


config = Config()
_browser: Optional[Browser] = None
_playwright: Optional[sync_playwright] = None


def init(**kwargs) -> Browser:
    global _browser
    global _playwright
    _playwright = sync_playwright().start()
    try:
        _browser = launch_browser(**kwargs)
    except Error:
        install_browser()
        _browser = launch_browser(**kwargs)
    return _browser


def launch_browser(proxy=config.htmlrender_proxy_host, **kwargs) -> Browser:
    assert _playwright is not None, "Playwright 没有安装"
    if proxy:
        kwargs["proxy"] = proxy
    if config.htmlrender_browser == "firefox":
        logging.info("使用 firefox 启动")
        return _playwright.firefox.launch(**kwargs)
    else:
        # 默认使用 chromium
        logging.info("使用 chromium 启动")
        return _playwright.chromium.launch(**kwargs)


def get_browser(**kwargs) -> Browser:
    return init()


def get_new_page(device_scale_factor: float = 2, **kwargs) -> Page:
    browser = get_browser()
    page = browser.new_page(device_scale_factor=device_scale_factor, **kwargs)
    return page


def shutdown_browser():
    global _browser
    global _playwright
    if _browser:
        _browser.close()
        _browser = None
    if _playwright:
        _playwright.stop()  # type: ignore
        _playwright = None


def install_browser():
    import os
    import sys

    from playwright.__main__ import main

    if host := config.htmlrender_download_host:
        logging.info("使用配置源进行下载")
        os.environ["PLAYWRIGHT_DOWNLOAD_HOST"] = host
    else:
        logging.info("使用镜像源进行下载")
        os.environ[
            "PLAYWRIGHT_DOWNLOAD_HOST"
        ] = "https://npmmirror.com/mirrors/playwright/"
    success = False

    if config.htmlrender_browser == "firefox":
        logging.info("正在安装 firefox")
        sys.argv = ["", "install", "firefox"]
    else:
        # 默认使用 chromium
        logging.info("正在安装 chromium")
        sys.argv = ["", "install", "chromium"]
    try:
        logging.info("正在安装依赖")
        os.system("playwright install-deps")
        main()
    except SystemExit as e:
        if e.code == 0:
            success = True
    if not success:
        logging.error("浏览器更新失败, 请检查网络连通性")
