import json
import os
import threading
import uuid

from curl_cffi import requests
from curl_cffi.const import CurlHttpVersion
from logging_tools import loggers
import time


lock = threading.Lock()
session_file_lock = threading.Lock()
result_lock = threading.Lock()
plus_lines = []
free_lines = []
error_lines = []

# 单次请求超时（秒）；代理较慢时可调大
REQUEST_TIMEOUT = 90
# 连接被重置等瞬时错误时的重试次数与间隔基数（秒）
MAX_RETRIES = 5
# accounts/check、subscriptions 等与 check_plus 一致的重试次数
SESSION_HTTP_RETRIES = 6
RETRY_DELAY_BASE = 2.0

# OAuth 之后的订阅/套餐结果（格式同 check_plus 逻辑，文件名独立避免覆盖 check_plus 运行结果）
subscription_result_txt = "get_token_plus_result.txt"


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
            print(e)
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
            print(e)
            last_exc = e
            if attempt < MAX_RETRIES - 1 and _is_transient_network_error(e):
                time.sleep(RETRY_DELAY_BASE * (attempt + 1))
                continue
            raise
    raise last_exc


def append_plan_line(is_plus: bool, line: str) -> None:
    with result_lock:
        if is_plus:
            plus_lines.append(line)
        else:
            free_lines.append(line)


def append_error_line(line: str) -> None:
    with result_lock:
        error_lines.append(line)


def format_error_suffix(exc: BaseException) -> str:
    msg = str(exc).strip().replace("\r", " ").replace("\n", " ")
    msg = msg.replace("----", "|")
    if len(msg) > 800:
        msg = msg[:800] + "..."
    return msg


def response_json(resp, label: str):
    code = getattr(resp, "status_code", "?")
    raw = resp.text if resp.text is not None else ""
    body = raw.strip()
    if not body:
        raise ValueError(f"{label} HTTP{code} 响应体为空(常被代理断开或非HTTPS隧道导致)")
    lb = body.lstrip().lower()
    if lb.startswith("<!doctype") or lb.startswith("<html"):
        raise ValueError(
            f"{label} HTTP{code} 返回HTML(多为代理替换/拦截或未正确转发); "
            f"请换干净出口、核对代理HTTPS、或暂时关代理验证"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        preview = body[:300].replace("\r", " ").replace("\n", " ")
        raise ValueError(f"{label} HTTP{code} 非JSON:{e}; 预览:{preview}") from e


def _session_retry_delay(attempt: int) -> None:
    total = min(1.8**attempt, 45)
    time.sleep(total)


def session_get_retry(session, url, *, log_name: str, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last = None
    for attempt in range(SESSION_HTTP_RETRIES):
        try:
            return session.get(url, **kwargs)
        except Exception as e:
            last = e
            if attempt < SESSION_HTTP_RETRIES - 1:
                loggers.info(f"{log_name} 连接失败({e})，{attempt + 1}/{SESSION_HTTP_RETRIES} 次重试")
                _session_retry_delay(attempt)
            else:
                raise last


def write_subscription_result_file() -> None:
    with open(subscription_result_txt, "w", encoding="utf-8", errors="ignore") as f:
        for line in plus_lines:
            f.write(line + "\n")
        for line in free_lines:
            f.write(line + "\n")
        for line in error_lines:
            f.write(line + "\n")


def remove_account(account):
    lock.acquire()
    try:
        with open("check.txt", "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()

        with open("check.txt", "w", encoding="utf-8", errors="ignore") as file:
            for line in lines:
                if account[0] not in line or account[1] not in line:
                    file.write(line)
    finally:
        lock.release()


with open("check.txt", "r", encoding="utf-8-sig") as f:
    accounts = [line.strip().split("----") for line in f]

# 下面填上你的住宅IP http://user:pass@host:port
proxy = "http://storm-aiguoguo_area-US:a1chat199@us.stormip.cn:1000"
# 下面填线程数；单代理时过高易触发对端或代理 RST，建议 3～8
num_threads = 10

# 浏览器里已登录时访问 /api/auth/session 主要靠 Cookie（__Secure-next-auth.session-token 等）。
# 若要把「和浏览器完全一致」的 Cookie 带上，可把 F12 里整段 Cookie 粘到该文件（单行）。
BROWSER_COOKIE_FILE = "chatgpt_browser_cookie.txt"

# 从 chatgpt.com 已登录页 F12 → 任意 backend-api 请求里复制；站点大版本更新后可按需改
OAI_CLIENT_BUILD_NUMBER = "6128297"
OAI_CLIENT_VERSION = "prod-81e0c5cdf6140e8c5db714d613337f4aeab94029"
# 经 CONNECT 代理访问 chatgpt.com 时，HTTP/2 易被中途 RST，强制 HTTP/1.1
CHATGPT_HTTP_KWARGS = {"http_version": CurlHttpVersion.V1_1}




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


def _backend_api_headers(
    access_token: str,
    oai_did: str,
    oai_session_id: str,
    *,
    target_path: str,
    target_route: str,
    referer: str = "https://chatgpt.com/",
) -> dict:
    """对齐站内 fetch(backend-api) 的头；缺 oai-* / Cookie 时边缘节点常直接断开连接。"""
    cookie = _build_cookie_header(oai_did)
    return {
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        "authorization": "Bearer " + access_token,
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "priority": "u=1, i",
        "origin": "https://chatgpt.com",
        "referer": referer,
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ),
        "cookie": cookie,
        "oai-client-build-number": OAI_CLIENT_BUILD_NUMBER,
        "oai-client-version": OAI_CLIENT_VERSION,
        "oai-device-id": oai_did,
        "oai-language": "en-US",
        "oai-session-id": oai_session_id,
        "x-openai-target-path": target_path,
        "x-openai-target-route": target_route,
    }


def _chatgpt_warmup_get(
    session,
    *,
    proxies: dict,
    impersonate: str,
    oai_did: str,
    log_name: str,
) -> None:
    """先 GET 首页，让 Session 带上站点 Set-Cookie，再调 backend-api（与浏览器先打开站点再 XHR 一致）。"""
    try:
        session.get(
            "https://chatgpt.com/",
            headers={
                "accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "accept-language": "en-US,en;q=0.9",
                "upgrade-insecure-requests": "1",
                "user-agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "cookie": _build_cookie_header(oai_did),
            },
            proxies=proxies,
            impersonate=impersonate,
            timeout=REQUEST_TIMEOUT,
            **CHATGPT_HTTP_KWARGS,
        )
    except Exception as e:
        loggers.info(f"{log_name} 预热 GET / 失败({e})，仍继续 accounts/check")


def _chatgpt_accounts_check(
    *,
    username: str,
    access_token: str,
    oai_did: str,
    oai_session_id: str,
    proxies: dict,
):
    """accounts/check 专用：每轮新 Session + 轮换 impersonate + 强制 HTTP/1.1，缓解代理上 RST。"""
    url = "https://chatgpt.com/backend-api/accounts/check/v4-2023-04-27?timezone_offset_min=-480"
    last = None
    for attempt in range(SESSION_HTTP_RETRIES):
        sess = requests.Session()
        loggers.info(
            f"{username} accounts/check 第 {attempt + 1}/{SESSION_HTTP_RETRIES} 次 "
        )
        try:
            _chatgpt_warmup_get(
                sess,
                proxies=proxies,
                impersonate="safari",
                oai_did=oai_did,
                log_name=username,
            )
            check_resp = sess.get(
                url,
                headers=_backend_api_headers(
                    access_token,
                    oai_did,
                    oai_session_id,
                    target_path="/backend-api/accounts/check/v4-2023-04-27",
                    target_route="/backend-api/accounts/check/{version}",
                ),
                proxies=proxies,
                impersonate="safari",
                timeout=REQUEST_TIMEOUT,
                **CHATGPT_HTTP_KWARGS,
            )
            return check_resp, sess
        except Exception as e:
            last = e
            if attempt < SESSION_HTTP_RETRIES - 1:
                loggers.info(f"{username} accounts/check 异常: {e}")
                _session_retry_delay(attempt)
                continue
            raise last
    raise RuntimeError(f"{username} accounts/check 未返回且未抛出预期异常")


def get_token_thread(accounts):
    account = None
    # 函数内如有 `account_id = ...`，整段里 account_id 会被视为局部变量；先占位可避免误在 check 前引用时触发 UnboundLocalError
    account_id = None
    # OAuth 若已成功，此字段为服务端返回的 refresh；否则为 None，失败时写 失败.txt 仍用账号里旧 token
    new_refresh_for_error = None
    oai_did = None
    try:
        account = accounts.pop(0)
        while len(account) < 4:
            account.append("")
        username, gptpass, mailpass, old_refresh = (
            account[0],
            account[1],
            account[2],
            account[3],
        )
        proxies = {"http": proxy, "https": proxy}

        loggers.info(f"{username} 开始刷新")
        data = {
            "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
            "grant_type": "refresh_token",
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "refresh_token": old_refresh,
        }
        oauth_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://auth0.openai.com",
            "referer": "https://auth0.openai.com/",
        }

        r = request_post(
            "https://auth0.openai.com/oauth/token",
            json=data,
            headers=oauth_headers,
            proxies=proxies,
            impersonate="safari",
        )
        print(r.text)
        res_json = response_json(r, "oauth/token")

        access_token = res_json["access_token"]
        new_refresh_token = res_json["refresh_token"]
        new_refresh_for_error = new_refresh_token
        # /api/auth/session 的 Cookie 里 oai-did 须为随机 UUID，勿与 backend 的 account_id 混用
        oai_did = str(uuid.uuid4())
        oai_session_id = str(uuid.uuid4())

        print(f"[{username}] OAuth 成功，access_token:\n{access_token}\n", flush=True)
        loggers.info(f"{username} 已拿到 access_token，长度 {len(access_token)}")

        check_resp, chat_session = _chatgpt_accounts_check(
            username=username,
            access_token=access_token,
            oai_did=oai_did,
            oai_session_id=oai_session_id,
            proxies=proxies,
        )
        print(check_resp.text)
        check_data = response_json(check_resp, "accounts/check")
        account_ordering = check_data.get("account_ordering") or []
        if not account_ordering:
            raise ValueError("account_ordering 为空")
        account_id = str(account_ordering[0])

        sub_resp = session_get_retry(
            chat_session,
            f"https://chatgpt.com/backend-api/subscriptions?account_id={account_id}",
            log_name=f"{username} subscriptions",
            headers=_backend_api_headers(
                access_token,
                oai_did,
                oai_session_id,
                target_path="/backend-api/subscriptions",
                target_route="/backend-api/subscriptions",
            ),
            proxies=proxies,
            impersonate="safari",
            **CHATGPT_HTTP_KWARGS,
        )
        print(sub_resp.text)
        sub_data = response_json(sub_resp, "subscriptions")
        plan_type = (sub_data.get("plan_type") or "").strip()
        active_until = sub_data.get("active_until") or ""
        is_plus = plan_type.lower() == "plus"
        if is_plus:
            line = (
                f"{username}----{gptpass}----{mailpass}----{new_refresh_token}----{plan_type}----{active_until}"
            )
            append_plan_line(True, line)
            loggers.success(f"{username} plus plan={plan_type} until={active_until}")
        else:
            line = f"{username}----{gptpass}----{mailpass}----{new_refresh_token}----free"
            append_plan_line(False, line)
            loggers.success(f"{username} 非 plus plan={plan_type or 'unknown'}")

        session_url = "https://chatgpt.com/api/auth/session"
        session_r = session_get_retry(
            chat_session,
            session_url,
            log_name=f"{username} api/auth/session",
            headers=_navigate_session_headers(access_token, oai_did),
            proxies=proxies,
            impersonate="safari",
            **CHATGPT_HTTP_KWARGS,
        )
        body = session_r.text
        if not _session_json_useful(body):
            loggers.info(f"{username} navigate 样式 session 无有效 JSON，改用 fetch 样式重试")
            session_r = session_get_retry(
                chat_session,
                session_url,
                log_name=f"{username} api/auth/session(fetch)",
                headers=_fetch_session_headers(access_token, oai_did),
                proxies=proxies,
                impersonate="safari",
                **CHATGPT_HTTP_KWARGS,
            )
            body = session_r.text

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
            f.write(
                f"{username}----{gptpass}----{mailpass}----{new_refresh_token}----{access_token}\n"
            )
        with open("成功.txt", "a", encoding="utf-8", errors="ignore") as f:
            f.write(f"{username}----{gptpass}----{mailpass}----{new_refresh_token}\n")
        loggers.success(f"{username} 获取 session 并保存成功")
        remove_account(account)

    except IndexError:
        return False
    except Exception as e:
        print(e)
        if account is not None:
            u = account[0] if len(account) > 0 else ""
            g = account[1] if len(account) > 1 else ""
            m = account[2] if len(account) > 2 else ""
            old_rt = account[3] if len(account) > 3 else ""
            # 已拿到 OAuth 新 refresh 的场合，失败行与 失败.txt 都写新 token
            rt = new_refresh_for_error if new_refresh_for_error is not None else old_rt
            err_text = format_error_suffix(e)
            append_error_line(f"{u}----{g}----{m}----{rt}----错误{err_text}")
            try:
                remove_account(account)
            except Exception:
                pass
            with open("失败.txt", "a", encoding="utf-8", errors="ignore") as f:
                f.write(f"{u}----{g}----{m}----{rt}\n")
            loggers.error(f"{u} 失败")
    return True


def _main():
    while get_token_thread(accounts):
        pass


if __name__ == "__main__":
    thread_list = []
    for i in range(int(num_threads)):
        t = threading.Thread(target=_main)
        t.daemon = True
        t.start()
        thread_list.append(t)

    for t in thread_list:
        t.join()

    write_subscription_result_file()
    loggers.success(
        f"所有账号处理完成，订阅结果已写入 {subscription_result_txt}，程序将在50秒后自动关闭"
    )

    time.sleep(50)

    exit(1)
