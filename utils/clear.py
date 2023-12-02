"""
维护优惠卷数据库、全部信息数据库数据。负责执行每日任务,删除过期数据
"""
import logging
import threading
from datetime import datetime, timedelta

from mirai import Plain
from pkg.utils import context
from plugins.discountAssistant.utils.database import DatabaseManager
from plugins.discountAssistant.utils.message import Message


class Clear:
    """清理类.负责存储信息"""

    def __init__(self, discount_message_save_day: int, all_message_save_day: int, clear_time: int, clear_report: bool):
        self.admin_qq = getattr(context.get_config(), 'admin_qq')  # 管理员qq
        start_timer(discount_message_save_day, all_message_save_day, clear_time, clear_report, self.admin_qq)


# 开始定时任务
def start_timer(discount_message_save_day: int, all_message_save_day: int, clear_time, clear_report, admin_qq):
    """开始定时任务"""
    delay = get_delay(clear_time)  # 延时时长:s
    param = {  # 传递参数
        'discount_message_save_day': discount_message_save_day,
        'all_message_save_day': all_message_save_day,
        'clear_time': clear_time,
        'clear_report': clear_report,
        'admin_qq': admin_qq
    }

    threading.Timer(delay, clear_task, kwargs=param).start()  # 启动定时任务
    # threading.Timer(3, clear_task, param).start()  # 启动定时任务

    hours = delay // 3600
    minutes = (delay % 3600) // 60
    seconds = (delay % 3600) % 60

    logging.info(
        f'数据库清理任务启动成功.将在{hours}时{minutes}分{seconds}秒后执行,清理{discount_message_save_day}天内的优惠券信息、{all_message_save_day}天内的全部信息')


# 得到距离下次清理的时间:s
def get_delay(clear_time) -> int:
    """得到距离下次清理的时间:s"""
    # 获取当前时间
    current_time = datetime.now()
    # 目标时间
    target_time = current_time.replace(hour=clear_time, minute=0, second=0, microsecond=0)

    # 如果目标时间在当前时间之前，说明已经过了今天的整点，需要调整到明天的整点
    if target_time < current_time:
        target_time += timedelta(days=1)

    # 计算时间差
    time_difference = target_time - current_time

    # 提取总秒数
    total_seconds = time_difference.total_seconds()
    return int(total_seconds)


# 清理任务
def clear_task(discount_message_save_day: int, all_message_save_day: int, clear_time, clear_report, admin_qq,
               repeat_task: bool = True):
    """清理任务"""
    discount_mes_cnt = delete_message('saleMes', discount_message_save_day)  # 清理优惠卷数据库
    all_mes_cnt = delete_message('allMes', all_message_save_day)  # 清理全部数据库

    report = f'数据库清理任务执行完毕,共清理{discount_mes_cnt}条优惠券信息,{all_mes_cnt}条全部信息'  # 报告

    logging.info(report)
    if clear_report:  # 发送管理员
        if not isinstance(admin_qq, list):
            admin_qq = [int(admin_qq)]
        qq_type = [0 for _ in range(len(admin_qq))]
        mes_chain = [Plain(report)]
        Message({}).send_message(admin_qq, qq_type, mes_chain)  # 发送信息

    if repeat_task:
        # 再次执行任务
        start_timer(discount_message_save_day, all_message_save_day, clear_time, clear_report, admin_qq)

    return report


# 删除信息
def delete_message(database, save_day) -> int:
    """
    清理优惠券数据库
    :return:删除条数
    """
    svc = DatabaseManager(database)
    table = svc.query(['*'])
    # 获取当前日期
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    delete_cnt = 0
    for row in table:
        date_string = row['time']
        date_format = '%m-%d %H:%M'
        # 将字符串转换为datetime对象
        date = datetime.strptime(date_string, date_format).replace(hour=0, minute=0, second=0, microsecond=0,
                                                                   year=datetime.now().year)
        # 计算两个日期之间的差距
        difference = today - date
        # 判断差距是否大于等于指定范围
        if difference > timedelta(days=save_day - 1):
            svc.delete({'id': row['id']})
            delete_cnt += 1

    return delete_cnt


if __name__ == 'main':
    print('ok')
    clear_task(3, 3, 3, False, [123])
