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

def check_cursor_subscription(email, token, proxies):
    """检查Cursor订阅状态"""
    try:
        # 从token中提取user_id
        user_id = extract_user_id(token)
        if not user_id:
            return {
                'success': False,
                'error': 'token格式错误，无法提取user_id',
                'membership_type': None,
                'start_date': None
            }
        
        # 构造cookie
        cookie = f"workos_id={user_id}; WorkosCursorSessionToken={token}; "
        
        # 构造请求头
        headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9",
            "cache-control": "no-cache",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "sec-ch-ua": "\"Not(A:Brand\";v=\"8\", \"Chromium\";v=\"144\", \"Google Chrome\";v=\"144\"",
            "sec-ch-ua-arch": "\"x86\"",
            "sec-ch-ua-bitness": "\"64\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"10.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "cookie": cookie,
            "Referer": "https://cursor.com/dashboard?tab=billing"
        }
        
        # 发送请求
        url = "https://cursor.com/api/usage-summary"
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.raise_for_status()
        
        # 解析响应
        data = response.json()
        
        # 提取需要的信息
        membership_type = data.get('membershipType')
        billing_cycle_start = data.get('billingCycleStart')
        
        # 判断是否成功（membershipType为pro）
        is_success = membership_type == 'pro'
        
        return {
            'success': is_success,
            'error': None,
            'membership_type': membership_type,
            'start_date': billing_cycle_start
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'请求错误: {str(e)}',
            'membership_type': None,
            'start_date': None
        }
    except json.JSONDecodeError as e:
        return {
            'success': False,
            'error': f'JSON解析错误: {str(e)}',
            'membership_type': None,
            'start_date': None
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'处理错误: {str(e)}',
            'membership_type': None,
            'start_date': None
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
    
    for i, line in enumerate(lines, 1):
        # 清理行内容
        acc_token = line.strip()
        if not acc_token:
            continue
            
        # 分割email和token
        if '----' not in acc_token:
            print(f"{Colors.RED}格式错误: {acc_token} (应为 email----token 格式){Colors.END}")
            continue
            
        email, token = acc_token.split('----', 1)
        print(f"{Colors.BLUE}[{i}/{len(lines)}] 处理账户: {email}{Colors.END}")
        
        # 检查订阅状态
        result = check_cursor_subscription(email, token, proxies)
        
        # 如果网络错误，进行重试
        retry_count = 0
        max_retries = 3
        while not result['success'] and result['error'] and 'Connection' in result['error'] and retry_count < max_retries:
            retry_count += 1
            print(f"{Colors.YELLOW}  网络连接错误，正在重试... (第{retry_count}次){Colors.END}")
            result = check_cursor_subscription(email, token, proxies)
        
        # 根据结果生成输出
        if result['success']:
            # 订阅成功（membershipType为pro）
            start_date = result['start_date'] if result['start_date'] else '日期未找到'
            result_line = f"{acc_token}----成功----{start_date}"
            results.append(result_line)
            print(f"{Colors.GREEN}  成功: {email} - 订阅类型: {result['membership_type']} - 开始时间: {start_date}{Colors.END}")
        else:
            # 失败
            if result['membership_type']:
                # 有返回数据但不是pro
                result_line = f"{acc_token}----失败:非Pro会员({result['membership_type']})----{result.get('start_date', '')}"
                print(f"{Colors.RED}  失败: {email} - 订阅类型: {result['membership_type']} (非Pro会员){Colors.END}")
            else:
                # 请求失败或其他错误
                error_msg = result['error'] if result['error'] else '未知错误'
                result_line = f"{acc_token}----失败:{error_msg}"
                print(f"{Colors.RED}  失败: {email} - {error_msg}{Colors.END}")
            results.append(result_line)
    
    # 写入结果到新文件
    output_file = "check_result.txt"
    with open(output_file, 'w', encoding='utf-8') as file:
        for result in results:
            file.write(result + '\n')
            
    print(f"{Colors.GREEN}\n处理完成！结果已保存到: {output_file}{Colors.END}")
    
    # 统计结果
    success_count = sum(1 for r in results if "----成功----" in r)
    fail_count = sum(1 for r in results if "失败" in r)
    
    print(f"{Colors.BLUE}成功: {success_count}, 失败: {fail_count}{Colors.END}")

if __name__ == "__main__":
    process_accounts()

