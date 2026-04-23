import requests
import json
import sys
import os
from datetime import datetime
import urllib3

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 在Windows PowerShell中启用ANSI颜色转义序列
os.system("")

# 颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def extract_user_id(token):
    """从token中提取user_id（格式为 user_xxx::，返回::前面的部分）"""
    try:
        if '::' in token:
            user_id = token.split('::')[0]
            return user_id
        else:
            return None
    except:
        return None

def check_cursor_subscription(token, proxies):
    """检查Cursor订阅状态，获取剩余额度并开启按需付费"""
    try:
        # 从token中提取user_id
        user_id = extract_user_id(token)
        if not user_id:
            return {
                'success': False,
                'skip': False,
                'error': 'token格式错误，无法提取user_id',
                'membership_type': None,
                'remaining_usd': None,
                'on_demand_enabled': None,
                'on_demand_activated': False
            }
        
        # 构造cookie
        cookie = f"workos_id={user_id}; WorkosCursorSessionToken={token}; "
        
        # 构造请求头
        headers = {
            "accept": "*/*",
            "origin": "https://cursor.com",
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "cookie": cookie,
            "Referer": "https://cursor.com/dashboard?tab=billing"
        }
        
        # 发送 usage-summary 请求
        url = "https://cursor.com/api/usage-summary"
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        data = response.json()
        print(data)
        
        membership_type = data.get('membershipType')
        
        # free账号直接跳过
        if membership_type == 'free':
            return {
                'success': False,
                'skip': True,
                'error': None,
                'membership_type': membership_type,
                'remaining_usd': None,
                'on_demand_enabled': None,
                'on_demand_activated': False
            }
        
        # 获取剩余额度
        individual_usage = data.get('individualUsage', {})
        plan = individual_usage.get('plan', {})
        remaining_raw = plan.get('remaining')
        remaining_usd = round(remaining_raw / 100, 2) if remaining_raw is not None else None
        
        # 检查 onDemand 状态
        on_demand = individual_usage.get('onDemand', {})
        on_demand_enabled = on_demand.get('enabled', False)
        on_demand_activated = False
        
        # 如果 onDemand 未开启，调用接口开启
        # if not on_demand_enabled:
        #     enable_url = "https://cursor.com/api/dashboard/enable-on-demand-spend"
        #     enable_headers = dict(headers)
        #     enable_headers["content-type"] = "application/json"
        #     enable_resp = requests.post(
        #         enable_url,
        #         headers=enable_headers,
        #         json={"hardLimit": 200},
        #         timeout=15,
        #         verify=False
        #     )
        #     dd = enable_resp.json()
        #     print(dd)
        #     if enable_resp.status_code == 200:
        #         on_demand_activated = True
        #     else:
        #         on_demand_activated = False
        
        return {
            'success': True,
            'skip': False,
            'error': None,
            'membership_type': membership_type,
            'remaining_usd': remaining_usd,
            'on_demand_enabled': on_demand_enabled,
            'on_demand_activated': on_demand_activated
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'skip': False,
            'error': f'请求错误: {str(e)}',
            'membership_type': None,
            'remaining_usd': None,
            'on_demand_enabled': None,
            'on_demand_activated': False
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'skip': False,
            'error': f'JSON解析错误: {str(e)}',
            'membership_type': None,
            'remaining_usd': None,
            'on_demand_enabled': None,
            'on_demand_activated': False
        }
    except Exception as e:
        return {
            'success': False,
            'skip': False,
            'error': f'处理错误: {str(e)}',
            'membership_type': None,
            'remaining_usd': None,
            'on_demand_enabled': None,
            'on_demand_activated': False
        }

def process_accounts():
    # 配置代理
    proxies = {
        'http': 'http://xiaoguo:Ji6dft4Cqd9l_eX6h3@199.119.138.75:1080',
        'https': 'http://xiaoguo:Ji6dft4Cqd9l_eX6h3@199.119.138.75:1080'
    }
    
    # 检查文件是否存在
    if not os.path.exists("check.txt"):
        print(f"{Colors.RED}错误：文件 check.txt 不存在{Colors.END}")
        return
    
    # 读取文件内容
    with open("check.txt", 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    results = []
    
    valid_lines = [l.strip() for l in lines if l.strip()]
    
    for i, token in enumerate(valid_lines, 1):
        print(f"{Colors.BLUE}[{i}/{len(valid_lines)}] 处理Token: {token[:20]}...{Colors.END}")
        
        # 检查订阅状态
        result = check_cursor_subscription(token, proxies)
        
        # 如果网络错误，进行重试
        retry_count = 0
        max_retries = 3
        while not result['success'] and result['error'] and 'Connection' in result['error'] and retry_count < max_retries:
            retry_count += 1
            print(f"{Colors.YELLOW}  网络连接错误，正在重试... (第{retry_count}次){Colors.END}")
            result = check_cursor_subscription(token, proxies)
        
        # 根据结果生成输出
        if result.get('skip'):
            print(f"{Colors.YELLOW}  跳过 - 账号类型: free{Colors.END}")
            continue
        
        if result['success']:
            remaining = result['remaining_usd']
            remaining_str = f"${remaining}" if remaining is not None else "未知"
            if result['on_demand_enabled']:
                on_demand_str = "按需付费已开启"
            elif result['on_demand_activated']:
                on_demand_str = "按需付费已激活"
            else:
                on_demand_str = "按需付费激活失败"
            result_line = f"{token}----成功----剩余:{remaining_str}----{on_demand_str}"
            results.append(result_line)
            print(f"{Colors.GREEN}  成功 - 类型: {result['membership_type']} - 剩余: {remaining_str} - {on_demand_str}{Colors.END}")
        else:
            error_msg = result['error'] if result['error'] else '未知错误'
            result_line = f"{token}----失败:{error_msg}"
            results.append(result_line)
            print(f"{Colors.RED}  失败 - {error_msg}{Colors.END}")
    
    # 按剩余金额从高到低排序
    def get_remaining(line):
        try:
            part = [p for p in line.split('----') if p.startswith('剩余:$')]
            if part:
                return float(part[0].replace('剩余:$', ''))
        except:
            pass
        return -1

    results.sort(key=get_remaining, reverse=True)

    # 写入结果到新文件
    output_file = "check_result.txt"
    with open(output_file, 'w', encoding='utf-8') as file:
        for result in results:
            file.write(result + '\n')
            
    print(f"{Colors.GREEN}\n处理完成！结果已保存到: {output_file}{Colors.END}")
    
    # 统计结果
    success_count = sum(1 for r in results if "----成功----" in r)
    fail_count = sum(1 for r in results if "----失败" in r)
    
    print(f"{Colors.BLUE}成功: {success_count}, 失败: {fail_count}{Colors.END}")

if __name__ == "__main__":
    process_accounts()

