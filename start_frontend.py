#!/usr/bin/env python3
"""
前端服务启动脚本
用于启动前端开发服务器
"""

import os
import sys
import webbrowser
import threading
import time
from pathlib import Path
import http.server
import socketserver

# 获取当前目录
current_dir = Path(__file__).parent
frontend_dir = current_dir / "web_fronted"

def check_frontend_files():
    """检查前端文件是否存在"""
    required_files = [
        "index.html",
        "main.js",
        "styles.css"
    ]
    
    for file in required_files:
        file_path = frontend_dir / file
        if not file_path.exists():
            print(f"错误: 缺少前端文件 {file}")
            return False
    
    print("前端文件检查通过")
    return True

def start_server(port=8080):
    """启动HTTP服务器"""
    os.chdir(frontend_dir)
    
    # 使用Python内置的HTTP服务器
    handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"前端服务器已启动，地址: http://localhost:{port}")
            httpd.serve_forever()
    except OSError as e:
        print(f"无法启动服务器: {e}")
        return False
    
    return True

def open_browser(url, delay=2):
    """延迟打开浏览器"""
    time.sleep(delay)
    webbrowser.open(url)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='启动前端开发服务器')
    parser.add_argument(
        '--port', 
        type=int, 
        default=8080, 
        help='服务器端口 (默认: 8080)'
    )
    parser.add_argument(
        '--no-browser', 
        action='store_true', 
        help='不自动打开浏览器'
    )
    
    args = parser.parse_args()
    
    # 检查前端文件
    if not check_frontend_files():
        sys.exit(1)
    
    # 启动浏览器的线程
    if not args.no_browser:
        url = f"http://localhost:{args.port}"
        browser_thread = threading.Thread(
            target=open_browser, 
            args=(url,), 
            daemon=True
        )
        browser_thread.start()
    
    # 启动服务器
    try:
        start_server(args.port)
    except KeyboardInterrupt:
        print("\n前端服务器已停止")

if __name__ == "__main__":
    main()
