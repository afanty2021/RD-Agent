#!/usr/bin/env python3
"""
清理GLM-4.6添加的中文注释脚本

策略：
1. 恢复原始英文模块docstring
2. 删除代码中间的独立多行字符串注释
3. 简化过度冗长的函数docstring
4. 保留英文注释和标准格式的docstring
"""

import subprocess
import re
from pathlib import Path


def get_commit_content(commit: str, filepath: str) -> str:
    """获取指定提交中文件的内容"""
    try:
        result = subprocess.run(
            ["git", "show", f"{commit}:{filepath}"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        return ""


def clean_cli_py():
    """清理cli.py文件"""
    filepath = "rdagent/app/cli.py"
    original_commit = "a4233868^"  # 添加注释前的提交

    print(f"清理 {filepath}...")

    # 获取原始版本
    original_content = get_commit_content(original_commit, filepath)
    if not original_content:
        print(f"  ⚠️  无法获取原始版本")
        return

    # 读取当前版本
    with open(filepath, 'r', encoding='utf-8') as f:
        current_content = f.read()

    # 策略：直接恢复到原始版本，然后手动添加必要的后续修改
    # 检查是否有重要的后续修改需要保留

    # 暂时使用简单策略：直接恢复原始模块docstring
    original_lines = original_content.split('\n')
    current_lines = current_content.split('\n')

    # 恢复文件头部的模块docstring
    new_lines = []
    i = 0

    # 跳过当前的中文模块docstring（第1-18行）
    while i < len(current_lines):
        if i == 0 and current_lines[i].startswith('# -*- coding: utf-8 -*-'):
            new_lines.append(current_lines[i])  # 保留coding声明
            i += 1
            continue
        if i < 20 and '"""' in current_lines[i]:
            # 跳过中文docstring，直到找到结束的"""
            if current_lines[i].count('"""') == 2:
                i += 1
                continue
            j = i + 1
            while j < len(current_lines) and '"""' not in current_lines[j]:
                j += 1
            i = j + 1
            continue
        break

    # 插入原始的英文docstring
    new_lines.append('')
    new_lines.append('"""')
    new_lines.append('CLI entrance for all rdagent application.')
    new_lines.append('')
    new_lines.append('This will')
    new_lines.append('- make rdagent a nice entry and')
    new_lines.append('- autoamtically load dotenv')
    new_lines.append('"""')
    new_lines.append('')

    # 添加import语句（保留原有）
    new_lines.append('import sys')
    new_lines.append('')
    new_lines.append('from dotenv import load_dotenv')
    new_lines.append('')
    new_lines.append('load_dotenv(".env")')
    new_lines.append('# 1) Make sure it is at the beginning of the script so that it will load dotenv before initializing BaseSettings.')
    new_lines.append('# 2) The ".env" argument is necessary to make sure it loads `.env` from the current directory.')
    new_lines.append('')

    # 添加其他imports（跳过注释块）
    in_import_section = False
    for line in current_lines:
        if line.startswith('import subprocess'):
            in_import_section = True
        if in_import_section:
            new_lines.append(line)
        elif line.startswith('from rdagent.app.data_science'):
            # 到达应用模块导入，添加之前的内容
            new_lines.append('')
            new_lines.append(line)
            in_import_section = True
        elif line.strip() == '' and in_import_section:
            new_lines.append(line)

    # 添加app初始化
    new_lines.append('')
    new_lines.append('app = typer.Typer()')
    new_lines.append('')

    # 添加函数定义（恢复原始的简洁docstring）
    # 找到ui函数
    ui_func_start = False
    for i, line in enumerate(current_lines):
        if line.startswith('def ui('):
            ui_func_start = True
            new_lines.append(line)
            # 找到docstring开始
            if i + 1 < len(current_lines) and '"""' in current_lines[i + 1]:
                # 跳过冗长的docstring
                j = i + 2
                while j < len(current_lines) and '"""' not in current_lines[j]:
                    j += 1
                # 插入简洁的docstring
                new_lines.append('    """')
                new_lines.append('    start web app to show the log traces.')
                new_lines.append('    """')
                # 添加函数体
                for k in range(j + 1, len(current_lines)):
                    # 简化注释
                    clean_line = current_lines[k]
                    # 删除中文注释
                    if re.search(r'[\u4e00-\u9fff]', clean_line):
                        if clean_line.strip().startswith('#'):
                            continue  # 跳过中文注释行
                    new_lines.append(clean_line)
                break
        elif not ui_func_start and line.startswith('def ') and not line.startswith('def ui'):
            # ui函数之前的其他函数（如server_ui）
            new_lines.append(line)

    # 写回文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))

    print(f"  ✓ {filepath} 已清理")


def clean_file_simple(filepath: str):
    """
    简单清理策略：删除所有中文注释，保留英文

    适用于：除了cli.py之外的其他文件
    """
    print(f"清理 {filepath}...")

    path = Path(filepath)
    if not path.exists():
        print(f"  ⚠️  文件不存在")
        return

    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    removed = 0
    in_docstring = False
    docstring_has_chinese = False

    for i, line in enumerate(lines):
        # 检查是否在docstring中
        if '"""' in line:
            if line.count('"""') == 2:
                # 单行docstring
                if re.search(r'[\u4e00-\u9fff]', line):
                    # 跳过包含中文的单行docstring
                    removed += 1
                    continue
                else:
                    new_lines.append(line)
                    continue
            else:
                if not in_docstring:
                    in_docstring = True
                    docstring_has_chinese = re.search(r'[\u4e00-\u9fff]', line)
                    new_lines.append(line)
                else:
                    in_docstring = False
                    if docstring_has_chinese and i > 0:
                        # 这是一个中文docstring，删除它
                        # 回溯删除整个docstring
                        while new_lines and '"""' not in new_lines[-1]:
                            new_lines.pop()
                            removed += 1
                        if new_lines:
                            new_lines.pop()  # 删除开始的"""
                            removed += 1
                    docstring_has_chinese = False
                continue

        # 在docstring中
        if in_docstring:
            if re.search(r'[\u4e00-\u9fff]', line):
                docstring_has_chinese = True
            new_lines.append(line)
            continue

        # 检查行内注释
        if '#' in line:
            # 分离代码和注释
            parts = line.split('#', 1)
            if len(parts) == 2:
                code_part = parts[0]
                comment_part = parts[1]
                # 如果注释包含中文，删除注释
                if re.search(r'[\u4e00-\u9fff]', comment_part):
                    new_lines.append(code_part + '\n')
                    if not code_part.strip():
                        removed += 1
                    continue

        # 删除纯中文注释行
        if line.strip().startswith('#') and re.search(r'[\u4e00-\u9fff]', line):
            removed += 1
            continue

        new_lines.append(line)

    # 写回文件
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"  ✓ {filepath}: 删除 {removed} 行")


def main():
    """主函数"""
    print("=" * 60)
    print("清理GLM-4.6添加的中文注释")
    print("=" * 60)

    # 清理cli.py（特殊处理）
    clean_cli_py()

    # 其他文件使用简单清理
    files = [
        "rdagent/components/coder/CoSTEER/evolving_strategy.py",
        "rdagent/core/conf.py",
        "rdagent/core/evaluation.py",
        "rdagent/core/evolving_framework.py",
        "rdagent/oai/llm_utils.py",
        "rdagent/app/data_science/loop.py",
        "rdagent/components/agent/base.py",
        "rdagent/components/coder/CoSTEER/config.py",
        "rdagent/components/coder/CoSTEER/evaluators.py",
        "rdagent/components/coder/CoSTEER/knowledge_management.py",
        "rdagent/oai/backend/litellm.py",
        "rdagent/scenarios/data_science/proposal/exp_gen/proposal.py",
    ]

    for filepath in files:
        clean_file_simple(filepath)

    print("\n" + "=" * 60)
    print("清理完成！")
    print("=" * 60)

    # 显示git状态
    print("\nGit状态:")
    subprocess.run(["git", "status", "--short"])


if __name__ == "__main__":
    main()
