import os

script_dir = os.path.dirname(os.path.abspath(__file__))
new_rt_file = os.path.join(script_dir, "newRt.txt")
old_rt_file = os.path.join(script_dir, "oldRt.txt")
output_file = os.path.join(script_dir, "outputRt.txt")

# 从 newRt.txt 构建 email -> rt 的映射
new_rt_map = {}
with open(new_rt_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("----")
        if len(parts) >= 2:
            email = parts[0]
            rt = parts[-1]  # 最后一段是 rt_xxx
            new_rt_map[email] = rt

# 处理 oldRt.txt，替换 rt 字段
results = []
matched = 0
not_matched = []

with open(old_rt_file, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split("----")
        email = parts[0]
        if email in new_rt_map:
            # 保留前三段，替换最后一段（rt_xxx）
            new_line = "----".join(parts[:-1]) + "----" + new_rt_map[email]
            results.append(new_line)
            matched += 1
        else:
            results.append(line)  # 未匹配则保持原样
            not_matched.append(email)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(results) + "\n")

print(f"处理完成！共 {len(results)} 条，成功替换 {matched} 条")
if not_matched:
    print(f"未匹配（保持原样）{len(not_matched)} 条：")
    for e in not_matched:
        print(f"  {e}")
print(f"结果已保存到：{output_file}")
