import json
import os
import threading
import uuid

from curl_cffi import requests
from logging_tools import loggers
import time


lock = threading.Lock()
session_file_lock = threading.Lock()

# 单次请求超时（秒）；代理较慢时可调大
REQUEST_TIMEOUT = 90
# 连接被重置等瞬时错误时的重试次数与间隔基数（秒）
MAX_RETRIES = 5
RETRY_DELAY_BASE = 2.0


def _is_transient_network_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    return (
        "recv failure" in msg
        or "connection was reset" in msg
        or "connection reset" in msg
        or "curl: (56)" in msg
        or "curl: (35)" in msg
        or "ssl" in msg
        and "error" in msg
        or "timeout" in msg
        or "timed out" in msg
        or "eof" in msg
    )


def request_post(url, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return requests.post(url, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1 and _is_transient_network_error(e):
                time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                continue
            raise
    raise last_exc


def request_get(url, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last_exc = None
    for attempt in range(MAX_RETRIES):
        try:
            return requests.get(url, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1 and _is_transient_network_error(e):
                time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                continue
            raise
    raise last_exc


def remove_account(account):
    lock.acquire()
    try:
        with open("mailboxs.txt", "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()

        with open("mailboxs.txt", "w", encoding="utf-8", errors="ignore") as file:
            for line in lines:
                if account[0] not in line or account[1] not in line:
                    file.write(line)
    finally:
        lock.release()


with open("mailboxs.txt", "r", encoding="utf-8-sig") as f:
    accounts = [line.strip().split("----") for line in f]

# 下面填上你的住宅IP http://user:pass@host:port
proxy = "http://xiaoguo:Ji6dft4Cqd9l_eX6h3@199.119.138.131:1080"
# 下面填线程数；单代理时过高易触发对端或代理 RST，建议 3～8
num_threads = 1

# 浏览器里已登录时访问 /api/auth/session 主要靠 Cookie（__Secure-next-auth.session-token 等）。
# 若要把「和浏览器完全一致」的 Cookie 带上，可把 F12 里整段 Cookie 粘到该文件（单行）。
BROWSER_COOKIE_FILE = "chatgpt_browser_cookie.txt"


def _read_optional_browser_cookie():
    if not os.path.isfile(BROWSER_COOKIE_FILE):
        return None
    try:
        with open(BROWSER_COOKIE_FILE, "r", encoding="utf-8", errors="ignore") as f:
            s = f.read().strip()
        return s or None
    except OSError:
        return None


def _build_cookie_header(oai_did: str) -> str:
    extra = _read_optional_browser_cookie()
    base = f"oai-did={oai_did}"
    if not extra:
        return base
    if "oai-did=" in extra:
        return extra
    return f"{extra}; {base}"


def _session_json_useful(text: str) -> bool:
    try:
        j = json.loads(text)
    except Exception:
        return False
    if not isinstance(j, dict):
        return False
    return bool(j.get("user") or j.get("accessToken") or j.get("expires"))


def _navigate_session_headers(access_token: str, oai_did: str) -> dict:
    """与已登录后从地址栏打开该 URL 时接近（参见 header.txt）：document + navigate + 长 accept。"""
    accept = (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,"
        "image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"
    )
    cookie = _build_cookie_header(oai_did)
    return {
        "accept": accept,
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=0, i",
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        'sec-ch-ua-platform': '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "cookie": cookie,
        "authorization": "Bearer " + access_token,
    }


def _fetch_session_headers(access_token: str, oai_did: str) -> dict:
    """站内 fetch 常见头；部分场景下 Bearer 仅在这种请求下有效。"""
    cookie = _build_cookie_header(oai_did)
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "authorization": "Bearer " + access_token,
        "referer": "https://chatgpt.com/",
        "origin": "https://chatgpt.com",
        'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
        "sec-ch-ua-mobile": "?0",
        'sec-ch-ua-platform': '"Windows"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "cookie": cookie,
    }


def get_token_thread(accounts):
    account = None
    try:
        proxies = {"http": proxy, "https": proxy}
        account = accounts.pop(0)
        username, gptpass, mailpass, refresh_token = account

        loggers.info(f"{username} 开始刷新")
        data = {
            "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
            "grant_type": "refresh_token",
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "refresh_token": refresh_token,
        }

        r = request_post(
            "https://auth0.openai.com/oauth/token",
            json=data,
            proxies=proxies,
            impersonate="safari",
        )
        res_json = json.loads(r.text)

        access_token = res_json["access_token"]
        new_refresh_token = res_json["refresh_token"]

        print(f"[{username}] OAuth 成功，access_token:\n{access_token}\n", flush=True)
        loggers.info(f"{username} 已拿到 access_token，长度 {len(access_token)}")

        oai_did = str(uuid.uuid4())
        session_url = "https://chatgpt.com/api/auth/session"
        session_r = request_get(
            session_url,
            headers=_navigate_session_headers(access_token, oai_did),
            proxies=proxies,
            impersonate="chrome131",
        )
        body = session_r.text
        if not _session_json_useful(body):
            loggers.info(f"{username} navigate 样式 session 无有效 JSON，改用 fetch 样式重试")
            session_r = request_get(
                session_url,
                headers=_fetch_session_headers(access_token, oai_did),
                proxies=proxies,
                impersonate="chrome131",
            )
            body = session_r.text

        remove_account(account)
        session_file_lock.acquire()
        try:
            with open("auth_session.txt", "a", encoding="utf-8", errors="ignore") as f:
                f.write(f"----{username}----\n")
                f.write(body)
                if not body.endswith("\n"):
                    f.write("\n")
                f.write("\n")
        finally:
            session_file_lock.release()
        with open("access_tokens.txt", "a", encoding="utf-8", errors="ignore") as f:
            f.write(f"{username}----{gptpass}----{mailpass}----{new_refresh_token}----{access_token}\n")
        loggers.success(f"{username} 获取 session 并保存成功")

    except IndexError:
        return
    except Exception as e:
        print(e)
        if account is not None:
            with open("失败.txt", "a", encoding="utf-8", errors="ignore") as f:
                u = account[0]
                g = account[1]
                m = account[2]
                rt = account[3]
                f.write(f"{u}----{g}----{m}----{rt}\n")
            loggers.error(f"{account[0]} 失败")


def _main():
    while True:
        try:
            get_token_thread(accounts)
        except:
            break


if __name__ == "__main__":
    thread_list = []
    for i in range(int(num_threads)):
        t = threading.Thread(target=_main)
        t.daemon = True
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    loggers.success(f"所有账号处理完成，程序将在50秒后自动关闭")

    time.sleep(50)

    exit(1)
