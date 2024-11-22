# 系统配置
class Config:
    # ——————————————————————————————-插件控制 ——————————————————————————————-
    # 是否允许非!cmd形式的命令
    # 若为False则只有以!开头的命令才会被识别
    normal_cmd = True

    # 是否屏蔽监听群内信息
    # 为True时将屏蔽监听群默认事件
    prevent_listen_qq_msg = True

    # ——————————————————————————————-自动清理数据库 ——————————————————————————————-
    # 已经筛选到的优惠券保存天数,默认3天
    # tips:优惠券的有效期一般最长3天
    discount_message_save_day = 3

    # 监听群的全部备份消息保存天数,默认3天
    # tips:平均每一个群每天产生200条信息,若该值过大可能导致数据库查询变慢
    all_message_save_day = 3

    # 自动清理数据库的时间,默认为凌晨3点
    # tips:一般这时不会有群发送消息,清理数据库不用担心冲突
    clear_time = 3  # 取值范围:[0,23]

    # 是否开启自动发送清理报告。
    # 若开启,将在清理完成时发送报告,包含两个数据库的清理条数
    clear_report = True

    # ——————————————————————————————-优惠券信息处理流程 ——————————————————————————————-
    # 判断两条优惠券是否重复的阈值
    # 重复度高于该百分比时认为两条优惠券重复,取值范围(0,1)
    # tips:该值经长时间验证,如无必要请勿更改
    #      过高将导致大量重复信息
    #      过低将导致大量非重复信息被忽略,比如麦当劳的辣翅优惠券和汉堡优惠券可能被判定为重复信息
    similarity = 0.8

    # 判断一条信息是否是是可疑信息
    # 可疑信息的标准:当信息不含http且信息内英文字符数量低于该值时,认为是可疑信息
    # 当判断是可疑信息时,将根据relate_message_num自动发送可疑信息相关信息
    # tips:有的信息,诸如美团饿了么红包,是以二维码形式发送的
    #      一般这样的操作复杂不止一条信息,
    #      该功能旨在当收到这类不含链接的优惠券信息时自动发送相关信息
    suspicious_mes = 14  # 仅当relate_message_num值不为0时生效

    # 当消息判定为可疑信息时,自动发送可疑信息相关信息的数量
    # 为0时不发送,大于0时发送可疑信息前后各该值条信息
    # -------!!!!!请注意!!!!!-------
    # 该值大于0时可能导致信息过多过长,如若开启建议为1~2,即发送前后各1~2条信息
    # 若不是很担心错过诸如美团、饿了吗等没有优惠券的信息请不要更改该值
    relate_message_num = 0

    # 收到可疑信息时,发送可疑信息相关信息的时间范围
    # 超过该时间范围的信息即使是可疑信息的相关信息也不会发送该信息
    # 单位:分
    max_relate_message_time = 10  # 仅当relate_message_num值不为0时生效

    # 可疑信息是有效信息后续信息的时间范围
    # 在该时间范围内即使判定为可疑信息也不会触发可疑信息机制,也不会发送该信息
    # tips:有的群发送完一条优惠券后可能接着发一些解释信息,诸如"上面的麦当劳好价百年难遇快抢"
    #      此时虽然满足可疑信息标准但实则不是可疑信息,同时若再次发送则重复且无意义。
    #      该参数旨在避免这一情况
    # 单位:分
    effect_message_time = 20