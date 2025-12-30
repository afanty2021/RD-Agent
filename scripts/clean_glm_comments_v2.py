#!/usr/bin/env python3
"""
精确清理GLM-4.6中文注释 - 版本2

使用git diff精确识别需要删除的行
"""

import subprocess
import re
from pathlib import Path


def get_added_lines_in_commit(commit: str, filepath: str) -> set:
    """获取指定commit中添加的行号"""
    try:
        result = subprocess.run(
            ["git", "show", commit, "--", filepath],
            capture_output=True,
            text=True,
            check=True
        )
        # 解析git show输出，找到添加的行
        added_lines = set()
        current_line = 0
        for line in result.stdout.split('\n'):
            if line.startswith('@@'):
                # 解析行号信息 @@ -start,count +start,count @@
                match = re.search(r'\+\s*(\d+)', line)
                if match:
                    current_line = int(match.group(1))
                continue
            if line.startswith('+') and not line.startswith('+++'):
                # 这是一个添加的行
                added_lines.add(current_line)
                current_line += 1
            elif line.startswith(' ') or line.startswith('-'):
                current_line += 1
        return added_lines
    except subprocess.CalledProcessError:
        return set()


def clean_file_by_commit(filepath: str, commits: list):
    """根据提交历史清理文件"""
    print(f"清理 {filepath}...")

    path = Path(filepath)
    if not path.exists():
        print(f"  ⚠️  文件不存在")
        return

    # 获取所有添加的行
    all_added_lines = set()
    for commit in commits:
        added = get_added_lines_in_commit(commit, filepath)
        all_added_lines.update(added)

    if not all_added_lines:
        print(f"  ℹ️  没有找到需要清理的行")
        return

    # 读取文件
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 删除在GLM-4.6提交中添加的包含中文的行
    new_lines = []
    removed = 0

    for i, line in enumerate(lines, 1):
        if i in all_added_lines:
            # 检查是否包含中文
            if re.search(r'[\u4e00-\u9fff]', line):
                # 删除这一行
                removed += 1
                continue
        # 保留其他行
        new_lines.append(line)

    if removed == 0:
        print(f"  ℹ️  没有需要清理的中文注释")
        return

    # 写回文件
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print(f"  ✓ 删除 {removed} 行中文注释")


def main():
    """主函数"""
    print("=" * 60)
    print("精确清理GLM-4.6中文注释（版本2）")
    print("=" * 60)

    # GLM-4.6添加中文注释的提交
    glm_commits = [
        "a4233868",  # 添加核心模块详尽中文注释
        "ed38d39c",  # 完善核心模块详尽中文注释系统
    ]

    files = [
        "rdagent/app/cli.py",
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

    total_removed = 0
    for filepath in files:
        try:
            clean_file_by_commit(filepath, glm_commits)
        except Exception as e:
            print(f"  ✗ 清理失败: {e}")

    print("\n" + "=" * 60)
    print("清理完成！")
    print("=" * 60)

    # 显示git状态
    print("\nGit状态:")
    subprocess.run(["git", "status", "--short"])


if __name__ == "__main__":
    main()
