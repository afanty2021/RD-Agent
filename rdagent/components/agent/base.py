# -*- coding: utf-8 -*-
"""
RD-Agent 智能体基类模块

本模块定义了RD-Agent智能体系统的核心抽象基类和Pydantic-AI实现，
提供：
1. 统一的智能体接口规范
2. Pydantic-AI集成和MCP协议支持
3. 可选的Prefect缓存机制
4. 工具集和提示词管理

智能体架构：
- BaseAgent: 智能体抽象基类，定义统一接口
- PAIAgent: 基于Pydantic-AI的具体实现
- MCP支持: 集成Model Context Protocol协议
- 缓存机制: 可选的持久化缓存提升性能

使用场景：
- 对话式智能体：与用户进行自然语言交互
- 任务执行智能体：执行特定的编码和评估任务
- 工具调用智能体：集成外部工具和API
- 知识检索智能体：RAG增强的知识问答

作者: RD-Agent Team
"""

from abc import abstractmethod

import nest_asyncio
from prefect import task
from prefect.cache_policies import INPUTS
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerStreamableHTTP

from rdagent.oai.backend.pydantic_ai import get_agent_model


class BaseAgent:
    """
    RD-Agent智能体抽象基类

    定义了RD-Agent智能体系统的统一接口规范。
    所有智能体实现都必须继承此基类并实现抽象方法。

    设计理念：
    - 接口统一：确保所有智能体有一致的行为模式
    - 功能抽象：定义智能体的核心功能契约
    - 可扩展性：支持不同类型的智能体实现

    核心方法：
    - __init__: 初始化智能体，设置系统提示词和工具集
    - query: 执行查询任务，返回智能体的响应结果

    实现要求：
    - 子类必须实现所有抽象方法
    - 确保线程安全和资源管理
    - 提供适当的错误处理机制
    """

    @abstractmethod
    def __init__(self, system_prompt: str, toolsets: list[str]):
        """
        初始化智能体

        Args:
            system_prompt: 系统提示词，定义智能体的角色和行为规范
            toolsets: 工具集列表，包含智能体可以使用的工具名称或MCP服务器
        """
        ...

    @abstractmethod
    def query(self, query: str) -> str:
        """
        执行查询任务

        Args:
            query: 用户查询字符串

        Returns:
            str: 智能体的响应结果

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        ...


class PAIAgent(BaseAgent):
    """
    基于Pydantic-AI的智能体实现

    这是RD-Agent的默认智能体实现，基于Pydantic-AI框架构建。
    提供完整的LLM集成、MCP协议支持和可选的缓存机制。

    核心特性：
    1. **Pydantic-AI集成**：使用现代的AI智能体框架
    2. **MCP协议支持**：集成Model Context Protocol，支持工具调用
    3. **可选缓存**：通过Prefect提供持久化缓存能力
    4. **异步支持**：基于nest_asyncio的异步执行
    5. **类型安全**：完整的类型注解和验证

    MCP (Model Context Protocol) 支持：
    - 支持HTTP流式MCP服务器
    - 自动工具集注册和管理
    - 工具调用结果的类型安全处理
    - 支持多种工具源（URL、实例等）

    缓存机制：
    - 基于Prefect的任务级缓存
    - INPUTS缓存策略：基于输入参数的智能缓存
    - 需要Prefect服务器支持
    - 显著提升重复查询的性能

    Attributes:
        agent: Pydantic-AI智能体实例，负责实际的推理和执行
        enable_cache: 是否启用缓存机制的标志
                     True: 启用Prefect缓存， False: 禁用缓存
    """

    agent: Agent
    """Pydantic-AI智能体实例，封装了LLM调用、工具管理和推理逻辑"""

    enable_cache: bool
    """缓存启用标志，控制是否使用Prefect持久化缓存"""

    def __init__(
        self,
        system_prompt: str,
        toolsets: list[str | MCPServerStreamableHTTP],
        enable_cache: bool = False,
    ):
        """
        初始化Pydantic-AI智能体

        Args:
            system_prompt: 系统提示词，定义智能体的角色、能力和行为规范
                         这是智能体决策的基础，影响所有后续的响应
            toolsets: MCP服务器列表，支持两种格式：
                     - str: MCP服务器的URL地址
                     - MCPServerStreamableHTTP: MCP服务器实例
                     智能体将自动注册这些服务器提供的工具
            enable_cache: 是否启用Prefect缓存机制
                         True: 启用缓存，需要运行Prefect服务器
                         False: 禁用缓存，每次都重新计算
                         默认为False

        缓存配置说明：
        启用缓存前需要：
        1. 启动Prefect服务器：`prefect server start`
        2. 设置环境变量：`export PREFECT_API_URL=http://localhost:4200/api`
        3. 确保有足够的存储空间用于缓存数据

        性能考虑：
        - 缓存能显著提升重复查询的性能
        - 但会增加存储开销和首次查询的延迟
        - 建议在生产环境中启用，开发环境中按需启用

        Example:
            >>> # 基础智能体
            >>> agent = PAIAgent(
            ...     system_prompt="你是一个专业的机器学习工程师",
            ...     toolsets=["http://localhost:8000/mcp"],
            ...     enable_cache=False
            ... )
            >>>
            >>> # 带缓存的智能体
            >>> cached_agent = PAIAgent(
            ...     system_prompt="你是一个数据分析专家",
            ...     toolsets=["http://tools-server:8080/mcp"],
            ...     enable_cache=True
            ... )
        """
        toolsets = [(ts if isinstance(ts, MCPServerStreamableHTTP) else MCPServerStreamableHTTP(ts)) for ts in toolsets]
        self.agent = Agent(get_agent_model(), system_prompt=system_prompt, toolsets=toolsets)
        self.enable_cache = enable_cache

        # Create cached query function if caching is enabled
        if enable_cache:
            self._cached_query = task(cache_policy=INPUTS, persist_result=True)(self._run_query)

    def _run_query(self, query: str) -> str:
        """
        Internal query execution (no caching)
        """
        nest_asyncio.apply()  # NOTE: very important. Because pydantic-ai uses asyncio!
        result = self.agent.run_sync(query)
        return result.output

    def query(self, query: str) -> str:
        """
        Run agent query with optional caching

        Parameters
        ----------
        query : str

        Returns
        -------
        str
        """
        if self.enable_cache:
            return self._cached_query(query)
        else:
            return self._run_query(query)
