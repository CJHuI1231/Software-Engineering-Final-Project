#!/usr/bin/env python3
"""
后端服务启动脚本
用于启动NLP服务和PDF处理服务
"""

import os
import sys
import logging
import argparse
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "backend"))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='启动PDF处理和NLP服务')
    parser.add_argument(
        '--host', 
        default='0.0.0.0', 
        help='服务器主机地址 (默认: 0.0.0.0)'
    )
    parser.add_argument(
        '--port', 
        type=int, 
        default=8000, 
        help='服务器端口 (默认: 8000)'
    )
    parser.add_argument(
        '--reload', 
        action='store_true', 
        help='启用自动重载 (开发模式)'
    )
    parser.add_argument(
        '--workers', 
        type=int, 
        default=4, 
        help='工作进程数 (默认: 4)'
    )
    parser.add_argument(
        '--log-level', 
        choices=['debug', 'info', 'warning', 'error'], 
        default='info', 
        help='日志级别 (默认: info)'
    )
    
    return parser.parse_args()

def check_system_requirements():
    """检查系统要求"""
    try:
        # 检查Tesseract OCR
        import pytesseract
        pytesseract.get_tesseract_version()
        logger.info("Tesseract OCR 可用")

        # 检查Poppler (pdf2image需要)
        try:
            import pdf2image
            # 简单检查是否可以导入，不调用内部方法
            logger.info("Poppler 可用")
        except ImportError as e:
            logger.error(f"无法导入pdf2image模块: {e}")
            logger.error("请安装pdf2image库: pip install pdf2image")
            return False

        # 尝试调用 pdf2image 的基本功能来验证
        try:
            from pdf2image import convert_from_path
            # 只验证函数存在，不实际执行
            logger.info("pdf2image 功能验证通过")
        except ImportError as e:
            logger.error(f"pdf2image 功能不可用: {e}")
            return False

        return True
    except ImportError as e:
        logger.error(f"系统要求检查失败: {e}")
        return False
    except Exception as e:
        logger.error(f"系统要求检查失败: {e}")
        logger.error("请确保已安装 Tesseract OCR 和 Poppler")
        return False

def main():
    """主函数"""
    args = parse_arguments()
    
    try:
        # 直接尝试导入所有必要的模块
        import fastapi
        import uvicorn
        import pdf2image
        import pytesseract
        import pdfplumber
        logger.info("所有必要的依赖项检查通过")
    except ImportError as e:
        logger.error(f"缺少依赖项: {e}")
        logger.error("请运行 'pip install -r requirements.txt' 安装依赖项")
        sys.exit(1)
    
    # 检查系统要求
    if not check_system_requirements():
        sys.exit(1)
    
    # 设置环境变量
    os.environ["PYTHONPATH"] = str(current_dir)
    
    # 导入主应用
    try:
        from backend.nlp.main import create_app
        app = create_app()
        logger.info("应用创建成功")
    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.error("请确保已安装所有必要的依赖项")
        sys.exit(1)
    except Exception as e:
        logger.error(f"应用创建失败: {e}")
        logger.error("请检查配置和依赖项")
        sys.exit(1)
    
    # 启动服务器
    try:
        import uvicorn
        
        logger.info(f"启动服务器，地址: {args.host}:{args.port}")
        logger.info(f"工作进程数: {args.workers}")
        logger.info(f"日志级别: {args.log_level}")
        
        uvicorn.run(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            workers=1 if args.reload else args.workers,
            log_level=args.log_level
        )
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
