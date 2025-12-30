#!/usr/bin/env python3
"""
PKL文件查看工具
用于查看RD-Agent日志目录下的pickle文件内容
"""

import pickle
import os
import sys
from pathlib import Path
import pandas as pd

def view_pkl_file(pkl_path):
    """查看单个pkl文件的内容"""
    print(f"\n{'='*60}")
    print(f"文件: {pkl_path}")
    print(f"{'='*60}")
    
    try:
        with open(pkl_path, 'rb') as f:
            data = pickle.load(f)
        
        print(f"\n数据类型: {type(data)}")
        print(f"内容预览:")
        print("-" * 60)
        
        # 根据数据类型进行不同的展示
        if isinstance(data, dict):
            print(f"字典，包含 {len(data)} 个键:")
            for key, value in data.items():
                print(f"  - {key}: {type(value).__name__}")
                if isinstance(value, (str, int, float, bool)):
                    print(f"    值: {value}")
                elif isinstance(value, (list, tuple)):
                    print(f"    长度: {len(value)}")
                elif isinstance(value, dict):
                    print(f"    包含 {len(value)} 个键")
                elif isinstance(value, pd.DataFrame):
                    print(f"    DataFrame 形状: {value.shape}")
                    print(f"    列: {list(value.columns)}")
                    print(f"\n{value.head()}")
                else:
                    print(f"    值: {str(value)[:100]}...")
        
        elif isinstance(data, (list, tuple)):
            print(f"{'列表' if isinstance(data, list) else '元组'}，长度: {len(data)}")
            if len(data) > 0:
                print(f"第一个元素类型: {type(data[0])}")
                print(f"前3个元素:")
                for i, item in enumerate(data[:3]):
                    print(f"  [{i}]: {type(item).__name__} - {str(item)[:100]}")
        
        elif isinstance(data, pd.DataFrame):
            print(f"DataFrame，形状: {data.shape}")
            print(f"列: {list(data.columns)}")
            print(f"\n{data}")
        
        elif hasattr(data, '__dict__'):
            # 对象类型
            print(f"对象属性:")
            for key, value in data.__dict__.items():
                print(f"  - {key}: {type(value).__name__}")
                if isinstance(value, (str, int, float, bool)):
                    print(f"    值: {value}")
                else:
                    print(f"    值: {str(value)[:100]}...")
        
        else:
            print(f"值: {data}")
        
        print("\n" + "="*60)
        return data
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def list_pkl_files(log_dir):
    """列出日志目录下的所有pkl文件"""
    pkl_files = list(Path(log_dir).rglob("*.pkl"))
    print(f"找到 {len(pkl_files)} 个pkl文件:")
    print("-" * 60)
    
    # 按大小分类显示
    for pkl_file in sorted(pkl_files)[:20]:  # 只显示前20个
        size = pkl_file.stat().st_size
        relative_path = pkl_file.relative_to(log_dir)
        print(f"  {relative_path} ({size} bytes)")
    
    if len(pkl_files) > 20:
        print(f"  ... 还有 {len(pkl_files) - 20} 个文件")
    
    return pkl_files

if __name__ == "__main__":
    log_dir = "/Users/berton/Github/RD-Agent/log"
    
    if len(sys.argv) > 1:
        # 如果提供了参数，打开指定的pkl文件
        pkl_path = sys.argv[1]
        view_pkl_file(pkl_path)
    else:
        # 否则列出所有pkl文件
        print("RD-Agent PKL文件查看工具")
        print("="*60)
        pkl_files = list_pkl_files(log_dir)
        
        print("\n使用方法:")
        print(f"  python view_pkl.py <pkl文件路径>")
        print(f"\n例如:")
        print(f"  python view_pkl.py {pkl_files[0]}")
