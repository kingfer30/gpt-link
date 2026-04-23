import requests
import json
import sys
import os
from datetime import datetime, timedelta

# 在Windows PowerShell中启用ANSI颜色转义序列
os.system("")

# 颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def parse_date(date_str):
    """解析日期字符串，返回datetime对象用于排序"""
    if not date_str:
        return datetime.min
    try:
        # 处理ISO格式日期（可能包含Z后缀）
        date_str_clean = date_str.replace('Z', '+00:00')
        return datetime.fromisoformat(date_str_clean)
    except:
        try:
            # 尝试其他常见格式
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        except:
            # 如果都失败，返回最小日期（会排在最后）
            return datetime.min
    
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
        acc_pass = line.strip()
        if not acc_pass:
            continue
            
        # 分割email和password
        if '----' not in acc_pass:
            print(f"{Colors.RED}格式错误: {acc_pass} (应为 email----password 格式){Colors.END}")
            continue
            
        email, password = acc_pass.split('----', 1)
        print(f"{Colors.BLUE}[{i}/{len(lines)}] 处理账户: {email}{Colors.END}")
        
        found_cursor_welcome = False
        cursor_date = None
        is_expired = False  # 标记邮件是否超过2天
        
        # 检查两个邮箱：inbox 和 junk
        for mailbox in ['inbox', 'junk']:
            try:
                # 构建URL
                url = f"https://www.xckj.site/easy-mailbox/emails?email={email}&password={password}&mailbox={mailbox}"
                
                # 发送请求（使用代理）
                response = requests.get(url, proxies=proxies, timeout=10)
                response.raise_for_status()
                
                # 解析JSON响应
                emails_data = response.json()
                
                # 检查是否为空数组
                if not emails_data:
                    continue
                    
                # 收集所有匹配"Welcome to Cursor!"的邮件
                matching_emails = []
                for email_item in emails_data:
                    if email_item.get('subject') == "Welcome to Cursor!":
                        matching_emails.append(email_item)
                
                # 如果有匹配的邮件，按日期排序取最新的
                if matching_emails:
                    # 按日期排序（降序，最新的在前）
                    matching_emails.sort(key=lambda x: parse_date(x.get('date')), reverse=True)
                    
                    # 取最新的邮件
                    latest_email = matching_emails[0]
                    found_cursor_welcome = True
                    cursor_date = latest_email.get('date')
                    
                    # 检查日期是否超过2天
                    email_datetime = parse_date(cursor_date)
                    if email_datetime != datetime.min:
                        days_diff = (datetime.now(email_datetime.tzinfo) - email_datetime).days
                        if days_diff > 2:
                            is_expired = True
                        
                # 如果找到了就退出循环
                if found_cursor_welcome:
                    break
                    
            except requests.exceptions.RequestException as e:
                error_str = str(e)
                # 如果错误包含"Connection"，说明是网络问题，需要重试
                if "Connection" in error_str:
                    # print(f"{Colors.YELLOW}  网络连接错误 ({mailbox}): {e} - 账户: {email}，正在重试...{Colors.END}")
                    retry_count = 0
                    max_retries = 5
                    while retry_count < max_retries:
                        try:
                            retry_count += 1
                            # 重新发送请求（使用代理）
                            response = requests.get(url, proxies=proxies, timeout=10)
                            response.raise_for_status()
                            
                            # 解析JSON响应
                            emails_data = response.json()
                            
                            # 检查是否为空数组
                            if not emails_data:
                                break
                                
                            # 收集所有匹配"Welcome to Cursor!"的邮件
                            matching_emails = []
                            for email_item in emails_data:
                                if email_item.get('subject') == "Welcome to Cursor!":
                                    matching_emails.append(email_item)
                            
                            # 如果有匹配的邮件，按日期排序取最新的
                            if matching_emails:
                                # 按日期排序（降序，最新的在前）
                                matching_emails.sort(key=lambda x: parse_date(x.get('date')), reverse=True)
                                
                                # 取最新的邮件
                                latest_email = matching_emails[0]
                                found_cursor_welcome = True
                                cursor_date = latest_email.get('date')
                                
                                # 检查日期是否超过2天
                                email_datetime = parse_date(cursor_date)
                                if email_datetime != datetime.min:
                                    days_diff = (datetime.now(email_datetime.tzinfo) - email_datetime).days
                                    if days_diff > 2:
                                        is_expired = True
                                
                                print(f"{Colors.GREEN}  重试成功 ({mailbox}): 账户: {email} (重试次数: {retry_count}){Colors.END}")
                                break
                            else:
                                break
                        except requests.exceptions.RequestException as retry_e:
                            # 检查是否达到最大重试次数
                            if retry_count >= max_retries:
                                print(f"{Colors.RED}  重试失败 ({mailbox}): 超过最大重试次数({max_retries}次) - 账户: {email}{Colors.END}")
                                break
                            # 继续重试
                            continue
                        except json.JSONDecodeError as retry_e:
                            print(f"{Colors.RED}  重试时JSON解析错误 ({mailbox}): {retry_e} - 账户: {email}{Colors.END}")
                            break
                        except Exception as retry_e:
                            print(f"{Colors.RED}  重试时处理错误 ({mailbox}): {retry_e} - 账户: {email}{Colors.END}")
                            break
                    
                    # 检查是否因为超过重试次数而退出
                    if not found_cursor_welcome and retry_count >= max_retries:
                        print(f"{Colors.RED}  网络连接失败 ({mailbox}): 重试{max_retries}次后仍然失败 - 账户: {email}{Colors.END}")
                    
                    # 如果找到了就退出外层循环
                    if found_cursor_welcome:
                        break
                else:
                    print(f"{Colors.RED}  请求错误 ({mailbox}): {e} - 账户: {email}{Colors.END}")
                    continue
            except json.JSONDecodeError as e:
                print(f"{Colors.RED}  JSON解析错误 ({mailbox}): {e} - 账户: {email}{Colors.END}")
                continue
            except Exception as e:
                print(f"{Colors.RED}  处理错误 ({mailbox}): {e} - 账户: {email}{Colors.END}")
                continue
        
        # 根据结果生成输出
        if found_cursor_welcome:
            if is_expired:
                # 邮件日期超过2天，标记为未订阅
                result_line = f"{acc_pass}----失败:未订阅----{cursor_date}"
                results.append(result_line)
                print(f"{Colors.RED}  失败:未订阅 (邮件日期超过2天): {email} - 日期: {cursor_date}{Colors.END}")
            elif cursor_date:
                result_line = f"{acc_pass}----成功----{cursor_date}"
                results.append(result_line)
                print(f"{Colors.GREEN}  成功: {email} - 日期: {cursor_date}{Colors.END}")
            else:
                result_line = f"{acc_pass}----成功----日期未找到"
                results.append(result_line)
                print(f"{Colors.YELLOW}  成功但日期未找到: {email}{Colors.END}")
        else:
            result_line = f"{acc_pass}----失败"
            results.append(result_line)
            print(f"{Colors.RED}  失败: {email}{Colors.END}")
    
    # 写入结果到新文件
    output_file ="check_result.txt"
    with open(output_file, 'w', encoding='utf-8') as file:
        for result in results:
            file.write(result + '\n')
            
    print(f"{Colors.GREEN}\n处理完成！结果已保存到: {output_file}{Colors.END}")
    
    # 统计结果
    success_count = sum(1 for r in results if "----成功----" in r)
    fail_count = sum(1 for r in results if "失败" in r)
    
    print(f"{Colors.BLUE}成功: {success_count}, 失败: {fail_count}{Colors.END}")
    
    print(f"处理完成！结果已保存到: {output_file}")

if __name__ == "__main__":
    process_accounts()