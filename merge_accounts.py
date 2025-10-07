def merge_account_data():
    accounts_data = {}

    # 读取111.txt文件 (acc----mailpass----gptpass----refresh_token)
    try:
        with open('111.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '----' in line:
                    # 移除行号前缀，只保留数据部分
                    if '→' in line:
                        line = line.split('→', 1)[1]

                    parts = line.split('----')
                    if len(parts) >= 4:
                        acc = parts[0]
                        mailpass = parts[1]
                        gptpass = parts[2]
                        refresh_token = parts[3]
                        accounts_data[acc] = {
                            'mailpass': mailpass,
                            'gptpass': gptpass,
                            'refresh_token': refresh_token,
                            'link': None
                        }
    except FileNotFoundError:
        print("111.txt文件未找到")
        return

    # 读取提链结果.txt文件 (acc----link)
    try:
        with open('提链结果.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and '----' in line:
                    # 移除行号前缀，只保留数据部分
                    if '→' in line:
                        line = line.split('→', 1)[1]

                    parts = line.split('----')
                    if len(parts) >= 2:
                        acc = parts[0]
                        link = parts[1]
                        if acc in accounts_data:
                            accounts_data[acc]['link'] = link
    except FileNotFoundError:
        print("提链结果.txt文件未找到")
        return

    # 写入result.txt文件 (acc----mailpass----gptpass----refresh_token----link)
    with open('result.txt', 'w', encoding='utf-8') as f:
        for acc, data in accounts_data.items():
            link = data['link'] if data['link'] else ''
            result_line = f"{acc}----{data['mailpass']}----{data['gptpass']}----{data['refresh_token']}----{link}\n"
            f.write(result_line)

    print(f"合并完成！共处理{len(accounts_data)}个账户")
    print("结果已保存到result.txt")

if __name__ == "__main__":
    merge_account_data()