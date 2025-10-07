def read_order(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def read_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines()]


def sort_data(order, data):
    # 创建一个字典以便快速查找每个项的索引
    order_dict = {item.split('----')[0]: item for item in order}

    # 根据 order.txt 的顺序对 data.txt 中的行进行排序
    sorted_data = [order_dict[item.split('----')[0]] for item in data if item.split('----')[0] in order_dict]

    return sorted_data


def write_sorted_data(file_path, sorted_data):
    with open(file_path, 'w', encoding='utf-8') as f:
        for line in sorted_data:
            f.write(line + '\n')


def main():
    order_file = '111.txt'
    data_file = '提链结果.txt'
    output_file = 'sorted_data.txt'

    order = read_order(order_file)
    data = read_data(data_file)

    sorted_data = sort_data(order, data)

    write_sorted_data(output_file, sorted_data)
    print(f"Sorted data has been written to {output_file}")


if __name__ == '__main__':
    main()
