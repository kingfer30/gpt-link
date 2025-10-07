from datetime import datetime

def read_base_data(file_path):
    """读取成功.txt基础数据：账号----密码----邮箱密码----RT"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def read_check_result(file_path):
    """读取check_result.txt检测结果"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def parse_date(date_str):
    """解析日期字符串，返回datetime对象用于排序"""
    try:
        # 处理ISO 8601格式：2025-09-17T16:58:51+00:00
        if 'T' in date_str and '+' in date_str:
            # 移除时区信息并解析
            date_part = date_str.split('+')[0]  # 去掉时区部分
            return datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
        elif 'T' in date_str and 'Z' in date_str:
            # 处理UTC格式：2025-09-17T16:58:51Z
            date_part = date_str.replace('Z', '')
            return datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
        else:
            # 尝试解析其他常见的日期格式
            formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
        
        # 如果都无法解析，返回一个很晚的日期作为默认值
        return datetime(9999, 12, 31)
    except:
        return datetime(9999, 12, 31)


def sort_data_by_result(base_data, check_results):
    """根据检测结果对基础数据进行排序"""
    # 创建检测结果字典
    result_dict = {}
    for result in check_results:
        parts = result.split('----')
        if len(parts) >= 2:
            account = parts[0]
            if len(parts) >= 4 and parts[2] == '成功':
                # 成功的记录：账号----邮箱密码----成功----日期
                date_str = parts[3]
                result_dict[account] = {'status': 'success', 'date': parse_date(date_str)}
            elif len(parts) >= 3 and parts[1] == 'link':
                # 新格式的成功记录：账号----link----链接
                # 这种格式没有日期，使用当前日期或默认日期
                result_dict[account] = {'status': 'success', 'date': datetime(2024, 1, 1)}
            else:
                # 失败的记录
                result_dict[account] = {'status': 'failed', 'date': datetime(9999, 12, 31)}
    
    # 分离成功和失败的基础数据
    success_data = []
    failed_data = []
    
    for line in base_data:
        if not line.strip():
            continue
        account = line.split('----')[0]
        if account in result_dict:
            if result_dict[account]['status'] == 'success':
                success_data.append((line, result_dict[account]['date']))
            else:
                failed_data.append(line)
        else:
            # 没有检测结果的默认为失败
            failed_data.append(line)
    
    # 按日期升序排序成功的数据
    success_data.sort(key=lambda x: x[1])
    
    # 组合结果：成功的在前（按日期升序），插入分隔符，然后是失败的
    sorted_data = [item[0] for item in success_data]
    if failed_data:  # 只有在有失败数据时才插入分隔符
        sorted_data.append('--以下失败')
        sorted_data.extend(failed_data)
    
    return sorted_data


def write_sorted_data(file_path, sorted_data):
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in sorted_data:
            f.write(line + '\n')


def main():
    base_file = '成功.txt'  # 基础数据文件
    check_file = 'check_result.txt'  # 检测结果文件
    output_file = 'sorted_data.txt'  # 输出到新文件

    base_data = read_base_data(base_file)
    check_results = read_check_result(check_file)

    sorted_data = sort_data_by_result(base_data, check_results)

    write_sorted_data(output_file, sorted_data)
    print(f"数据已按检测结果排序并写入 {output_file}")
    print(f"排序规则：成功的按日期升序在前，失败的在后")


if __name__ == '__main__':
    main()
