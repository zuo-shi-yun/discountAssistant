# 使用oliverkirk-sudo的QChatMarkdown项目
# 项目地址:https://github.com/oliverkirk-sudo/QChatMarkdown

from os import getcwd
from pathlib import Path
from typing import Union, Literal

import jinja2
import markdown

from utils.md.browser import get_new_page

TEMPLATES_PATH = str(Path(__file__).parent / "templates")

env = jinja2.Environment(
    extensions=["jinja2.ext.loopcontrols"],
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH),
    enable_async=True,
)


def text_to_pic(
        text: str,
        css_path: str = "",
        width: int = 500,
        type: Literal["jpeg", "png"] = "png",
        quality: Union[int, None] = None,
        device_scale_factor: float = 2,
) -> bytes:
    """多行文本转图片

    Args:
        text (str): 纯文本, 可多行
        css_path (str, optional): css文件
        width (int, optional): 图片宽度，默认为 500
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        device_scale_factor: 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)

    Returns:
        bytes: 图片, 可直接发送
    """
    template = env.get_template("text.html")

    return html_to_pic(
        template_path=f"file://{css_path if css_path else TEMPLATES_PATH}",
        html=template.render(
            text=text,
            css=read_file(css_path) if css_path else read_tpl("text.css"),
        ),
        viewport={"width": width, "height": 10},
        type=type,
        quality=quality,
        device_scale_factor=device_scale_factor,
    )


def md_to_pic(
        md: str = "",
        md_path: str = "",
        css_path: str = "",
        width: int = 500,
        type: Literal["jpeg", "png"] = "png",
        quality: Union[int, None] = None,
        device_scale_factor: float = 2,
) -> bytes:
    """markdown 转 图片

    Args:
        md (str, optional): markdown 格式文本
        md_path (str, optional): markdown 文件路径
        css_path (str,  optional): css文件路径. Defaults to None.
        width (int, optional): 图片宽度，默认为 500
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        device_scale_factor: 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)

    Returns:
        bytes: 图片, 可直接发送
    """
    template = env.get_template("markdown.html")
    if not md:
        if md_path:
            md = read_file(md_path)
        else:
            raise Exception("必须输入 md 或 md_path")
    md = markdown.markdown(
        md,
        extensions=[
            "pymdownx.tasklist",
            "tables",
            "fenced_code",
            "codehilite",
            "mdx_math",
            "pymdownx.tilde",
        ],
        extension_configs={"mdx_math": {"enable_dollar_delimiter": True}},
    )

    extra = ""
    if "math/tex" in md:
        katex_css = read_tpl("katex/katex.min.b64_fonts.css")
        katex_js = read_tpl("katex/katex.min.js")
        mathtex_js = read_tpl("katex/mathtex-script-type.min.js")
        extra = (
            f'<style type="text/css">{katex_css}</style>'
            f"<script defer>{katex_js}</script>"
            f"<script defer>{mathtex_js}</script>"
        )

    if css_path:
        css = read_file(css_path)
    else:
        css = read_tpl("github-markdown-light.css") + read_tpl(
            "pygments-default.css"
        )

    return html_to_pic(
        template_path=f"file://{css_path if css_path else TEMPLATES_PATH}",
        html=template.render(md=md, css=css, extra=extra),
        viewport={"width": width, "height": 10},
        type=type,
        quality=quality,
        device_scale_factor=device_scale_factor,
    )


# def read_md(md_path: str) -> str:
#     with aiofiles.open(str(Path(md_path).resolve()), mode="r") as f:
#         md = f.read()
#     return markdown.markdown(md)


def read_file(path: str) -> str:
    with open(path, mode="r", encoding='utf-8') as f:
        return f.read()


def read_tpl(path: str) -> str:
    return read_file(f"{TEMPLATES_PATH}/{path}")


def template_to_html(
        template_path: str,
        template_name: str,
        **kwargs,
) -> str:
    """使用jinja2模板引擎通过html生成图片

    Args:
        template_path (str): 模板路径
        template_name (str): 模板名
        **kwargs: 模板内容
    Returns:
        str: html
    """

    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        enable_async=True,
    )
    template = template_env.get_template(template_name)

    return template.render(**kwargs)


def html_to_pic(
        html: str,
        wait: int = 0,
        template_path: str = f"file://{getcwd()}",
        type: Literal["jpeg", "png"] = "png",
        quality: Union[int, None] = None,
        device_scale_factor: float = 2,
        **kwargs,
) -> bytes:
    """html转图片

    Args:
        html (str): html文本
        wait (int, optional): 等待时间. Defaults to 0.
        template_path (str, optional): 模板路径 如 "file:///path/to/template/"
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        device_scale_factor: 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)
        **kwargs: 传入 page 的参数

    Returns:
        bytes: 图片, 可直接发送
    """
    if "file:" not in template_path:
        raise Exception("template_path 应该为 file:///path/to/template")
    page = get_new_page(device_scale_factor, **kwargs)
    page.goto(template_path)
    page.set_content(html, wait_until="networkidle")
    page.wait_for_timeout(wait)
    img_raw = page.screenshot(
        full_page=True,
        type=type,
        quality=quality,
    )
    page.close()
    return img_raw


def template_to_pic(
        template_path: str,
        template_name: str,
        templates: dict,
        pages: dict = {
            "viewport": {"width": 500, "height": 10},
            "base_url": f"file://{getcwd()}",
        },
        wait: int = 0,
        type: Literal["jpeg", "png"] = "png",
        quality: Union[int, None] = None,
        device_scale_factor: float = 2,
) -> bytes:
    """使用jinja2模板引擎通过html生成图片

    Args:
        template_path (str): 模板路径
        template_name (str): 模板名
        templates (dict): 模板内参数 如: {"name": "abc"}
        pages (dict): 网页参数 Defaults to
            {"base_url": f"file://{getcwd()}", "viewport": {"width": 500, "height": 10}}
        wait (int, optional): 网页载入等待时间. Defaults to 0.
        type (Literal["jpeg", "png"]): 图片类型, 默认 png
        quality (int, optional): 图片质量 0-100 当为`png`时无效
        device_scale_factor: 缩放比例,类型为float,值越大越清晰(真正想让图片清晰更优先请调整此选项)
    Returns:
        bytes: 图片 可直接发送
    """

    template_env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_path),
        enable_async=True,
    )
    template = template_env.get_template(template_name)

    return html_to_pic(
        template_path=f"file://{template_path}",
        html=template.render(**templates),
        wait=wait,
        type=type,
        quality=quality,
        device_scale_factor=device_scale_factor,
        **pages,
    )


def capture_element(
        url: str,
        element: str,
        timeout: float = 0,
        type: Literal["jpeg", "png"] = "png",
        quality: Union[int, None] = None,
        **kwargs,
) -> bytes:
    page = get_new_page(**kwargs)
    page.goto(url, timeout=timeout)
    img_raw = page.locator(element).screenshot(
        type=type,
        quality=quality,
    )
    page.close()
    return img_raw
