import requests
from bs4 import BeautifulSoup
import sys
import os
import re

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
            target_mail_title = None
            for mail_title in mail_titles:
                if mail_title and "Your customer portal login link" in mail_title.text:
                    found_subscription = True
                    target_mail_title = mail_title
                    break
            
            if found_subscription:
                print(f"账户: {acc_pass}----找到客户门户登录链接! ")
                # 查找同级span后的<a>标签
                next_span = target_mail_title.find_next_sibling('span')
                if next_span:
                    # 在下一个span中查找<a>标签
                    link_tag = next_span.find_next_sibling('a')
                    if link_tag and link_tag.get('href'):
                        href = link_tag.get('href')
                        if href.startswith('/show_email/'):
                            # 构建完整的URL
                            full_url = f"https://ms.lqqq.cc{href}"
                            print(f"{Colors.BLUE}  访问链接: {full_url}{Colors.END}")
                            
                            try:
                                # 访问新页面
                                link_response = requests.get(full_url, timeout=10)
                                link_response.raise_for_status()
                                
                                # 解析新页面
                                link_soup = BeautifulSoup(link_response.text, 'html.parser')
                                
                                # 查找<div class="content">
                                content_div = link_soup.find('div', class_='content')
                                if content_div:
                                    # 在content div中查找括号链接
                                    content_text = content_div.get_text()
                                    # 使用正则表达式查找括号中以https://pay.openai.com/p/session开头的链接
                                    bracket_links = re.findall(r'\((https://pay\.openai\.com/p/session[^)]+)\)', content_text)
                                    if bracket_links:
                                        portal_link = bracket_links[0]  # 取第一个找到的链接
                                        result_line = f"{acc_pass}----link----{portal_link}"
                                        results.append(result_line)
                                        print(f"{Colors.GREEN}  成功: {acc_pass} - 门户链接: {portal_link}{Colors.END}")
                                    else:
                                        result_line = f"{acc_pass}----失败----未找到括号链接"
                                        results.append(result_line)
                                        print(f"{Colors.YELLOW}  失败: {acc_pass} - 未找到括号链接{Colors.END}")
                                else:
                                    result_line = f"{acc_pass}----失败----未找到content div"
                                    results.append(result_line)
                                    print(f"{Colors.YELLOW}  失败: {acc_pass} - 未找到content div{Colors.END}")
                                    
                            except Exception as link_error:
                                result_line = f"{acc_pass}----失败----链接访问错误"
                                results.append(result_line)
                                print(f"{Colors.RED}  链接访问错误: {link_error} - 账户: {acc_pass}{Colors.END}")
                        else:
                            result_line = f"{acc_pass}----失败----无效的href格式"
                            results.append(result_line)
                            print(f"{Colors.YELLOW}  失败: {acc_pass} - 无效的href格式{Colors.END}")
                    else:
                        result_line = f"{acc_pass}----失败----未找到链接标签"
                        results.append(result_line)
                        print(f"{Colors.YELLOW}  失败: {acc_pass} - 未找到链接标签{Colors.END}")
                else:
                    result_line = f"{acc_pass}----失败----未找到下一个span"
                    results.append(result_line)
                    print(f"{Colors.YELLOW}  失败: {acc_pass} - 未找到下一个span{Colors.END}")
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