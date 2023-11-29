# 使用oliverkirk-sudo的QChatMarkdown项目
# 项目地址:https://github.com/oliverkirk-sudo/QChatMarkdown

from typing import Optional


class Config:
    def __init__(self):
        self.open: bool = False
        self.width: int = 500  # 图片宽度
        self.type: str = "png"  # 图片类型，["jpeg", "png"]
        self.quality: int = 100  # 图片质量 0-100 当为png时无效
        self.scale: float = 2  # 缩放比例,类型为float,值越大越清晰
        self.htmlrender_browser: Optional[str] = "chromium"
        self.htmlrender_download_host: Optional[str] = None
        self.htmlrender_proxy_host: Optional[str] = None
