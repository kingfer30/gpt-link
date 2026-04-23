# 根据 20.txt 中的 token 对 600.txt 数据排序
# 600.txt 格式: 用户名----密码----邮箱密码----token
# 20.txt  格式: token----其他（已按余额从高到低排列）

input_600 = "0313-600.txt"
input_20  = "20.txt"
output    = "sorted_0313.txt"

# 读取 20.txt 中的 token，保留顺序
with open(input_20, "r", encoding="utf-8") as f:
    priority_tokens_ordered = []
    for line in f:
        line = line.strip()
        if not line:
            continue
        token = line.split("----")[0].strip()
        priority_tokens_ordered.append(token)

priority_token_set = set(priority_tokens_ordered)
print(f"20.txt 中共读取到 {len(priority_tokens_ordered)} 个 token")

# 读取 600.txt，建立 token -> 行 的映射，并收集未匹配行
token_to_line = {}
unmatched = []

with open(input_600, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("----")
        # token 是第4个字段（index 3）
        if len(parts) >= 4:
            token = parts[3].strip()
            if token in priority_token_set:
                token_to_line[token] = line
            else:
                unmatched.append(line)
        else:
            unmatched.append(line)

# 按 20.txt 的顺序输出匹配行
matched = []
for token in priority_tokens_ordered:
    if token in token_to_line:
        matched.append(token_to_line[token])

print(f"匹配到的行数: {len(matched)}")
print(f"未匹配的行数: {len(unmatched)}")

# 写出结果：匹配的按 20.txt 顺序在前，未匹配的在后
with open(output, "w", encoding="utf-8") as f:
    for line in matched:
        f.write(line + "\n")
    for line in unmatched:
        f.write(line + "\n")

print(f"排序完成，结果已写入 {output}")
