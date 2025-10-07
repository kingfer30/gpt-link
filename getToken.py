import json

from curl_cffi import requests
import threading
from logging_tools import loggers
import time


lock = threading.Lock()

def remove_account(account):
    lock.acquire()
    try:
        with open("mailboxs.txt", "r", encoding='utf-8', errors='ignore') as file:
            lines = file.readlines()

        with open("mailboxs.txt", "w", encoding='utf-8', errors='ignore') as file:
            for line in lines:
                if account[0] not in line or account[1] not in line:
                    file.write(line)
        file.close()
    finally:
        lock.release()

with open('rt.txt', 'r', encoding='utf-8-sig') as f:
    accounts = [line.strip().split('----') for line in f]

# 下面填上你的住宅IP http://user:pass@host:port 
proxy = 'http://storm-aiguoguo_area-US:a1chat199@us.stormip.cn:1000'
# 下面填线程数 默认30
num_threads = 30
def register_account_thread(accounts):
    try:
        proxies = {
            'http': proxy,
            'https': proxy
        }
        account = accounts.pop(0)
        username, refresh_token = account

        loggers.info(f'{username} 开始刷新')
        data = {
            "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
            "grant_type": "refresh_token",
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "refresh_token": refresh_token
        }

        r = requests.post("https://auth0.openai.com/oauth/token", json=data, proxies=proxies, impersonate='safari')
        res_json = json.loads(r.text)

        access_token = res_json['access_token']
        print(access_token)
    except:
            pass

def _main():
    while True:
        try:
            register_account_thread(accounts)
        except:
            break
if __name__ == '__main__':
    thread_list = []
    for i in range(int(num_threads)):
        t = threading.Thread(target=_main)
        t.daemon = True
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    loggers.success(f"所有账号注册完成，程序将在50秒后自动关闭")

    time.sleep(50)

    exit(1)

