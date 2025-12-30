#!/usr/bin/env python3
"""
测试 BGE-M3 在 M4 Pro 上的内存占用
"""

import subprocess
import time
import json

def check_ollama_status():
    """检查 Ollama 服务状态"""
    try:
        result = subprocess.run(
            ["pgrep", "-x", "ollama"],
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except:
        return False

def get_memory_info():
    """获取系统内存信息"""
    try:
        # 使用 vm_stat 获取内存信息 (macOS)
        result = subprocess.run(
            ["vm_stat"],
            capture_output=True,
            text=True
        )

        mem_info = {}
        for line in result.stdout.split('\n'):
            if ':' in line:
                key, value = line.split(':')
                key = key.strip()
                value = value.strip().rstrip('.')
                try:
                    mem_info[key] = int(value) * 4096  # 页面大小为 4KB
                except:
                    pass

        # 转换为 GB
        for key in mem_info:
            mem_info[key] = mem_info[key] / (1024**3)

        return mem_info
    except:
        return {}

def get_process_memory():
    """获取 Ollama 进程内存"""
    try:
        result = subprocess.run(
            ["ps", aux | grep ollama | grep -v grep | awk '{print $6}'"],
            shell=True,
            capture_output=True,
            text=True
        )

        memories = []
        for line in result.stdout.split('\n'):
            try:
                mem_kb = int(line.strip())
                mem_mb = mem_kb / 1024
                memories.append(mem_mb)
            except:
                pass

        return memories
    except:
        return []

def test_bge_m3_memory():
    """测试 BGE-M3 实际内存占用"""
    print("=" * 60)
    print("🧪 BGE-M3 内存占用测试 (M4 Pro)")
    print("=" * 60)

    # 检查 Ollama 是否运行
    if not check_ollama_status():
        print("\n❌ Ollama 服务未运行")
        print("请先启动: ollama serve")
        return

    print("\n✅ Ollama 服务正在运行")

    # 测试前内存
    print("\n📊 测试前系统内存:")
    mem_before = get_memory_info()
    if 'Pages free' in mem_before:
        print(f"   可用内存: {mem_before.get('Pages free', 0):.2f} GB")

    # 发送测试请求
    print("\n🔄 发送 Embedding 测试请求...")

    test_texts = [
        "RD-Agent是微软开源的机器学习工程自主代理系统",
        "量化投资因子挖掘需要结合机器学习和金融知识",
    ] * 5  # 10条测试文本

    total_start = time.time()

    for i, text in enumerate(test_texts):
        start = time.time()
        result = subprocess.run(
            f'curl -s http://localhost:11434/api/embeddings -d \'{{"model": "bge-m3", "prompt": "{text}"}}\'',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        elapsed = time.time() - start

        if result.returncode == 0:
            response = json.loads(result.stdout)
            embedding = response.get("embedding", [])
            print(f"   [{i+1}/10] 延迟: {elapsed*1000:.1f}ms | 向量维度: {len(embedding)}")
        else:
            print(f"   [{i+1}/10] ❌ 请求失败")

    total_time = time.time() - total_start

    # 测试后内存
    print("\n📊 测试后系统内存:")
    mem_after = get_memory_info()
    if 'Pages free' in mem_after:
        print(f"   可用内存: {mem_after.get('Pages free', 0):.2f} GB")

    # Ollama 进程内存
    print("\n💾 Ollama 进程内存占用:")
    ollama_mem = get_process_memory()
    if ollama_mem:
        for i, mem in enumerate(ollama_mem):
            print(f"   进程 {i+1}: {mem:.1f} MB")
        print(f"   总计: {sum(ollama_mem):.1f} MB ({sum(ollama_mem)/1024:.2f} GB)")

    # 统计
    print(f"\n⚡ 性能统计:")
    print(f"   平均延迟: {total_time/len(test_texts)*1000:.1f}ms")
    print(f"   总耗时: {total_time:.2f}秒")
    print(f"   吞吐量: {len(test_texts)/total_time:.2f} 条/秒")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)

if __name__ == "__main__":
    test_bge_m3_memory()
