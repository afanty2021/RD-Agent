# -*- coding: utf-8 -*-
"""
RD-Agent 进化框架核心模块

本模块定义了RD-Agent系统的进化式开发框架，提供：
1. 可进化对象的基础抽象
2. 进化策略的接口定义
3. RAG（检索增强生成）策略框架
4. 知识管理和查询机制

这是RD-Agent实现自主进化学习的核心基础设施。

作者: RD-Agent Team
"""

from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from rdagent.core.evaluation import EvaluableObj
from rdagent.core.knowledge_base import KnowledgeBase

if TYPE_CHECKING:
    from rdagent.core.evaluation import Feedback
    from rdagent.core.scenario import Scenario


class Knowledge:
    """
    知识基类

    用于表示在进化过程中积累的各种类型的知识。
    可以是代码片段、解决方案、经验总结等。
    """
    pass


class QueriedKnowledge:
    """
    查询知识基类

    用于表示从知识库中检索到的相关知识。
    通常包含与当前进化步骤相关的历史经验和解决方案。
    """
    pass


class EvolvingKnowledgeBase(KnowledgeBase):
    """
    进化知识库抽象基类

    继承自基础知识库，专门用于支持进化过程中的知识管理。
    提供知识查询、存储和检索功能。
    """

    @abstractmethod
    def query(
        self,
    ) -> QueriedKnowledge | None:
        """
        从知识库中查询相关知识

        Returns:
            QueriedKnowledge | None: 查询到的相关知识，如果没有则返回None
        """
        raise NotImplementedError


class EvolvableSubjects(EvaluableObj):
    """
    可进化对象抽象基类

    定义了可以被进化的目标对象的基本接口。
    任何需要通过进化策略改进的对象都应该继承此类。
    """

    def clone(self) -> EvolvableSubjects:
        """
        创建当前对象的深拷贝

        Returns:
            EvolvableSubjects: 当前对象的深拷贝实例
        """
        return copy.deepcopy(self)


# 类型变量定义，用于泛型约束
ASpecificEvolvableSubjects = TypeVar("ASpecificEvolvableSubjects", bound=EvolvableSubjects)


@dataclass
class EvoStep(Generic[ASpecificEvolvableSubjects]):
    """
    进化步骤数据类

    记录进化过程中的一个完整步骤，包含：
    - 当前的可进化对象状态
    - 查询到的相关知识
    - 评估反馈信息

    这个类构成了进化轨迹的基本单元。
    """

    evolvable_subjects: ASpecificEvolvableSubjects
    """当前步骤的可进化对象实例"""

    queried_knowledge: QueriedKnowledge | None = None
    """从知识库中查询到的相关知识"""

    feedback: Feedback | None = None
    """评估后得到的反馈信息"""


class EvolvingStrategy(ABC, Generic[ASpecificEvolvableSubjects]):
    """
    进化策略抽象基类

    定义了进化算法的核心接口，所有具体的进化策略都需要继承此类。
    负责根据历史反馈和查询知识来改进可进化对象。
    """

    def __init__(self, scen: Scenario) -> None:
        """
        初始化进化策略

        Args:
            scen: 场景实例，提供进化所需的上下文信息
        """
        self.scen = scen

    @abstractmethod
    def evolve(
        self,
        *evo: ASpecificEvolvableSubjects,
        evolving_trace: list[EvoStep[ASpecificEvolvableSubjects]] | None = None,
        queried_knowledge: QueriedKnowledge | None = None,
        **kwargs: Any,
    ) -> ASpecificEvolvableSubjects:
        """
        执行进化操作

        Args:
            *evo: 需要进化的可进化对象
            evolving_trace: 历史进化轨迹，按时间顺序排列的(previous_subjects, feedback)列表
            queried_knowledge: 查询到的相关知识
            **kwargs: 其他参数

        Returns:
            ASpecificEvolvableSubjects: 进化后的新对象

        Note:
            进化轨迹的重要性：
            - evolving_trace: 包含历史反馈，对避免重复错误、学习成功经验至关重要
            - queried_knowledge: 提供相关的先验知识和解决方案
        """


class RAGStrategy(ABC, Generic[ASpecificEvolvableSubjects]):
    """
    检索增强生成策略抽象基类

    实现RAG（Retrieval Augmented Generation）机制，
    结合知识检索和生成来改进进化策略的效果。
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        初始化RAG策略

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        self.knowledgebase: EvolvingKnowledgeBase = self.load_or_init_knowledge_base(*args, **kwargs)

    @abstractmethod
    def load_or_init_knowledge_base(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> EvolvingKnowledgeBase:
        """
        加载或初始化知识库

        Args:
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            EvolvingKnowledgeBase: 初始化的知识库实例
        """
        pass

    @abstractmethod
    def query(
        self,
        evo: ASpecificEvolvableSubjects,
        evolving_trace: list[EvoStep],
        **kwargs: Any,
    ) -> QueriedKnowledge | None:
        """
        根据当前状态和历史轨迹查询相关知识

        Args:
            evo: 当前的可进化对象
            evolving_trace: 历史进化轨迹
            **kwargs: 其他参数

        Returns:
            QueriedKnowledge | None: 查询到的相关知识
        """
        pass

    @abstractmethod
    def generate_knowledge(
        self,
        evolving_trace: list[EvoStep[ASpecificEvolvableSubjects]],
        *,
        return_knowledge: bool = False,
        **kwargs: Any,
    ) -> Knowledge | None:
        """
        基于进化轨迹生成新知识

        Args:
            evolving_trace: 进化轨迹
            return_knowledge: 是否返回生成的知识
            **kwargs: 其他参数

        Returns:
            Knowledge | None: 生成的新知识

        Note:
            - 鼓励在生成新知识之前先查询相关知识
            - RAGStrategy应该自行管理新知识的维护和存储
        """
        pass

    @abstractmethod
    def dump_knowledge_base(self, *args: Any, **kwargs: Any) -> None:
        """
        持久化知识库

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        pass

    @abstractmethod
    def load_dumped_knowledge_base(self, *args: Any, **kwargs: Any) -> None:
        """
        加载持久化的知识库

        主要用于并行编码场景，当多个编码器共享同一个知识库时，
        在更新知识库之前需要先加载其他编码器的最新知识。

        Args:
            *args: 位置参数
            **kwargs: 关键字参数
        """
        pass
