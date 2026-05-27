import json
import signal
import threading
import time

from curl_cffi import requests

from logging_tools import loggers

# 代理在高并发下容易 RST；可适当减小 num_threads
REQUEST_TIMEOUT = 90
MAX_HTTP_RETRIES = 6
RETRY_BACKOFF_BASE = 1.8

shutdown_event = threading.Event()


class ShutdownRequested(BaseException):
    """协作式退出：Ctrl+C 设置 shutdown_event，工作线程在重试间隙响应。"""


def _request_shutdown(signum=None, frame=None):
    shutdown_event.set()


lock = threading.Lock()
result_lock = threading.Lock()
plus_lines = []
free_lines = []
error_lines = []


def remove_account(account):
    lock.acquire()
    try:
        with open("check_plus.txt", "r", encoding="utf-8", errors="ignore") as file:
            lines = file.readlines()

        with open("check_plus.txt", "w", encoding="utf-8", errors="ignore") as file:
            for line in lines:
                if account[0] not in line or account[1] not in line:
                    file.write(line)
        file.close()
    finally:
        lock.release()


with open("check_plus.txt", "r", encoding="utf-8-sig") as f:
    accounts = [line.strip().split("----") for line in f]

# 下面填上你的住宅IP http://user:pass@host:port
# proxy = 'http://storm-aiguoguo_area-JP:a1chat199@proxy.stormip.cn:1000'
proxy = "http://storm-aiguoguo_area-US:a1chat199@us.stormip.cn:1000"
# proxy = "http://xiaoguo:Ji6dft4Cqd9l_eX6h3@199.119.138.131:1080"
# 下面填线程数 默认30
num_threads = 30

subscription_result_txt = "check_plus_result.txt"


def append_plan_line(is_plus: bool, line: str):
    with result_lock:
        if is_plus:
            plus_lines.append(line)
        else:
            free_lines.append(line)


def append_error_line(line: str):
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
            f"{label} HTTP{code} 返回HTML(多为代理替换/拦截或未正确转发POST到oauth/token); "
            f"请换干净出口、核对代理HTTPS、或暂时关代理验证"
        )
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        preview = body[:300].replace("\r", " ").replace("\n", " ")
        raise ValueError(f"{label} HTTP{code} 非JSON:{e}; 预览:{preview}") from e


def _retry_delay(attempt: int) -> None:
    total = min(RETRY_BACKOFF_BASE**attempt, 45)
    deadline = time.time() + total
    while time.time() < deadline:
        if shutdown_event.is_set():
            raise ShutdownRequested()
        time.sleep(min(0.25, max(0.0, deadline - time.time())))


def session_get_retry(session, url, *, log_name: str, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last = None
    for attempt in range(MAX_HTTP_RETRIES):
        if shutdown_event.is_set():
            raise ShutdownRequested()
        try:
            return session.get(url, **kwargs)
        except Exception as e:
            last = e
            if attempt < MAX_HTTP_RETRIES - 1:
                loggers.info(f"{log_name} 连接失败({e})，{attempt + 1}/{MAX_HTTP_RETRIES} 次重试")
                _retry_delay(attempt)
            else:
                raise last


def post_retry(url, *, log_name: str, **kwargs):
    kwargs.setdefault("timeout", REQUEST_TIMEOUT)
    last = None
    for attempt in range(MAX_HTTP_RETRIES):
        if shutdown_event.is_set():
            raise ShutdownRequested()
        try:
            return requests.post(url, **kwargs)
        except Exception as e:
            last = e
            if attempt < MAX_HTTP_RETRIES - 1:
                loggers.info(f"{log_name} 连接失败({e})，{attempt + 1}/{MAX_HTTP_RETRIES} 次重试")
                _retry_delay(attempt)
            else:
                raise last


def register_account_thread(accounts):
    try:
        account = accounts.pop(0)
    except IndexError:
        raise

    proxies = {"http": proxy, "https": proxy}
    while len(account) < 4:
        account.append("")
    username, gptpass, mailpass, refresh_token = account[0], account[1], account[2], account[3]

    try:
        if shutdown_event.is_set():
            raise ShutdownRequested()
        loggers.info(f"{username} 开始刷新")
        data = {
            "client_id": "app_LlGpXReQgckcGGUo2JrYvtJK",
            "grant_type": "refresh_token",
            "redirect_uri": "com.openai.chat://auth0.openai.com/ios/com.openai.chat/callback",
            "refresh_token": refresh_token,
        }
        oauth_headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "origin": "https://auth0.openai.com",
            "referer": "https://auth0.openai.com/",
        }

        r = post_retry(
            "https://auth0.openai.com/oauth/token",
            log_name=f"{username} oauth/token",
            json=data,
            headers=oauth_headers,
            proxies=proxies,
            impersonate="chrome131",
        )
        print(r.text)
        res_json = response_json(r, "oauth/token")

        access_token = res_json["access_token"]
        refresh_token = res_json["refresh_token"]

        api_headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": "Bearer " + access_token,
            "origin": "https://chatgpt.com",
            "referer": "https://chatgpt.com/",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        }

        session = requests.Session()
        check_resp = session_get_retry(
            session,
            "https://chatgpt.com/backend-api/accounts/check/v4-2023-04-27?timezone_offset_min=-480",
            log_name=f"{username} accounts/check",
            headers=api_headers,
            proxies=proxies,
            impersonate="safari",
        )
        check_resp.raise_for_status()
        print(2222222222222222222222222)
        check_data = response_json(check_resp, "accounts/check")
        account_ordering = check_data.get("account_ordering") or []
        if not account_ordering:
            raise ValueError("account_ordering 为空")

        account_id = account_ordering[0]

        sub_resp = session_get_retry(
            session,
            f"https://chatgpt.com/backend-api/subscriptions?account_id={account_id}",
            log_name=f"{username} subscriptions",
            headers=api_headers,
            proxies=proxies,
            impersonate="safari",
        )
        sub_resp.raise_for_status()
        sub_data = response_json(sub_resp, "subscriptions")
        plan_type = (sub_data.get("plan_type") or "").strip()
        active_until = sub_data.get("active_until") or ""

        is_plus = plan_type.lower() == "plus"
        if is_plus:
            line = f"{username}----{gptpass}----{mailpass}----{refresh_token}----{plan_type}----{active_until}"
            append_plan_line(True, line)
            loggers.success(f"{username} plus plan={plan_type} until={active_until}")
        else:
            line = f"{username}----{gptpass}----{mailpass}----{refresh_token}----free"
            append_plan_line(False, line)
            loggers.success(f"{username} 非 plus plan={plan_type or 'unknown'}")

        remove_account(account)
        with open("成功.txt", "a", encoding="utf-8", errors="ignore") as f:
            f.write(f"{username}----{gptpass}----{mailpass}----{refresh_token}\n")

    except ShutdownRequested:
        raise
    except IndexError:
        raise
    except Exception as e:
        print(e)
        err_text = format_error_suffix(e)
        append_error_line(f"{username}----{gptpass}----{mailpass}----错误{err_text}")
        remove_account(account)
        with open("失败.txt", "a", encoding="utf-8", errors="ignore") as f:
            f.write(f"{username}----{gptpass}----{mailpass}----{refresh_token}\n")
        loggers.error(f"{username} 失败 ")


def _main():
    while True:
        if shutdown_event.is_set():
            break
        try:
            register_account_thread(accounts)
        except ShutdownRequested:
            break
        except IndexError:
            break
        except Exception:
            break


def write_subscription_result_file():
    with open(subscription_result_txt, "w", encoding="utf-8", errors="ignore") as f:
        for line in plus_lines:
            f.write(line + "\n")
        for line in free_lines:
            f.write(line + "\n")
        for line in error_lines:
            f.write(line + "\n")


if __name__ == "__main__":
    signal.signal(signal.SIGINT, _request_shutdown)

    thread_list = []
    for i in range(int(num_threads)):
        t = threading.Thread(target=_main)
        t.daemon = True
        t.start()
        thread_list.append(t)

    _shutdown_wait_logged = False
    try:
        while any(t.is_alive() for t in thread_list):
            for t in thread_list:
                t.join(timeout=0.5)
            if shutdown_event.is_set() and not _shutdown_wait_logged:
                loggers.info(
                    "已请求退出，等待线程结束（单次 HTTP 最长约 REQUEST_TIMEOUT 秒；"
                    "libcurl 执行期间无法抢占）"
                )
                _shutdown_wait_logged = True
    except KeyboardInterrupt:
        shutdown_event.set()

    write_subscription_result_file()
    msg = (
        f"结果已写入 {subscription_result_txt}"
        if shutdown_event.is_set()
        else f"所有账号处理完成，结果已写入 {subscription_result_txt}"
    )
    loggers.success(f"{msg}，程序将在50秒后自动关闭")

    end = time.time() + 50
    try:
        while time.time() < end:
            time.sleep(min(0.5, end - time.time()))
            if shutdown_event.is_set():
                break
    except KeyboardInterrupt:
        pass

    exit(1)
