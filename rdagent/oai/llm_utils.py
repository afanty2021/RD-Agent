# -*- coding: utf-8 -*-
"""
RD-Agent LLM工具模块

本模块提供RD-Agent与大语言模型交互的核心工具函数，包括：
1. Embedding相似度计算
2. 动态API后端加载
3. 多Provider统一的接口封装

这是RD-Agent实现智能对话、代码生成和知识检索的基础设施。

作者: RD-Agent Team
"""

from __future__ import annotations

from typing import Any, Type

import numpy as np

from rdagent.core.utils import import_class
from rdagent.oai.backend.base import APIBackend as BaseAPIBackend
from rdagent.oai.llm_conf import LLM_SETTINGS
from rdagent.utils import md5_hash  # 为了兼容之前的导入


def calculate_embedding_distance_between_str_list(
    source_str_list: list[str],
    target_str_list: list[str],
) -> list[list[float]]:
    """
    计算两个字符串列表之间的embedding相似度矩阵

    使用余弦相似度计算source_str_list中每个字符串与target_str_list中每个字符串的相似度。
    常用于RAG检索、知识匹配和相似性分析等场景。

    Args:
        source_str_list: 源字符串列表
        target_str_list: 目标字符串列表

    Returns:
        list[list[float]]: 相似度矩阵
                           - matrix[i][j] 表示source_str_list[i]与target_str_list[j]的相似度
                           - 相似度范围：[0, 1]，越接近1表示越相似

    Example:
        >>> source = ["如何训练机器学习模型", "Python编程基础"]
        >>> target = ["深度学习教程", "机器学习入门", "数据科学指南"]
        >>> similarity = calculate_embedding_distance_between_str_list(source, target)
        >>> print(similarity[0][1])  # "如何训练机器学习模型"与"机器学习入门"的相似度

    Note:
        - 如果任一输入列表为空，返回空列表
        - 使用配置的embedding模型进行向量计算
        - 计算过程：文本 → embedding向量 → 归一化 → 余弦相似度
    """
    # 输入验证
    if not source_str_list or not target_str_list:
        return [[]]

    # 批量获取所有字符串的embedding向量
    try:
        embeddings = APIBackend().create_embedding(source_str_list + target_str_list)
    except Exception as e:
        # 如果embedding创建失败（例如API不可用），使用零向量作为fallback
        # 这样可以确保系统继续运行，只是RAG检索效果会降低（所有相似度都为0）
        import warnings
        warnings.warn(f"Failed to create embedding for similarity calculation: {e}. Using zero vectors as fallback.")
        total_count = len(source_str_list) + len(target_str_list)
        embeddings = [np.zeros(768) for _ in range(total_count)]

    # 分离源和目标的embedding向量
    source_embeddings = embeddings[: len(source_str_list)]
    target_embeddings = embeddings[len(source_str_list) :]

    # 转换为numpy数组以便进行矩阵运算
    source_embeddings_np = np.array(source_embeddings)
    target_embeddings_np = np.array(target_embeddings)

    # 向量归一化（L2范数）
    source_embeddings_np = source_embeddings_np / np.linalg.norm(source_embeddings_np, axis=1, keepdims=True)
    target_embeddings_np = target_embeddings_np / np.linalg.norm(target_embeddings_np, axis=1, keepdims=True)

    # 计算余弦相似度矩阵
    similarity_matrix = np.dot(source_embeddings_np, target_embeddings_np.T)

    return similarity_matrix.tolist()  # type: ignore[no-any-return]


def get_api_backend(*args: Any, **kwargs: Any) -> BaseAPIBackend:
    """
    基于配置动态获取LLM API后端实例

    根据LLM_SETTINGS中的backend配置，动态加载并实例化相应的API后端。
    支持多种LLM Provider的统一接口访问。

    Args:
        *args: 传递给API后端构造函数的位置参数
        **kwargs: 传递给API后端构造函数的关键字参数

    Returns:
        BaseAPIBackend: 配置的API后端实例

    Example:
        >>> backend = get_api_backend(api_key="your_key", model="gpt-4")
        >>> response = backend.chat_completion("你好，请介绍一下RD-Agent")

    Note:
        TODO: 考虑从base.py模块导入此函数以避免重复定义

    Raises:
        ImportError: 当配置的backend类无法导入时
        TypeError: 当backend类不是BaseAPIBackend的子类时
    """
    # 根据配置动态导入API后端类
    api_backend_cls: Type[BaseAPIBackend] = import_class(LLM_SETTINGS.backend)

    # 实例化并返回API后端
    return api_backend_cls(*args, **kwargs)


# 创建别名，方便直接使用
APIBackend = get_api_backend
"""
APIBackend别名

提供直接访问API后端的便捷方式，等同于调用get_api_backend()。

使用示例：
    >>> from rdagent.oai.llm_utils import APIBackend
    >>> backend = APIBackend()
    >>> response = backend.chat_completion("Hello")
"""
