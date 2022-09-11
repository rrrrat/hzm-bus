import smtplib
from email.mime.text import MIMEText
from email.header import Header
import uuid
import json
import datetime
import requests
import logging
import ddddocr
import pymysql
from selenium import webdriver
import random


class BuyTicket:
    def __init__(self):
        self.person_info = None
        self.tickets_log = None
        self.tickets = None
        self.account_info = None
        self.cookies = ''
        self.global_uuid = uuid.uuid4()
        # Selenium setting begin
        self.options = webdriver.ChromeOptions()
        self.options.add_experimental_option('excludeSwitches', ['enable-automation'])
        self.options.add_experimental_option('useAutomationExtension', False)
        self.options.add_argument('--headless')
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-gpu')
        self.options.add_argument('--disable-dev-shm-usage')
        # Selenium Setting end
        self.max = random.randint(2, 4)
        self.session = requests.session()
        self.login_url = 'http://i.hzmbus.com/webh5api/login'  # 登录地址
        self.query_ticket_url = 'http://i.hzmbus.com/webh5api/manage/query.book.info.data'  # 车票查询地址
        # Email Setting begin
        self.from_addr = 'email_address'
        self.password = 'email_password'
        self.to_addr = 'email_to_address'
        self.smtp_server = 'smtp_server_address'
        # EMail Setting end
        # DB Setting begin
        self.db = pymysql.connect(host='bj-cynosdbmysql-grp-1wd2xs2k.sql.tencentcdb.com', port=23776, user='hzm_bus_demo',
                                  password='Hzm_bus_demo@', charset='utf8mb4', database='hzm_bus_demo')
        self.cursor = self.db.cursor()
        # DB Setting end
        self.mac = uuid.UUID(int=uuid.getnode()).hex[-12:]
        self.headers = {
            'Host': 'i.hzmbus.com',
            'Connection': 'keep-alive',
            'Content-Length': '148',
            'sec-ch-ua': '"Chromium";v="104", " Not A;Brand";v="99", "Google Chrome";v="104"',
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json;charset=UTF-8',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36',
            'sec-ch-ua-platform': '"Windows"',
            'ec-Fetch-Sit': 'same-origin',
            'ec-Fetch-Mod': 'cors',
            'ec-Fetch-Des': 'empty',
            'Accept - Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.get_cookies()

    def get_cookies(self):
        """
        获取cookies， 此处使用了selenium
        :return:
        """
        print('Get cookies')
        driver = webdriver.Chrome(options=self.options)

        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',
                               {'source': 'Object.defineProperty(navigator, "webdriver", {get: () => undefined})'})
        self.cookies = ''
        driver.get(self.login_url)
        cookies = driver.get_cookies()
        if 'PHPSESSID' not in str(cookies):
            self.get_cookies()
        for cookie in cookies:
            name = cookie['name']
            value = cookie['value']
            self.cookies += f'{name}={value};'
        self.headers['Cookie'] = self.cookies
        driver.close()

    def email(self):
        """
        Email
        :return:
        """
        msg = MIMEText('请尽快上号支付' + str(self.account_info), 'plain', 'utf-8')
        msg['From'] = Header('test')
        msg['To'] = Header('HZM-BUS')
        subject = '中了'
        msg['Subject'] = Header(subject, 'utf-8')
        try:
            smtpobj = smtplib.SMTP_SSL(self.smtp_server)
            smtpobj.connect(self.smtp_server, 465)
            smtpobj.login(self.from_addr, self.password)
            smtpobj.sendmail(self.from_addr, self.to_addr, msg.as_string())
            print("吱！汇报进度" + str(self.account_info))
        except smtplib.SMTPException:
            print("无法发送邮件")
        finally:
            smtpobj.quit()

    def save_log(self, log_level, log_info):
        if log_level == 'error':
            logging.error(log_info)
        elif log_level == 'info':
            logging.error(log_info)
        else:
            logging.error(log_info)
        log_sql = f"insert into hzmbus_t_log(account_username, account_password, log_level, log_info, tickets, ident) values ('{self.account_info[0]}', '{self.account_info[1]}', '{log_level}', '{log_info}', '{self.tickets_log}', '{self.mac + '_' + str(self.global_uuid)}')"
        self.cursor.execute(log_sql)
        self.cursor.execute('commit')

    def db_query(self, sql):
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_ticket_info(self, cdate):
        """
        票务查询
        :param cdate: 购票日期
        :return:
        """
        while True:
            try:
                max_people_data = {"bookDate": str(cdate), "lineCode": "HKGZHO",
                                   "appId": "HZMBWEB_HK", "joinType": "WEB",
                                   "version": "2.7.202207.1213", "equipment": "PC"}
                book_info = self.session.post(self.query_ticket_url,
                                              data=json.dumps(max_people_data),
                                              headers=self.headers)
                if book_info.json()['code'] != 'SUCCESS':
                    logging.error(book_info.json()['message'])
                    self.login()
                    return
                return book_info.json()['responseData']
            except Exception as error:
                self.get_cookies()
                self.login()
                logging.error('访问异常')
                continue

    def get_date_domain(self):
        """
        获取购票时间区间
        可选
        any: 任意可购票时间
        具体日期列表， 例: ['2022-01-01'. '2022-01-02']
        :return:
        """
        if self.tickets[0][3] != 'any':
            return str(self.tickets[0][3]).split(',')
        begin_date = datetime.datetime.now().date()
        while True:
            end_date = self.get_ticket_info(begin_date)
            if not end_date:
                self.login()
            else:
                end_date = end_date[0]['maxBookDate']
                break
        date_domain = []
        while True:
            try:
                date_domain.append(begin_date.__str__())
                begin_date += datetime.timedelta(days=1)
                if str(begin_date) == end_date:
                    date_domain.append(end_date)
                    break
            except:
                continue
        return date_domain

    def ticket_query(self, date_domain):
        """
        票务查询--购票
        :param date_domain: 购票区间日期
        :return:
        """
        for buy_date in date_domain:
            logging.info(f'当前查询日期[{buy_date}]')
            get_book_info = self.get_ticket_info(buy_date)
            if not get_book_info:
                logging.warning('开始切换账号')
                self.login()
                continue
            max_people = 0
            for item in get_book_info:
                try:
                    max_people += int(item["maxPeople"])
                    log = f'时间: {buy_date + " " + item["beginTime"]}, 票数: {max_people}, 状态: {"不能购买" if max_people > self.max else "正在购买"}'
                    if max_people > self.max:
                        self.save_log('info', log)
                        self.buy_ticket(buy_date, item["beginTime"])
                except:
                    logging.error('当日无车票信息')
            log = f'时间: {buy_date}, 票数: {max_people}, 状态: {"不能购买" if max_people == 0 else "可以购买"}'
            self.save_log('info', log)

    def buy_ticket(self, begin_date, begin_time):
        """
        购票
        :param begin_date: 开始日期
        :param begin_time: 开始时间
        :return:
        """
        buy_url = 'http://i.hzmbus.com/webh5api/captcha?1'
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'DNT': '1',
            'Host': 'i.hzmbus.com',
            'Cookie': self.cookies,
            'If-None-Match': 'W/"62f25921-937"',
            'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/103.0.0.0 Safari/537.36'}
        while True:
            a = self.session.get(buy_url, headers=headers)
            code = ocr.classification(a.content)
            try:
                if len(code) != 4:
                    continue
                int(code)
                break
            except:
                continue
        logging.info(code)
        buy_data = {"ticketData": begin_date, "lineCode": "HKGZHO", "startStationCode": "HKG",
                    "endStationCode": "ZHO",
                    "boardingPointCode": "HKG01", "breakoutPointCode": "ZHO01", "currency": "2", "ticketCategory": "1",
                    "tickets": self.person_info,
                    "amount": 6500 * len(self.person_info), "feeType": 9, "totalVoucherpay": 0, "voucherNum": 0,
                    "voucherStr": "", "totalBalpay": 0,
                    "totalNeedpay": 6500 * len(self.person_info), "bookBeginTime": begin_time,
                    "bookEndTime": begin_time,
                    "captcha": code,
                    "sessionId": "", "sig": "", "token": "",
                    "timestamp": 1660551038, "appId": "HZMBWEB_HK",
                    "joinType": "WEB", "version": "2.7.202207.1213", "equipment": "PC"}
        headers = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate, br',
                   'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                   'Connection': 'keep-alive',
                   'Content-Length': '591',
                   'Content-Type': 'application/json;charset=UTF-8',
                   'DNT': '1',
                   'Cookie': self.cookies,
                   'Host': 'i.hzmbus.com',
                   'Origin': 'https://i.hzmbus.com',
                   'Referer': 'https://i.hzmbus.com/webhtml/ticket_details?xlmc_1=%E9%A6%99%E6%B8%AF&xlmc_2=%E7%8F%A0%E6%B5%B7&xllb=1&xldm=HKGZHO&code_1=HKG&code_2=ZHO',
                   'Sec-Fetch-Dest': 'empty',
                   'Sec-Fetch-Mode': 'cors',
                   'Sec-Fetch-Site': 'same-origin',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36',
                   'sec-ch-ua': '".Not/A)Brand";v="99", "Google Chrome";v="103", "Chromium";v="103"',
                   'sec-ch-ua-mobile': '?0',
                   'sec-ch-ua-platform': '"Windows"'}

        buy_ticket = self.session.post('http://i.hzmbus.com/webh5api/ticket/buy.ticket', headers=headers,
                                       data=json.dumps(buy_data))
        self.save_log('info', str(buy_ticket.json()).replace("'", ""))
        if buy_ticket.json()['code'] == 'SUCCESS':
            self.email()
            return self.run()
        elif buy_ticket.json()['code'] == 'FAIL':
            self.login()
            return
        else:
            self.login()
            return self.buy_ticket(begin_date, begin_time)

    def login(self):
        """
        用户登录
        :return:
        """
        try:
            self.account_info = self.db_query(
                'select username, password from hzmbus_t_buy_account where  accountlock = 0 order by rand() limit 1')[0]
            user = {"webUserid": self.account_info[0],
                    "passWord": self.account_info[1], "code": "", "appId": "HZMBWEB_HK",
                    "joinType": "WEB", "version": "2.7.202207.1213", "equipment": "PC"}
            string = json.dumps(user)
            login_msg = self.session.post(url=self.login_url, data=string, headers=self.headers, verify=False)
            # 以下代码为应对下次源站更新准备
            # cookies = ''
            # for cookie in login_msg.cookies.items():
            #     for k, v in cookie:
            #         cookies += f'{k}={v};'
            # print(cookies)
            if login_msg.json()['code'] != 'SUCCESS':
                logging.info(login_msg.json()['msg'])
                self.login()
            logging.info('登录成功' + str(self.account_info))
        except Exception as error:
            logging.error(error)
            self.login()

    def run(self):
        """
        开始运行
        :return:
        """
        self.tickets = self.db_query('select id, username, idcard, buy_date from hzmbus_v_ticket_wait')
        tickets_id = [ticket[0] for ticket in self.tickets]
        self.cursor.execute(
            f'update hzmbus_t_ticket set is_run = 1 where id in ({str(tickets_id).replace("[", "").replace("]", "")})')
        self.cursor.execute('commit')
        self.tickets_log = [f'{ticket[1]}-{ticket[2]}' for ticket in self.tickets]
        self.tickets_log = str(self.tickets_log).replace("['", "").replace("']", "").replace("'", "")
        self.person_info = []
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - [line:%(lineno)d] - %(message)s - ' + str(self.tickets_log), )
        self.login()
        for ticket in self.tickets:
            person = {"ticketType": "00", "idCard": ticket[2], "idType": 1, "userName": ticket[1], "telNum": ""}
            self.person_info.append(person)
        date_domain = self.get_date_domain()
        while True:
            self.ticket_query(date_domain)


if __name__ == '__main__':
    BuyTicket().run()
