"""
检测 HTTP(S) 代理是否连通：出口 IP、JSON 接口、Auth0 发现文档（与 check_plus 同栈 curl_cffi）。

用法:
  python test_proxy.py --proxy "http://user:pass@host:port"
  set HTTPS_PROXY=http://... && python test_proxy.py
  python test_proxy.py   # 不配代理则仅测本机直连
"""
from __future__ import annotations

import argparse
import json
import os
import sys

TIMEOUT = 35

try:
    from curl_cffi import requests
except ImportError:
    print("请先安装: pip install curl_cffi")
    sys.exit(1)


def pick_proxy(cli: str) -> str:
    return (
        (cli or "").strip()
        or os.environ.get("HTTPS_PROXY", "").strip()
        or os.environ.get("HTTP_PROXY", "").strip()
    )


def proxy_error_hints(exc: Exception) -> list[str]:
    """根据 curl/libcurl 常见报错给出中文排查提示（非官方文档，仅供参考）。"""
    msg = str(exc)
    lines: list[str] = []
    if "CONNECT tunnel failed" in msg:
        lines.append(
            "说明: HTTPS 会先向代理发 CONNECT 建隧道；失败表示「到代理这一跳」就没建好，"
            "目标站(ipify/Auth0)尚未参与。"
        )
    if "response 610" in msg or " 610" in msg:
        lines.extend(
            [
                "610: 多为代理服务商自定义的 HTTP 状态（非标准 RFC），表示拒绝本次 CONNECT 或线路异常。",
                "可排查: ①账号/密码/端口是否填对 ②套餐是否含 HTTPS/隧道 ③余额/并发/地区参数 ④问供应商 610 含义。",
            ]
        )
    if "407" in msg:
        lines.append("407: 代理要求认证，检查 URL 内 user:pass 或白名单 IP。")
    if "502" in msg or "503" in msg:
        lines.append("502/503: 代理上游故障或过载，换节点或稍后重试。")
    if "Connection was reset" in msg or "Recv failure" in msg:
        lines.append(
            "连接被重置: 常见于出口风控、代理主动断流、或 TLS 指纹与线路不兼容；可换节点/换 impersonate/直连对比。"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="测试代理是否可用（curl_cffi）")
    parser.add_argument(
        "--proxy",
        default="",
        help='代理 URL，如 http://user:pass@host:port；也可设环境变量 HTTPS_PROXY',
    )
    parser.add_argument(
        "--impersonate",
        default="chrome131",
        help="curl_cffi TLS 指纹，默认 chrome131",
    )
    args = parser.parse_args()
    proxy_url = pick_proxy(args.proxy)
    proxies = (
        {"http": proxy_url, "https": proxy_url} if proxy_url else None
    )

    if proxy_url:
        print(f"使用代理: {proxy_url.split('@')[-1] if '@' in proxy_url else proxy_url}")
    else:
        print("未配置代理，仅测试本机直连")

    tests = [
        ("出口 IP (ipify)", "https://api.ipify.org?format=json"),
        (
            "Auth0 发现文档 (应返回 JSON，非 HTML)",
            "https://auth0.openai.com/.well-known/openid-configuration",
        ),
        ("ChatGPT 首页 (仅看状态码)", "https://chatgpt.com/"),
    ]

    ok_all = True
    for name, url in tests:
        print(f"\n--- {name} ---")
        print(f"GET {url}")
        try:
            r = requests.get(
                url,
                proxies=proxies,
                impersonate=args.impersonate,
                timeout=TIMEOUT,
            )
            text = r.text or ""
            head = text.lstrip()[:120].replace("\n", " ")
            print(f"HTTP {r.status_code}  正文长度 {len(text)}")
            if head.startswith("<") or head.lower().startswith("<!doctype"):
                print(f"预览(HTML): {head}...")
                if "openid-configuration" in url or "oauth" in url:
                    print("  [失败] 该地址期望 JSON，却得到 HTML，常见于代理替换/拦截或未正确转发 HTTPS")
                    ok_all = False
            else:
                print(f"预览: {head}...")
                if "ipify" in url:
                    try:
                        j = json.loads(text)
                        print(f"  解析: ip = {j.get('ip', j)}")
                    except json.JSONDecodeError:
                        print("  [失败] 非 JSON")
                        ok_all = False
                elif "openid-configuration" in url:
                    try:
                        j = json.loads(text)
                        iss = j.get("issuer", "")
                        print(f"  解析: issuer = {iss[:80]}...")
                    except json.JSONDecodeError:
                        print("  [失败] 非 JSON")
                        ok_all = False
        except Exception as e:
            print(f"[异常] {type(e).__name__}: {e}")
            for hint in proxy_error_hints(e):
                print(f"  → {hint}")
            ok_all = False

    print("\n==========")
    if ok_all:
        print("结论: 上述检测均通过（至少未判为明显失败）。")
        return 0
    print("结论: 存在失败项，请检查代理类型(HTTP CONNECT)、账号密码、出口地区。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
