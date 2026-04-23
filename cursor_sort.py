from datetime import datetime


def read_check_result(file_path):
    """读取 check_result.txt，格式：账号----邮箱密码----密码----token----状态----日期"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def parse_date(date_str):
    """解析日期字符串，返回 datetime 对象用于排序"""
    try:
        date_str = date_str.strip()
        if 'T' in date_str:
            date_part = date_str.split('+')[0].replace('Z', '').split('.')[0]
            return datetime.strptime(date_part, '%Y-%m-%dT%H:%M:%S')
        formats = ['%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y', '%d/%m/%Y']
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    except Exception:
        pass
    return datetime(9999, 12, 31)


def sort_data(records):
    """
    按状态和日期排序。
    格式：账号----邮箱密码----密码----token----状态----日期
    成功（状态=='成功'）按日期升序排前，其余按日期升序排后。
    """
    success_records = []
    failed_records = []

    for line in records:
        parts = line.split('----')
        if len(parts) >= 6:
            status = parts[4]
            date_str = parts[5]
        elif len(parts) == 5:
            status = parts[4]
            date_str = ''
        else:
            status = ''
            date_str = ''

        dt = parse_date(date_str)
        if status == '成功':
            success_records.append((line, dt))
        else:
            failed_records.append((line, dt))

    success_records.sort(key=lambda x: x[1])
    failed_records.sort(key=lambda x: x[1])

    result = [item[0] for item in success_records]
    if failed_records:
        result.append('--以下失败')
        result.extend(item[0] for item in failed_records)
    return result


def write_sorted_data(file_path, sorted_data):
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in sorted_data:
            f.write(line + '\n')


def main():
    check_file = 'check_result.txt'
    output_file = 'sorted_data.txt'

    records = read_check_result(check_file)
    sorted_data = sort_data(records)
    write_sorted_data(output_file, sorted_data)

    success_count = sum(1 for line in sorted_data if '----成功----' in line)
    print(f"数据已按检测结果排序并写入 {output_file}")
    print(f"成功：{success_count} 条，总计：{len(records)} 条")
    print(f"排序规则：成功按日期升序在前，其余按日期升序在后")


if __name__ == '__main__':
    main()
