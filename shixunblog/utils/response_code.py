# -- * -- coding : utf-8 -- * --
# @Author	    	:	Jumper.Han
# @Project	    	:	Project01
# @File		    	:	response_code.py
# @Time		    	:	2021/9/26 下午 8:55
# @Contact	    	:	Cynosure0313@live.cn
# @License	    	:	(C) Copyright 2019-2020
# @Software(IDE)	:	PyCharm
# @Site		    	:	https://www.jetbrains.com/pycharm/
# @Version	    	:	Python 3.8.2


class RETCODE:
    OK = "0" # 成功
    TMAGECODEERR = "4001" # 验证码错误
    THROTTLINGERR = "4002" # 短信发送频繁
    NECESSARYPARAMERR = "4003"  # 缺少必须的参数
    USERERR = "4004" # 用户错误
    PWDERR = "4005"  # 密码错误
    CPWDERR = "4006"  # 确认密码错误
    MOBILEERR = "4087" # 手机号错误
    SMSCODERR = "4008" # 短信验证码错误
    SESSIONERR = "4009" # 未登录