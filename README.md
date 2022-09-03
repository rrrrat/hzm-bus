# 港珠澳大桥穿梭巴士抢票
```angular2html
支持多登录账号, 多同行人 
支持运行多个程序同时抢票(需同一个数据库), 提高成功率
预计非周二，10位乘客中4位。
周二本脚本无效, 滑块验证可参考 https://github.com/Algortex/hzm-goldenbus 自行配置
购票网站: https://i.hzmbus.com/
```
## 部署
### 0x01 准备 | 难度 1-5
```angular2html
Mysql数据库(项目内已连接数据库仅供测试使用) | 难度: 4
Chrome浏览器(Linux也可正常部署，有疑问联系) | Windows难度: 1 Linux难度: 2
Chrome driver(百度一下，你就知道。注！需对应版本) | 难度: 1
网站账号(越多越好, 预计2000个账号大概能跑20个本脚本) | 难度: 5
```
### 0x02 安装依赖
```shell
pip3 install -r requirements.txt
```

### 0x03 修改文件内Setting相关内容
```python
# Email Setting begin
self.from_addr = 'email_address' # Email用户名
self.password = 'email_password' # Email密码
self.to_addr = 'email_to_address' # 接收邮件地址
self.smtp_server = 'smtp_server_address' # 邮件SMTP服务器
# EMail Setting end
# DB Setting begin
self.db = pymysql.connect(host='bj-cynosdbmysql-grp-1wd2xs2k.sql.tencentcdb.com', port=23776, user='hzm_bus_demo',
                          password='Hzm_bus_demo@', charset='utf8mb4', database='hzm_bus_demo')
self.cursor = self.db.cursor()
# DB Setting end
```

### 0x04 开始运行
```shell
python3 main.py
```

## 表说明
| 表名  | 说明      | 注意                                                      |
|-----|---------|---------------------------------------------------------|
| hzmbus_t_ticket | 乘客信息存放表 | 通过buy_group来确定同行人并且排序, order字段历史遗留问题需和buy_group一致, 负责卖萌 |
| hzmbus_t_log | 日志表     | ident标注机器mac地址和进程唯一编号, SUCCESS存在于log_info则表示购买成功        |
| hzmbus_t_buy_account | 网站账号表   | 没什么要注意的, 加就完事了                                          |

## 常用SQL
```sql
select * from hzmbus_t_log where log_info like '%SUCCESS%' and createtime
between date_sub(now(), interval 60 MINUTE) and  now() ; -- 查询60分钟内购票成功的账号信息及乘客信息
----
SELECT distinct tickets
FROM hzmbus_t_log  where createtime
between date_sub(now(), interval 1 MINUTE) and now();  -- 查询当前正在运行的乘客信息
----
select distinct ident from hzmbus_t_log where createtime
between date_sub(now(), interval 5 MINUTE) and  now() ; -- 查询当前正在运行的节点
```

## 关于集群
```angular2html
给个大家一个思路
在run while内加控制, 通过网站实现群控
```

## 关于后期更新
```angular2html
当前无优化思路，欢迎大家给出意见。
乘客填报系统已制作完成, 后面有需要将会开源
```

## 须知
### 该程序仅用于学习用途，禁止用作非法用途！
### 个人维护，不定期更新
### 该程序造成的任何法律责任，财产损失或者人身伤害等问题，本人概不负责！
### 企鹅: 843636329
