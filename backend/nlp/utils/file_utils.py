import os
import shutil
import tempfile
import logging
from typing import List, Dict, Any, Optional
import magic  # 文件类型检测库

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """
        验证文件路径是否有效
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否有效
        """
        if not file_path or not isinstance(file_path, str):
            return False
        
        try:
            # 检查文件是否存在
            if not os.path.exists(file_path):
                logger.warning(f"文件不存在: {file_path}")
                return False
            
            # 检查是否是文件
            if not os.path.isfile(file_path):
                logger.warning(f"不是文件: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"文件路径验证失败: {e}")
            return False
    
    @staticmethod
    def get_file_info(file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件信息字典
        """
        if not FileUtils.validate_file_path(file_path):
            return {}
        
        try:
            file_info = {
                "path": file_path,
                "size": os.path.getsize(file_path),
                "modified_time": os.path.getmtime(file_path),
                "created_time": os.path.getctime(file_path),
                "is_readable": os.access(file_path, os.R_OK),
                "is_writable": os.access(file_path, os.W_OK),
                "extension": os.path.splitext(file_path)[1].lower()
            }
            
            # 使用magic库检测文件类型
            try:
                mime = magic.Magic(mime=True)
                file_info["mime_type"] = mime.from_file(file_path)
            except:
                file_info["mime_type"] = "unknown/unknown"
            
            logger.info(f"获取文件信息: {file_path}")
            return file_info
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {}
    
    @staticmethod
    def copy_file(src_path: str, dst_path: str) -> bool:
        """
        复制文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        if not FileUtils.validate_file_path(src_path):
            return False
        
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(src_path, dst_path)
            logger.info(f"复制文件: {src_path} -> {dst_path}")
            return True
            
        except Exception as e:
            logger.error(f"复制文件失败: {e}")
            return False
    
    @staticmethod
    def move_file(src_path: str, dst_path: str) -> bool:
        """
        移动文件
        
        Args:
            src_path: 源文件路径
            dst_path: 目标文件路径
            
        Returns:
            是否成功
        """
        if not FileUtils.validate_file_path(src_path):
            return False
        
        try:
            # 确保目标目录存在
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # 移动文件
            shutil.move(src_path, dst_path)
            logger.info(f"移动文件: {src_path} -> {dst_path}")
            return True
            
        except Exception as e:
            logger.error(f"移动文件失败: {e}")
            return False
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否成功
        """
        if not FileUtils.validate_file_path(file_path):
            return False
        
        try:
            os.remove(file_path)
            logger.info(f"删除文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"删除文件失败: {e}")
            return False
    
    @staticmethod
    def list_files(directory: str, extensions: Optional[List[str]] = None) -> List[str]:
        """
        列出目录中的文件
        
        Args:
            directory: 目录路径
            extensions: 文件扩展名过滤（可选）
            
        Returns:
            文件路径列表
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            return []
        
        try:
            files = []
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    
                    # 如果指定了扩展名过滤
                    if extensions:
                        ext = os.path.splitext(filename)[1].lower()
                        if ext in extensions:
                            files.append(file_path)
                    else:
                        files.append(file_path)
            
            logger.info(f"列出目录文件: {directory}, 找到 {len(files)} 个文件")
            return files
            
        except Exception as e:
            logger.error(f"列出目录文件失败: {e}")
            return []
    
    @staticmethod
    def create_temp_file(content: str = "", suffix: str = ".txt") -> str:
        """
        创建临时文件
        
        Args:
            content: 文件内容
            suffix: 文件后缀
            
        Returns:
            临时文件路径
        """
        try:
            # 创建临时文件
            with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as temp_file:
                if content:
                    temp_file.write(content)
                temp_path = temp_file.name
            
            logger.info(f"创建临时文件: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"创建临时文件失败: {e}")
            return ""
    
    @staticmethod
    def read_file_content(file_path: str, encoding: str = "utf-8") -> str:
        """
        读取文件内容
        
        Args:
            file_path: 文件路径
            encoding: 文件编码
            
        Returns:
            文件内容
        """
        if not FileUtils.validate_file_path(file_path):
            return ""
        
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            logger.info(f"读取文件内容: {file_path}, 长度: {len(content)}")
            return content
            
        except Exception as e:
            logger.error(f"读取文件内容失败: {e}")
            return ""
    
    @staticmethod
    def write_file_content(file_path: str, content: str, encoding: str = "utf-8") -> bool:
        """
        写入文件内容
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码
            
        Returns:
            是否成功
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, 'w', encoding=encoding) as file:
                file.write(content)
            
            logger.info(f"写入文件内容: {file_path}, 长度: {len(content)}")
            return True
            
        except Exception as e:
            logger.error(f"写入文件内容失败: {e}")
            return False
    
    @staticmethod
    def is_pdf_file(file_path: str) -> bool:
        """
        检查是否是PDF文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否是PDF文件
        """
        if not FileUtils.validate_file_path(file_path):
            return False
        
        try:
            file_info = FileUtils.get_file_info(file_path)
            return file_info.get("mime_type", "").startswith("application/pdf")
            
        except Exception as e:
            logger.error(f"检查PDF文件失败: {e}")
            return False
    
    @staticmethod
    def is_image_file(file_path: str) -> bool:
        """
        检查是否是图像文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否是图像文件
        """
        if not FileUtils.validate_file_path(file_path):
            return False
        
        try:
            file_info = FileUtils.get_file_info(file_path)
            return file_info.get("mime_type", "").startswith("image/")
            
        except Exception as e:
            logger.error(f"检查图像文件失败: {e}")
            return False
    
    @staticmethod
    def get_file_size_formatted(file_path: str, unit: str = "MB") -> float:
        """
        获取格式化的文件大小
        
        Args:
            file_path: 文件路径
            unit: 单位（B, KB, MB, GB）
            
        Returns:
            格式化后的文件大小
        """
        if not FileUtils.validate_file_path(file_path):
            return 0.0
        
        try:
            size = os.path.getsize(file_path)
            
            # 转换单位
            if unit.upper() == "B":
                return size
            elif unit.upper() == "KB":
                return size / 1024
            elif unit.upper() == "MB":
                return size / (1024 * 1024)
            elif unit.upper() == "GB":
                return size / (1024 * 1024 * 1024)
            else:
                return size / (1024 * 1024)  # 默认MB
            
        except Exception as e:
            logger.error(f"获取文件大小失败: {e}")
            return 0.0







