import json
import re
import os

# 导入数据库-领域映射
try:
    from db_domain_mapping import get_domain_for_db_id
except ImportError:
    # 如果导入失败，定义一个简单的默认函数
    def get_domain_for_db_id(db_id):
        """如果映射模块不可用，返回默认领域"""
        return "General Visualization"
    print("警告: 无法导入 db_domain_mapping 模块，将使用默认领域。")

def extract_all_table_names(sql_query):
    """
    从 SQL 查询中提取 FROM 和 JOIN 子句后的所有表名。
    尝试处理简单的 AS 别名。返回一个唯一的表名列表。
    """
    # 使用 findall 查找 FROM 或 JOIN 后面的表名，忽略可选的 AS 别名
    # (?:FROM|JOIN) 是一个非捕获组，匹配 FROM 或 JOIN
    # \s+ 匹配一个或多个空白字符
    # ([\w.-]+) 捕获组，匹配表名（允许字母、数字、下划线、点、连字符）
    # (?:\s+AS\s+\w+)? 非捕获组，可选地匹配 " AS alias"
    tables = re.findall(r'(?:FROM|JOIN)\s+([\w.-]+)(?:\s+AS\s+\w+)?', sql_query, re.IGNORECASE)
    # 使用 dict.fromkeys 保留顺序并去重
    unique_tables = list(dict.fromkeys(tables))
    if not unique_tables:
        # 如果上面没找到，尝试一个更简单的模式，只匹配 FROM 后面的第一个词
        # 这可以处理一些没有明确 JOIN 但可能引用多表的复杂情况（尽管不完美）
        fallback_match = re.search(r'FROM\s+([\w.-]+)', sql_query, re.IGNORECASE)
        if fallback_match:
            unique_tables = [fallback_match.group(1)]
        else:
            print(f"警告: 无法从 SQL 中提取任何表名: {sql_query}")
    return unique_tables

def convert_viseval_to_ba_bench(input_json_path, output_json_path, base_data_dir):
    """
    将 VisEval JSON 数据转换为 BA-bench 格式。
    将所有涉及的数据文件路径列表存储在 additional_information['involved_data_files'] 中。

    Args:
        input_json_path (str): 输入的 VisEval JSON 文件路径 (e.g., 'VisEval/visEval_dataset/visEval.json').
        output_json_path (str): 输出的 BA-bench JSON 文件路径 (e.g., 'ba_bench_viseval.json').
        base_data_dir (str): VisEval 数据集的基础目录 (e.g., 'VisEval/visEval_dataset').
    """
    try:
        with open(input_json_path, 'r', encoding='utf-8') as f:
            viseval_data = json.load(f)
    except FileNotFoundError:
        print(f"错误: 输入文件未找到: {input_json_path}")
        return
    except json.JSONDecodeError:
        print(f"错误: 解析 JSON 文件失败: {input_json_path}")
        return

    ba_bench_data = []
    processed_count = 0
    error_count = 0

    for original_id, vis_entry in viseval_data.items():
        nl_queries = vis_entry.get('nl_queries', [])
        if not nl_queries:
            error_count += 1
            continue

        db_id = vis_entry.get('db_id')
        sql_part = vis_entry.get('vis_query', {}).get('data_part', {}).get('sql_part')
        vis_obj = vis_entry.get('vis_obj')

        if not db_id or not sql_part or not vis_obj:
            print(f"警告: ID '{original_id}' 缺少 db_id, sql_part 或 vis_obj，跳过。")
            error_count += 1
            continue

        # 提取所有涉及的表名
        all_table_names = extract_all_table_names(sql_part)
        if not all_table_names:
            error_count += 1
            print(f"警告: ID '{original_id}' 的 SQL 无法提取表名，跳过其所有查询。 SQL: {sql_part}")
            continue # Skip if no tables found

        # 确定主表名 (用第一个提取到的) 以填充 data_file 字段
        primary_table_name = all_table_names[0]
        primary_data_file_path = os.path.join(base_data_dir, 'databases', db_id, f"{primary_table_name}.csv").replace('\\', '/')

        # 构建所有涉及的数据文件路径列表
        involved_data_files = [
            os.path.join(base_data_dir, 'databases', db_id, f"{name}.csv").replace('\\', '/')
            for name in all_table_names
        ]

        # 使用映射函数获取该数据库对应的业务领域
        data_domain = get_domain_for_db_id(db_id)

        for nl_idx, nl_query in enumerate(nl_queries):
            ba_bench_sample = {
                'id': f"VisEval_{original_id}_{nl_idx}",
                'question': nl_query,
                # data_file 仍然是字符串，指向主文件
                'data_file': primary_data_file_path,
                'doc_file': "None",
                'answer': json.dumps(vis_obj), # 将 vis_obj 序列化为 JSON 字符串
                'data_domain': data_domain,  # 使用映射表中查找到的领域
                'analysis_type': "Chart problems",
                'origin_from': ['VisEval', original_id],
                'additional_information': {
                    'hardness': vis_entry.get('hardness'),
                    'chart': vis_entry.get('chart'),
                    'vis_query': vis_entry.get('vis_query'),
                    'sql_part': sql_part,
                    # 新增字段：包含所有相关数据文件的列表
                    'involved_data_files': involved_data_files,
                    'irrelevant_tables': vis_entry.get('irrelevant_tables', []),
                    'query_meta': vis_entry.get('query_meta', [])
                }
            }
            ba_bench_data.append(ba_bench_sample)
            processed_count += 1

    # 确保输出目录存在
    output_dir = os.path.dirname(output_json_path)
    if output_dir and not os.path.exists(output_dir):
         try:
             os.makedirs(output_dir)
             print(f"创建目录: {output_dir}")
         except OSError as e:
             print(f"错误: 创建目录失败 {output_dir}: {e}")
             return

    try:
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(ba_bench_data, f, indent=4, ensure_ascii=False)
        print(f"转换完成！")
        print(f"成功处理 {processed_count} 个自然语言查询。")
        if error_count > 0:
             print(f"跳过 {error_count} 个有问题或信息不完整的原始条目/查询。")
        print(f"结果已保存到: {output_json_path}")
    except IOError as e:
        print(f"错误: 无法写入输出文件 {output_json_path}: {e}")


# --- 使用示例 ---
# 获取当前脚本所在目录 (TransVis)
script_dir = os.path.dirname(os.path.abspath(__file__))
# 获取工作区根目录 (BA-bench)
workspace_dir = os.path.dirname(script_dir)

# 输入文件路径 (使用绝对路径)
input_file = os.path.join(workspace_dir, 'VisEval', 'visEval_dataset', 'visEval.json')
# VisEval 数据集的基础目录 (使用绝对路径)
viseval_base_dir = os.path.join(workspace_dir, 'VisEval', 'visEval_dataset')
# 输出目录 (此脚本所在目录)
output_dir = script_dir
# 输出文件名
output_filename = 'ba_bench_viseval.json'
# 组合输出路径 (确保跨平台兼容)
output_file = os.path.join(output_dir, output_filename).replace('\\', '/')

# 显示所有路径 (调试用)
print(f"工作区目录: {workspace_dir}")
print(f"脚本目录: {script_dir}")
print(f"输入文件: {input_file}")
print(f"数据集目录: {viseval_base_dir}")
print(f"输出文件: {output_file}")

# 执行转换
print(f"\n开始转换: {input_file} -> {output_file}")
convert_viseval_to_ba_bench(input_file, output_file, viseval_base_dir)

# # 你也可以选择处理 single 或 multiple 文件，并保存到 TransVis 目录：
# input_single = os.path.join(workspace_dir, 'VisEval', 'visEval_dataset', 'visEval_single.json')
# output_single = os.path.join(output_dir, 'ba_bench_viseval_single.json').replace('\\', '/')
# print(f"\n开始转换: {input_single} -> {output_single}")
# convert_viseval_to_ba_bench(input_single, output_single, viseval_base_dir)

# input_multiple = os.path.join(workspace_dir, 'VisEval', 'visEval_dataset', 'visEval_multiple.json')
# output_multiple = os.path.join(output_dir, 'ba_bench_viseval_multiple.json').replace('\\', '/')
# print(f"\n开始转换: {input_multiple} -> {output_multiple}")
# convert_viseval_to_ba_bench(input_multiple, output_multiple, viseval_base_dir)

print("\n所有处理结束。")