# -*- coding: utf-8 -*-
"""
CoSTEER 知识管理模块

本模块实现了CoSTEER框架的知识管理系统，提供：
1. 知识的存储、检索和复用机制
2. RAG（检索增强生成）策略实现
3. 版本兼容的知识库管理
4. 基于embedding的相似性检索
5. 知识图谱组织和管理

这是CoSTEER框架实现智能学习和经验复用的核心组件。

作者: RD-Agent Team
"""

from __future__ import annotations

import copy
import json
import pickle
import random
import re
from itertools import combinations
from pathlib import Path
from typing import List, Union

from rdagent.components.coder.CoSTEER.config import CoSTEERSettings
from rdagent.components.coder.CoSTEER.evaluators import CoSTEERSingleFeedback
from rdagent.components.knowledge_management.graph import (
    UndirectedGraph,
    UndirectedNode,
)
from rdagent.core.evolving_agent import Feedback
from rdagent.core.evolving_framework import (
    EvolvableSubjects,
    EvolvingKnowledgeBase,
    EvoStep,
    Knowledge,
    QueriedKnowledge,
    RAGStrategy,
)
from rdagent.core.experiment import FBWorkspace, Task
from rdagent.log import rdagent_logger as logger
from rdagent.oai.llm_utils import (
    APIBackend,
    calculate_embedding_distance_between_str_list,
)
from rdagent.utils.agent.tpl import T


class CoSTEERKnowledge(Knowledge):
    """
    CoSTEER知识单元类

    封装了一个完整的知识条目，包含：
    - 目标任务描述
    - 具体实现代码
    - 评估反馈信息

    这个类构成了知识库的基本存储单元。
    """

    def __init__(
        self,
        target_task: Task,
        implementation: FBWorkspace,
        feedback: Feedback,
    ) -> None:
        """
        初始化CoSTEER知识单元

        Args:
            target_task: 目标任务，描述要解决的问题
            implementation: 实现方案，包含代码的工作空间
            feedback: 评估反馈，包含执行结果和质量评价
        """
        self.target_task = target_task
        self.implementation = implementation.copy()
        self.feedback = feedback

    def get_implementation_and_feedback_str(self) -> str:
        """
        获取实现和反馈的字符串表示

        Returns:
            str: 格式化的实现代码和反馈信息字符串
        """
        return f"""------------------implementation code:------------------
{self.implementation.all_codes}
------------------implementation feedback:------------------
{self.feedback!s}
"""


class CoSTEERRAGStrategy(RAGStrategy):
    """
    CoSTEER检索增强生成策略类

    实现RAG（Retrieval Augmented Generation）机制，
    通过检索历史经验来增强新任务的生成过程。

    核心功能：
    - 知识库的加载和初始化
    - 版本兼容性管理
    - 知识的持久化存储
    - 智能知识检索
    """

    def __init__(self, *args, dump_knowledge_base_path: Path = None, **kwargs):
        """
        初始化CoSTEER RAG策略

        Args:
            *args: 位置参数
            dump_knowledge_base_path: 知识库持久化路径（可选）
            **kwargs: 关键字参数
        """
        super().__init__(*args, **kwargs)
        self.dump_knowledge_base_path = dump_knowledge_base_path
        """知识库持久化存储路径"""

    def load_or_init_knowledge_base(
        self, former_knowledge_base_path: Path = None, component_init_list: list = [], evolving_version: int = 2
    ) -> EvolvingKnowledgeBase:
        """
        加载或初始化知识库

        支持从现有文件加载知识库，或创建新的知识库实例。
        提供版本兼容性检查，确保加载的知识库与当前版本兼容。

        Args:
            former_knowledge_base_path: 已有知识库文件路径（可选）
            component_init_list: 初始化组件列表（仅V2版本使用）
            evolving_version: 知识库版本（1或2，默认为2）

        Returns:
            EvolvingKnowledgeBase: 初始化的知识库实例

        Raises:
            ValueError: 当知识库版本不兼容时抛出

        Note:
            版本差异：
            - V1: 基础版本，简单的知识存储和检索
            - V2: 增强版本，支持组件化初始化和更高级的知识管理
        """
        # 尝试加载现有知识库
        if former_knowledge_base_path is not None and former_knowledge_base_path.exists():
            knowledge_base = pickle.load(open(former_knowledge_base_path, "rb"))

            # 版本兼容性检查
            if evolving_version == 1 and not isinstance(knowledge_base, CoSTEERKnowledgeBaseV1):
                raise ValueError("已有知识库与当前V1版本不兼容")
            elif evolving_version == 2 and not isinstance(
                knowledge_base,
                CoSTEERKnowledgeBaseV2,
            ):
                raise ValueError("已有知识库与当前V2版本不兼容")
        else:
            # 创建新的知识库实例
            knowledge_base = (
                CoSTEERKnowledgeBaseV2(
                    init_component_list=component_init_list,
                )
                if evolving_version == 2
                else CoSTEERKnowledgeBaseV1()
            )
        return knowledge_base