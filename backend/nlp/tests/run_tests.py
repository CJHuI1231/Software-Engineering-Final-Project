#!/usr/bin/env python3
"""
测试运行脚本
用于运行NLP处理模块的所有测试用例
"""

import sys
import os
import subprocess
import time

def run_tests():
    """运行所有测试用例"""
    print("开始运行NLP处理模块测试...")
    print("=" * 50)
    
    # 记录开始时间
    start_time = time.time()
    
    # 测试目录
    test_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)))
    
    # 运行pytest
    try:
        # 构建pytest命令
        cmd = [
            sys.executable, "-m", "pytest",
            test_dir,
            "--verbose",
            "--tb=short",
            "--cov=nlp",
            "--cov-report=html:cov_report",
            "--cov-report=term-missing"
        ]
        
        print("运行测试命令:", " ".join(cmd))
        print()
        
        # 执行测试
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # 输出测试结果
        print(result.stdout)
        if result.stderr:
            print("错误输出:", result.stderr)
        
        # 计算并显示运行时间
        end_time = time.time()
        duration = end_time - start_time
        print("=" * 50)
        print(f"测试完成，总耗时: {duration:.2f}秒")
        
        # 检查覆盖率报告
        if os.path.exists("cov_report"):
            print("覆盖率报告已生成在: cov_report/index.html")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print("测试失败:")
        print(e.stdout)
        print(e.stderr)
        return False
    except Exception as e:
        print(f"运行测试时发生错误: {e}")
        return False

def check_dependencies():
    """检查依赖项"""
    print("检查依赖项...")
    
    try:
        import pytest
        import psutil
        import redis
        print("✓ 核心性能优化依赖已安装")
        return True
    except ImportError as e:
        print(f"✗ 缺少依赖项: {e}")
        print("请安装缺少的依赖项:")
        print("pip install -r requirements.txt")
        return False

def main():
    """主函数"""
    print("NLP处理模块测试套件")
    print("=" * 50)
    
    # 检查依赖项
    if not check_dependencies():
        return
    
    print()
    
    # 运行测试
    success = run_tests()
    
    if success:
        print("测试套件运行成功！")
    else:
        print("测试套件运行失败，请检查错误信息。")

if __name__ == "__main__":
    main()


