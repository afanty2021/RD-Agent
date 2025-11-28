# -*- coding: utf-8 -*-
"""
RD-Agent CLI入口模块

本模块是RD-Agent系统的统一命令行入口，提供：
1. 所有RD-Agent应用的CLI接口
2. 自动环境变量加载
3. 现代化的命令行交互体验
4. Web UI启动功能

支持的主要应用场景：
- 数据科学实验自动化
- Kaggle竞赛参与
- 量化交易策略开发
- 模型微调和优化
- 通用模型提取与实现

作者: RD-Agent Team
"""

import sys

from dotenv import load_dotenv

# ==================== 环境初始化 ====================
# 加载.env环境变量文件
load_dotenv(".env")
"""
环境变量加载说明：
1) 确保在脚本开头执行，以便在初始化BaseSettings之前加载dotenv
2) ".env"参数确保从当前目录加载.env文件
3) 支持API密钥、配置参数等敏感信息的统一管理
"""

import subprocess
from importlib.resources import path as rpath

import typer

# ==================== 应用模块导入 ====================
from rdagent.app.data_science.loop import main as data_science
from rdagent.app.general_model.general_model import (
    extract_models_and_implement as general_model,
)
from rdagent.app.qlib_rd_loop.factor import main as fin_factor
from rdagent.app.qlib_rd_loop.factor_from_report import main as fin_factor_report
from rdagent.app.qlib_rd_loop.model import main as fin_model
from rdagent.app.qlib_rd_loop.quant import main as fin_quant
from rdagent.app.utils.health_check import health_check
from rdagent.app.utils.info import collect_info
from rdagent.log.mle_summary import grade_summary as grade_summary

# ==================== CLI应用初始化 ====================
app = typer.Typer()
"""
创建Typer应用实例

Typer是一个现代化的Python CLI框架，提供：
- 自动帮助文档生成
- 类型安全的参数验证
- 丰富的命令行交互功能
- 优美的错误消息显示
"""


def ui(port=19899, log_dir="", debug: bool = False, data_science: bool = False):
    """
    启动Web UI应用

    启动基于Streamlit的Web界面，用于展示日志追踪和实验结果。
    支持普通模式和数据科学专用模式。

    Args:
        port: Web服务器端口号，默认19899
        log_dir: 日志目录路径（可选）
        debug: 是否启用调试模式
        data_science: 是否启动数据科学专用界面

    Web界面功能：
    - 实时实验进度监控
    - 日志和结果可视化
    - 性能指标展示
    - 交互式图表分析

    Example:
        >>> rdagent ui                           # 启动默认Web界面
        >>> rdagent ui --port 8080               # 指定端口启动
        >>> rdagent ui --data-science            # 启动数据科学专用界面
        >>> rdagent ui --debug --log_dir ./logs  # 调试模式启动
    """
    if data_science:
        # 数据科学专用界面
        with rpath("rdagent.log.ui", "dsapp.py") as app_path:
            cmds = ["streamlit", "run", app_path, f"--server.port={port}"]
            subprocess.run(cmds)
        return

    # 通用Web界面
    with rpath("rdagent.log.ui", "app.py") as app_path:
        cmds = ["streamlit", "run", app_path, f"--server.port={port}"]

        # 添加可选参数
        if log_dir or debug:
            cmds.append("--")
        if log_dir:
            cmds.append(f"--log_dir={log_dir}")
        if debug:
            cmds.append("--debug")

        subprocess.run(cmds)


def server_ui(port=19899):
    """
    启动服务器端Web UI

    启动用于实时显示日志追踪的服务器端Web应用。
    提供更强大的实时数据处理和展示能力。

    Args:
        port: 服务器端口号，默认19899

    Features:
    - 实时数据流处理
    - WebSocket长连接支持
    - 高并发数据展示
    - 服务器端渲染优化

    Example:
        >>> rdagent server_ui          # 启动服务器端UI
        >>> rdagent server_ui --port 9000  # 指定端口启动
    """
    subprocess.run(["python", "rdagent/log/server/app.py", f"--port={port}"])


def ds_user_interact(port=19900):
    """
    启动数据科学用户交互界面

    为数据科学任务提供专门的用户交互界面，
    支持实验配置、结果分析和参数调优。

    Args:
        port: 交互界面端口号，默认19900

    功能特性：
    - 实验参数配置界面
    - 结果对比和分析工具
    - 交互式数据探索
    - 模型性能评估面板

    Example:
        >>> rdagent ds_user_interact            # 启动交互界面
        >>> rdagent ds_user_interact --port 8080  # 指定端口启动
    """
    commands = ["streamlit", "run", "rdagent/log/ui/ds_user_interact.py", f"--server.port={port}"]
    subprocess.run(commands)


app.command(name="fin_factor")(fin_factor)
app.command(name="fin_model")(fin_model)
app.command(name="fin_quant")(fin_quant)
app.command(name="fin_factor_report")(fin_factor_report)
app.command(name="general_model")(general_model)
app.command(name="data_science")(data_science)
app.command(name="grade_summary")(grade_summary)
app.command(name="ui")(ui)
app.command(name="server_ui")(server_ui)
app.command(name="health_check")(health_check)
app.command(name="collect_info")(collect_info)
app.command(name="ds_user_interact")(ds_user_interact)


if __name__ == "__main__":
    app()
