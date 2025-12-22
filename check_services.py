#!/usr/bin/env python3
"""
服务健康检查脚本
用于验证所有服务是否正常运行
"""

import requests
import time
import sys
import argparse
from typing import Dict, List, Tuple

# 服务配置
SERVICES = [
    {"name": "后端API", "url": "http://localhost:8000/health", "method": "GET"},
    {"name": "前端服务", "url": "http://localhost:8080", "method": "GET"},
    {"name": "Redis", "url": "http://localhost:6379", "method": "GET", "skip": True},  # Redis没有HTTP接口
    {"name": "Neo4j", "url": "http://localhost:7474", "method": "GET"},
]

def check_service(service: Dict) -> Tuple[bool, str]:
    """
    检查单个服务的健康状态
    
    Args:
        service: 服务配置字典
        
    Returns:
        (是否健康, 响应消息)
    """
    name = service["name"]
    url = service["url"]
    method = service.get("method", "GET")
    
    # 跳过检查的服务
    if service.get("skip", False):
        return (True, f"{name}: 跳过检查")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=5)
            if response.status_code < 400:
                return (True, f"{name}: 正常 (状态码: {response.status_code})")
            else:
                return (False, f"{name}: 异常 (状态码: {response.status_code})")
        else:
            # 可以扩展其他HTTP方法
            return (True, f"{name}: 不支持的方法 {method}")
    except requests.exceptions.ConnectionError:
        return (False, f"{name}: 连接失败")
    except requests.exceptions.Timeout:
        return (False, f"{name}: 请求超时")
    except Exception as e:
        return (False, f"{name}: 未知错误 ({str(e)})")

def check_all_services(services: List[Dict]) -> List[Tuple[bool, str]]:
    """
    检查所有服务的健康状态
    
    Args:
        services: 服务配置列表
        
    Returns:
        检查结果列表
    """
    results = []
    
    for service in services:
        result = check_service(service)
        results.append(result)
        
    return results

def print_results(results: List[Tuple[bool, str]]):
    """
    打印检查结果
    
    Args:
        results: 检查结果列表
    """
    print("=" * 50)
    print("服务健康检查结果")
    print("=" * 50)
    
    healthy_count = 0
    total_count = len(results)
    
    for is_healthy, message in results:
        if is_healthy:
            print(f"✅ {message}")
            healthy_count += 1
        else:
            print(f"❌ {message}")
    
    print("=" * 50)
    print(f"健康服务: {healthy_count}/{total_count}")
    
    if healthy_count == total_count:
        print("所有服务运行正常！")
        return 0
    else:
        print("部分服务存在问题，请检查日志")
        return 1

def wait_for_services(timeout: int = 120, interval: int = 5):
    """
    等待所有服务启动
    
    Args:
        timeout: 超时时间（秒）
        interval: 检查间隔（秒）
    """
    start_time = time.time()
    end_time = start_time + timeout
    
    print(f"等待服务启动，超时时间: {timeout}秒")
    
    while time.time() < end_time:
        results = check_all_services(SERVICES)
        all_healthy = all(result[0] for result in results)
        
        if all_healthy:
            print("所有服务已启动！")
            return True
        
        print(f"服务尚未全部就绪，{interval}秒后重试...")
        time.sleep(interval)
    
    print("等待服务启动超时")
    return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='检查服务健康状态')
    parser.add_argument(
        '--wait', 
        action='store_true', 
        help='等待所有服务启动'
    )
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=120, 
        help='等待超时时间（秒）'
    )
    
    args = parser.parse_args()
    
    if args.wait:
        success = wait_for_services(args.timeout)
        sys.exit(0 if success else 1)
    else:
        results = check_all_services(SERVICES)
        return_code = print_results(results)
        sys.exit(return_code)

if __name__ == "__main__":
    main()

