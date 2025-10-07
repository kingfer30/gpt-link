import requests
import json
import sys
import os

# 在Windows PowerShell中启用ANSI颜色转义序列
os.system("")

# 颜色代码
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    
def process_accounts():
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
        
        # 检查两个邮箱：inbox 和 junk
        for mailbox in ['inbox', 'junk']:
            try:
                # 构建URL
                url = f"https://www.xckj.site/easy-mailbox/emails?email={email}&password={password}&mailbox={mailbox}"
                
                # 发送请求
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                
                # 解析JSON响应
                emails_data = response.json()
                
                # 检查是否为空数组
                if not emails_data:
                    continue
                    
                # 遍历邮件数据
                for email_item in emails_data:
                    if email_item.get('subject') == "Welcome to Cursor!":
                        found_cursor_welcome = True
                        cursor_date = email_item.get('date')
                        break
                        
                # 如果找到了就退出循环
                if found_cursor_welcome:
                    break
                    
            except requests.exceptions.RequestException as e:
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
            if cursor_date:
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
    success_count = sum(1 for r in results if "成功" in r)
    fail_count = sum(1 for r in results if "失败" in r)
    
    print(f"{Colors.BLUE}成功: {success_count}, 失败: {fail_count}{Colors.END}")
    
    print(f"处理完成！结果已保存到: {output_file}")

if __name__ == "__main__":
    process_accounts()