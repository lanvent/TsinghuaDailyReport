# -*- coding:utf-8 -*-
# @Time : 2020/3/8 20:08
# @Author : naihai
import json
import requests
from bs4 import BeautifulSoup
import os

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Cache-Control': 'max-age=0',
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_4) \
        AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.122 Safari/537.36',
}


class Report(object):
    def __init__(self, user_name_, user_pass_):
        self.user_name = user_name_
        self.user_pass = user_pass_

        self.session = requests.session()
        self.session.headers.update(headers)

        self.server_id = "d42b05be-1ad8-4d96-8c1e-14be2bb24e26"
        self.resource_id = ""
        self.process_id = ""
        self.user_id = ""
        self.form_id = ""
        self.privilege_id = ""

        self.base_url = "https://thos.tsinghua.edu.cn"

        self.report_url = "https://thos.tsinghua.edu.cn/fp/view?m=fp#from=hall&" \
                          "serveID={0}&" \
                          "act=fp/serveapply".format(self.server_id)

        self.common_referer = "https://thos.tsinghua.edu.cn/fp/view?m=fp"

        self.form_data = None

        self.ds=""

    def run(self):
        try:
            self.__login()
        except Exception as e:
            print("登录失败", e)
        try:
            self.__check_service()
            self.__get_server_info()
            self.__get_data()
            self.__submit_report()
        except Exception as e:
            print("提交失败", e)
            raise RuntimeError(e)

    def __login(self):
        """登录 获取cookie"""

        res1 = self.session.get(self.base_url, headers=headers)  # 重定向到登录页面

        login_url_ = "https://id.tsinghua.edu.cn/do/off/ui/auth/login/check"
        headers_ = headers
        headers_["Referer"] = self.common_referer
        data_ = {
            "i_user": self.user_name,
            "i_pass": self.user_pass,
        }

        res2 = self.session.post(login_url_, data=data_, headers=headers_)
        # 登录成功 会重定向到 在线服务页面
        soup2 = BeautifulSoup(res2.text, 'html.parser')
        redirect_url = soup2.find("a")["href"]
        self.session.get(redirect_url)

        # 验证是否登录成功
        res3 = self.session.get(url=self.report_url, headers=headers)
        soup3 = BeautifulSoup(res3.text, 'html.parser')
        if soup3.find('form', attrs={'class': 'form-signin'}) is not None:
            print("登录失败")
            raise RuntimeError("Login Failed")
        else:
            self.session.headers.update(res3.headers)
            print("登录成功")

    def __check_service(self):
        url_ = "https://thos.tsinghua.edu.cn/fp/fp/serveapply/checkService"

        headers_ = self.session.headers
        headers_["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers_["Content-Type"] = "application/json;charset=UTF-8"
        headers_["Referer"] = self.common_referer
        headers_["Origin"] = "https://thos.tsinghua.edu.cn"
        headers_["X-Requested-With"] = "XMLHttpRequest"
        headers_["Host"] = "thos.tsinghua.edu.cn"

        data = {"serveID": self.server_id}
        try:
            response = self.session.post(url=url_, data=json.dumps(data))
            print("检查服务成功",response.text)
        except Exception as e:
            print("检查服务失败", e)
            raise RuntimeError("Get server info failed")
    def __get_server_info(self):
        """
        获取服务器提供的一些参数
        resource_id
        formid
        procID
        privilegeId
        """
        url_ = "https://thos.tsinghua.edu.cn/fp/fp/serveapply/getServeApply"

        headers_ = self.session.headers
        headers_["Accept"] = "application/json, text/javascript, */*; q=0.01"
        headers_["Content-Type"] = "application/json;charset=UTF-8"
        headers_["Referer"] = self.common_referer
        headers_["Origin"] = "https://thos.tsinghua.edu.cn"
        headers_["X-Requested-With"] = "XMLHttpRequest"
        headers_["Host"] = "thos.tsinghua.edu.cn"

        data = {"serveID": self.server_id, "from": "hall"}
        try:
            response = self.session.post(url=url_, data=json.dumps(data))
            result = response.json()

            self.resource_id = result["resource_id"]
            self.user_id = result["user_id"]
            self.form_id = result["formID"]
            self.process_id = result["procID"]
            self.privilege_id = result["privilegeId"]
            print("获取服务器参数成功")
        except Exception as e:
            print("获取服务器参数失败", e)
            raise RuntimeError("Get server info failed")

    def __get_data(self):
        """获取表单信息"""
        url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
               "status=select&" \
               "formid={0}&" \
               "service_id={1}&" \
               "process={2}&" \
               "privilegeId={3}".format(self.form_id,
                                        self.server_id,
                                        self.process_id,
                                        self.privilege_id)
        headers_ = self.session.headers
        headers_["Accept"] = "text/html,application/xhtml+xml,application/xml;" \
                             "q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        headers_["Host"] = "thos.tsinghua.edu.cn"
        cookies_ = self.session.cookies

        try:
            response = requests.get(url=url_, headers=headers, cookies=cookies_)
            soup = BeautifulSoup(response.text, 'html.parser')
            form_data_str = soup.find("script", attrs={"id": "dcstr"}).extract().string
            self.form_data = eval(form_data_str, type('js', (dict,), dict(__getitem__=lambda k, n: n))())
            records=self.form_data["body"]["dataStores"]["variable"]["rowSet"]["primary"]
            newdict=dict()
            recordDict=dict()
            for r in records:
                recordDict[r['name']]=r['value']
                if r['name'].startswith("5503059824640."):
                    name=r['name'].split('.')[1]
                    newdict[name]=r['value']
                    if len(r['value'])>0 and name!='MQXXDZ':
                        newdict[name+"_TEXT"]=r['value']
            newdict["XH"]=recordDict["716e67c5-a4ae-4d51-95b8-92c4a9c5.ID_NUMBER"]
            newdict["_t"]=3
            newdict["XM"]=recordDict["SYS_USER"]
            newdict["SZYX"]=recordDict["SYS_UNIT"]
            newdict["YXDM"]=recordDict["716e67c5-a4ae-4d51-95b8-92c4a9c5.UNIT_ID"]
            for k in self.form_data["body"]["dataStores"]:
                if k!="variable":
                    self.ds=k
                    break
            # print(self.ds)
            self.form_data["body"]["dataStores"][self.ds]["recordCount"]=1
            self.form_data["body"]["dataStores"][self.ds]["rowSet"]["primary"].append(newdict)
            print("获取表单成功")
        except Exception as e:
            print("获取表单失败", e)
            raise RuntimeError("Get form failed")

    def __submit_report(self):
        url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
               "status=update&" \
               "formid={0}&" \
               "workflowAction=startProcess&" \
               "workitemid=&" \
               "process={1}".format(self.form_id,
                                    self.process_id)

        referer_url_ = "https://thos.tsinghua.edu.cn/fp/formParser?" \
                       "status=select&" \
                       "formid={0}&" \
                       "service_id={1}&" \
                       "process={2}&" \
                       "privilegeId={3}".format(self.form_id,
                                                self.server_id,
                                                self.process_id,
                                                self.privilege_id)

        headers_ = self.session.headers
        headers_["Origin"] = "https://thos.tsinghua.edu.cn"
        headers_["Host"] = "thos.tsinghua.edu.cn"
        headers_["Sec-Fetch-Mode"] = "cors"
        headers_["Sec-Fetch-Site"] = "same-origin"
        headers_["Referer"] = referer_url_
        response = self.session.post(url_, data=json.dumps(self.form_data), headers=headers_)
        if response.status_code == requests.codes.OK:
            print("提交健康日报成功")
        else:
            print("提交健康日报失败")
            raise RuntimeError("Submit failed")


def load_info():
    with open("conf.ini") as rf:
        line = rf.readlines()
        user_name_ = line[0].strip().split("=")[1].strip()
        user_pass_ = line[1].strip().split("=")[1].strip()
    return user_name_, user_pass_


if __name__ == '__main__':
    # 首先检查环境变量中是否存在 USER_NAME USER_PASS
    # 该功能用于Github Action部署
    if os.getenv("USER_NAME") and os.getenv("USER_PASS"):
        print("User info found in env")
        user_name = os.getenv("USER_NAME")
        user_pass = os.getenv("USER_PASS")
    else:
        user_name, user_pass = load_info()
    Report(user_name, user_pass).run()
