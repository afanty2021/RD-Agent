# -*- coding: utf-8 -*-
"""
RD-Agent 核心配置模块

本模块定义了RD-Agent系统的配置管理基础设施，提供：
1. 扩展的基础配置类，支持继承式环境变量配置
2. 全局RD-Agent设置配置
3. 工作空间、多进程、缓存等核心配置项

作者: RD-Agent Team
"""

from __future__ import annotations

from pathlib import Path
from typing import cast

from pydantic_settings import (
    BaseSettings,
    EnvSettingsSource,
    PydanticBaseSettingsSource,
)


class ExtendedBaseSettings(BaseSettings):
    """
    扩展的基础设置类

    继承自Pydantic的BaseSettings，增加了对继承式环境变量配置的支持。
    允许子类自动继承父类的环境变量配置源，实现配置的层次化管理。
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """
        自定义配置源优先级和继承关系

        Args:
            settings_cls: 设置类类型
            init_settings: 初始化设置源
            env_settings: 环境变量设置源
            dotenv_settings: .env文件设置源
            file_secret_settings: 文件密钥设置源

        Returns:
            按优先级排序的配置源元组
        """
        # 1) 遍历基类继承链，收集所有父类
        def base_iter(settings_cls: type[ExtendedBaseSettings]) -> list[type[ExtendedBaseSettings]]:
            """
            递归收集所有继承自ExtendedBaseSettings的父类

            Args:
                settings_cls: 起始设置类

            Returns:
                父类列表，按继承顺序排列
            """
            bases = []
            for cl in settings_cls.__bases__:
                if issubclass(cl, ExtendedBaseSettings) and cl is not ExtendedBaseSettings:
                    bases.append(cl)
                    bases.extend(base_iter(cl))
            return bases

        # 2) 为所有父类构建环境变量配置源，实现配置继承
        parent_env_settings = [
            EnvSettingsSource(
                base_cls,
                case_sensitive=base_cls.model_config.get("case_sensitive"),
                env_prefix=base_cls.model_config.get("env_prefix"),
                env_nested_delimiter=base_cls.model_config.get("env_nested_delimiter"),
            )
            for base_cls in base_iter(cast("type[ExtendedBaseSettings]", settings_cls))
        ]
        # 返回配置源优先级：初始化 > 当前环境变量 > 父类环境变量 > .env文件 > 密钥文件
        return init_settings, env_settings, *parent_env_settings, dotenv_settings, file_secret_settings


class RDAgentSettings(ExtendedBaseSettings):
    """
    RD-Agent全局设置配置类

    定义了RD-Agent系统的所有核心配置项，包括：
    - Azure文档智能服务配置
    - 因子提取相关配置
    - 工作空间管理配置
    - 多进程处理配置
    - 缓存系统配置
    - 并行循环配置等
    """

    # ==================== Azure文档智能配置 ====================
    azure_document_intelligence_key: str = ""
    """Azure文档智能服务API密钥"""
    azure_document_intelligence_endpoint: str = ""
    """Azure文档智能服务端点URL"""

    # ==================== 因子提取配置 ====================
    max_input_duplicate_factor_group: int = 300
    """输入重复因子组的最大数量限制"""
    max_output_duplicate_factor_group: int = 20
    """输出重复因子组的最大数量限制"""
    max_kmeans_group_number: int = 40
    """K-means聚类的最大簇数量"""

    # ==================== 工作空间配置 ====================
    workspace_path: Path = Path.cwd() / "git_ignore_folder" / "RD-Agent_workspace"
    """RD-Agent工作空间根目录路径"""
    workspace_ckp_size_limit: int = 0
    """工作空间检查点文件大小限制（MB）。0或负值表示无限制"""
    workspace_ckp_white_list_names: list[str] | None = None
    """工作空间检查点白名单文件名列表。None表示包含所有文件"""

    """
    工作空间检查点说明：
    检查点是一个zip压缩文件，包含工作空间的完整状态。
    当size_limit <= 0时，对检查点文件大小不做限制。
    """

    # ==================== 多进程配置 ====================
    multi_proc_n: int = 1
    """多进程处理的进程数量。1表示单进程模式"""

    # ==================== Pickle缓存配置 ====================
    cache_with_pickle: bool = True
    """是否启用pickle缓存功能"""
    pickle_cache_folder_path_str: str = str(
        Path.cwd() / "pickle_cache/",
    )
    """pickle缓存文件存储目录路径"""
    use_file_lock: bool = True
    """是否使用文件锁防止相同参数函数的并发执行"""

    """
    文件锁机制说明：
    当多个进程/线程同时调用相同参数的函数时，
    文件锁可以确保函数只被执行一次，其他调用等待结果。
    """

    # ==================== 杂项配置 ====================
    stdout_context_len: int = 400
    """上下文标准输出的长度限制（字符数）"""
    stdout_line_len: int = 10000
    """单行标准输出的长度限制（字符数）"""

    enable_mlflow: bool = False
    """是否启用MLflow实验跟踪功能"""

    initial_fator_library_size: int = 20
    """初始因子库的大小（因子数量）"""

    # ==================== 并行循环配置 ====================
    step_semaphore: int | dict[str, int] = 1
    """
    步骤信号量配置，控制并发执行的循环数量

    可以是：
    - 整数：全局统一的信号量限制
    - 字典：按步骤分别设置，如 {"coding": 3, "running": 2}

    示例：
    - 1: 串行执行，无并发
    - 3: 最多3个循环并发执行
    - {"coding": 2, "running": 4}: 编码阶段最多2个并发，运行阶段最多4个并发
    """

    def get_max_parallel(self) -> int:
        """
        获取最大并发循环数量

        Returns:
            int: 基于信号量配置的最大并发数
        """
        if isinstance(self.step_semaphore, int):
            return self.step_semaphore
        return max(self.step_semaphore.values())

    # ==================== 调试配置 ====================
    # 注意：以下配置仅用于调试目的，不应在主逻辑中使用
    subproc_step: bool = False
    """是否强制使用子进程执行每个步骤（调试用）"""

    def is_force_subproc(self) -> bool:
        """
        判断是否需要强制使用子进程执行

        Returns:
            bool: 当subproc_step为True或最大并发数>1时返回True
        """
        return self.subproc_step or self.get_max_parallel() > 1

    # ==================== 模板配置 ====================
    app_tpl: str | None = None
    """
    应用模板路径，用于覆盖默认模板

    示例：
    - "app/finetune/tpl": 使用微调应用的模板
    - None: 使用默认模板
    """


# 创建全局RD-Agent设置实例
RD_AGENT_SETTINGS = RDAgentSettings()
