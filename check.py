import requests
from bs4 import BeautifulSoup
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
            
        # 构建URL
        url = f"https://ms.lqqq.cc/web/{acc_pass}"
        print(f"{Colors.BLUE}[{i}/{len(lines)}] 处理账户: {acc_pass}{Colors.END}")
        try:
            # 发送请求
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # 检查请求是否成功
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找所有包含指定文本的span
            mail_titles = soup.find_all('span', class_='mail-title')
            
            found_subscription = False
            for mail_title in mail_titles:
                if mail_title and "ChatGPT - Your new plan" in mail_title.text:
                    found_subscription = True
                    break
            
            if found_subscription:
                print(f"账户: {acc_pass}----已订阅! ")
                # 查找下一个span元素获取日期
                next_span = mail_title.find_next_sibling('span')
                if next_span:
                    # 提取日期（去掉括号和空格）
                    date_str = next_span.text.strip().replace('(', '').replace(')', '').strip()
                    result_line = f"{acc_pass}----成功----{date_str}"
                    results.append(result_line)
                    print(f"{Colors.GREEN}  成功: {acc_pass} - 日期: {date_str}{Colors.END}")
                else:
                    result_line = f"{acc_pass}----成功----日期未找到"
                    results.append(result_line)
                    print(f"{Colors.YELLOW}  成功但日期未找到: {acc_pass}{Colors.END}")
            else:
                result_line = f"{acc_pass}----失败"
                results.append(result_line)
                print(f"{Colors.RED}  失败: {acc_pass}{Colors.END}")
                
        except requests.exceptions.RequestException as e:
            error_msg = f"{acc_pass}----请求失败"
            results.append(error_msg)
            print(f"{Colors.RED}  请求错误: {e} - 账户: {acc_pass}{Colors.END}")
        except Exception as e:
            error_msg = f"{acc_pass}----处理失败"
            results.append(error_msg)
            print(f"{Colors.RED}  处理错误: {e} - 账户: {acc_pass}{Colors.END}")
    
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