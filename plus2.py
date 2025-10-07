from proofofWork import get_answer_token, get_config, get_requirements_token
import random
import uuid
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

with open('mailboxs.txt', 'r', encoding='utf-8-sig') as f:
    accounts = [line.strip().split('----') for line in f]

# 下面填上你的住宅IP http://user:pass@host:port
# proxy = 'http://storm-aiguoguo_area-JP:a1chat199@proxy.stormip.cn:1000'
# 下面填线程数 默认30
num_threads = 30
def register_account_thread(accounts):
    try:
        account = accounts.pop(0)
        username, refresh_token = account

        loggers.info(f'{username} 开始刷新')
        data = {
            "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
            "refresh_token": refresh_token
        }

        r = requests.post("https://public.xyhelper.cn/oauth/oai2xy", json=data, impersonate='safari')
        res_json = json.loads(r.text)

        access_token = res_json['access_token']
        while True:
            seed = format(random.random())
            diff = "059dfe"
            ua_config = get_config(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Mobile/15E148 Safari/604.1")
            answer, result = get_answer_token(seed, diff, ua_config)
            ppp = get_requirements_token(ua_config)
            if result == True:
                break
            else:
                continue
        session = requests.Session()
        token_id = str(uuid.uuid4())
        data = {"p": answer, "id": token_id, "flow": "chatgpt_checkout"}

        headers = {
            'accept': '*/*',
            'content-type': 'text/plain;charset=UTF-8',
            'sec-fetch-site': 'cross-site',
            'origin': 'https://auth0.openai.com',
            'sec-fetch-mode': 'cors',
            'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_0_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0.1 Mobile/15E148 Safari/604.1',
            'sec-fetch-dest': 'empty',
            'accept-language': 'en-US,en;q=0.9',
            'priority': 'u=3, i',
        }
        response = session.post('https://chatgpt.com/backend-api/sentinel/req', headers=headers, data=data, impersonate='safari')
        data = json.loads(response.text)
        token = data['token']
        sentinelToken = {"p": ppp, "t": "", "c": token, "id": token_id, "flow": "chatgpt_checkout"}
        sentinelToken = json.dumps(sentinelToken)

        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': 'Bearer ' + access_token,
            'oai-device-id': 'f319fc4f-60cc-4081-9c95-c7c4a0771f2f',
            'oai-language': 'en-US',
            'openai-sentinel-token': sentinelToken,
            'origin': 'https://chatgpt.com',
            'priority': 'u=1, i',
            'referer': 'https://chatgpt.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }

        response = session.post('https://chatgpt.com/backend-api/payments/checkout', headers=headers, impersonate='safari')
        url = json.loads(response.text)['url']
        remove_account(account)
        with open('成功.txt', 'a', encoding='utf-8', errors='ignore') as f:
            f.write(f'{username}----{refresh_token}----{url}\n')
            loggers.success(f"{username} 取连接成功 {url}")

    except Exception as e:
        print(e)
        remove_account(account)
        with open('失败.txt', 'a', encoding='utf-8', errors='ignore') as f:
            f.write(f'{username}----{refresh_token}\n')
            loggers.error(f"{username} 失败 ")

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

