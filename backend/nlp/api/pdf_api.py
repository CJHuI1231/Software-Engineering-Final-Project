import os
import tempfile
import shutil
from fastapi import APIRouter, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import logging
import time
import sys

# 添加OCR模块路径
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'OCR'))
from PDF_OCR import PdfOcrParser

# 添加NLP模块路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from summary.summary_model import SummaryModel
from entity_recognition.entity_recognition import EntityRecognitionModel

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 数据库集成（可选）
db_integration = None
try:
    from backend.integration import DatabaseIntegration
    db_integration = DatabaseIntegration()
    logger.info("数据库集成服务加载成功")
except ImportError as e:
    logger.warning(f"数据库集成服务未加载（可选功能）: {e}")
except Exception as e:
    logger.warning(f"数据库集成服务初始化失败: {e}")

# 创建API路由器
router = APIRouter(
    tags=["PDF Processing"]
)

# 初始化模型
try:
    # 初始化PDF OCR解析器
    pdf_parser = PdfOcrParser(ocr_lang='chi_sim+eng')
    logger.info("PDF OCR解析器初始化成功")
    
    # 初始化摘要模型
    summary_model = SummaryModel({})
    logger.info("摘要模型初始化成功")
    
    # 初始化实体识别模型
    entity_model = EntityRecognitionModel({})
    logger.info("实体识别模型初始化成功")
    
except Exception as e:
    logger.error(f"模型初始化失败: {e}")
    pdf_parser = None
    summary_model = None
    entity_model = None

@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    """
    上传PDF文件并提取文本
    
    请求格式: multipart/form-data
    
    响应格式:
    {
        "status": "success",
        "file_id": "uuid",
        "filename": "example.pdf",
        "text": "提取的文本内容",
        "processing_time": 5.2,
        "pages_processed": 10
    }
    """
    try:
        # 检查文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 检查文件大小 (100MB限制，但会对大文件进行处理)
        file_size = 0
        for chunk in file.file:
            file_size += len(chunk)
            if file_size > 100 * 1024 * 1024:  # 100MB
                raise HTTPException(status_code=413, detail="文件大小超过100MB限制")
        
        # 重置文件指针
        await file.seek(0)
        
        # 检查是否为大文件（>10MB），如果是则进行分块处理
        is_large_file = file_size > 10 * 1024 * 1024  # 10MB
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = temp_file.name
        
        try:
            # 记录处理开始时间
            start_time = time.time()
            
            # 解析PDF并提取文本
            if not pdf_parser:
                raise HTTPException(status_code=503, detail="PDF处理服务暂时不可用")
            
            # 对于大文件，使用优化的处理方式
            if is_large_file:
                logger.info(f"检测到大文件({file_size/1024/1024:.2f}MB)，使用优化处理方式")
                extracted_text = pdf_parser.parse(temp_path)
                
                # 对大文件的文本进行截取，避免处理超时
                if len(extracted_text) > 50000:  # 约25,000个中文字符
                    extracted_text = extracted_text[:50000]
                    logger.info("大文件文本已截取至50,000字符以优化处理速度")
            else:
                extracted_text = pdf_parser.parse(temp_path)
            
            # 计算处理时间
            processing_time = time.time() - start_time
            
            # 计算处理页数
            page_count = extracted_text.count('\n\n') + 1 if extracted_text else 0
            
            # 生成唯一文件ID
            file_id = f"pdf_{int(time.time())}_{hash(file.filename)}".replace('-', '_')
            
            # 保存提取的文本到临时文件
            text_temp_path = os.path.join(tempfile.gettempdir(), f"{file_id}.txt")
            with open(text_temp_path, 'w', encoding='utf-8') as text_file:
                text_file.write(extracted_text)
            
            # 构建响应
            response = {
                "status": "success",
                "file_id": file_id,
                "filename": file.filename,
                "text": extracted_text,
                "processing_time": round(processing_time, 2),
                "pages_processed": page_count
            }
            
            logger.info(f"PDF文件 {file.filename} 处理完成，耗时 {processing_time:.2f}s")
            return response
            
        finally:
            # 删除临时PDF文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF上传处理错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/summary")
async def generate_pdf_summary(request: Dict[str, Any]):
    """
    为PDF文本生成摘要
    
    请求格式:
    {
        "file_id": "uuid",
        "text": "PDF文本内容",
        "method": "bart|textrank|auto",
        "max_length": 150,
        "min_length": 30
    }
    
    响应格式:
    {
        "status": "success",
        "summary": "生成的摘要文本",
        "method_used": "bart",
        "processing_time": 1.8,
        "quality_metrics": {...}
    }
    """
    try:
        # 检查模型是否初始化
        if not summary_model:
            raise HTTPException(status_code=503, detail="摘要生成服务暂时不可用")
        
        # 获取请求参数
        text = request.get('text', '')
        method = request.get('method', 'auto')
        max_length = request.get('max_length', 150)
        min_length = request.get('min_length', 30)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 根据方法生成摘要
        if method == "bart":
            summary = summary_model.generate_bart_summary(text, max_length, min_length)
        elif method == "textrank":
            summary = summary_model.generate_textrank_summary(text)
        elif method == "auto":
            summary = summary_model.select_best_summary(text, max_length, min_length)
        else:
            raise HTTPException(status_code=400, detail="不支持的摘要方法")
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 评估摘要质量
        quality_metrics = summary_model.evaluate_summary_quality(text, summary)
        
        # 构建响应
        response = {
            "status": "success",
            "summary": summary,
            "method_used": method,
            "processing_time": round(processing_time, 2),
            "quality_metrics": quality_metrics
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF摘要生成错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entities")
async def extract_pdf_entities(request: Dict[str, Any]):
    """
    从PDF文本中提取实体
    
    请求格式:
    {
        "file_id": "uuid",
        "text": "PDF文本内容",
        "entity_types": ["PERSON", "ORG", "DATE", "LOCATION"],
        "relation_extraction": true
    }
    
    响应格式:
    {
        "status": "success",
        "entities": [...],
        "relations": [...],
        "processing_time": 1.2
    }
    """
    try:
        # 检查模型是否初始化
        if not entity_model:
            raise HTTPException(status_code=503, detail="实体识别服务暂时不可用")
        
        # 获取请求参数
        text = request.get('text', '')
        entity_types = request.get('entity_types', [])
        relation_extraction = request.get('relation_extraction', False)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 执行实体识别
        entities = entity_model.recognize_entities(text)
        
        # 如果需要提取关系
        relations = []
        if relation_extraction:
            relations = entity_model.extract_entity_relations(text)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "entities": entities,
            "relations": relations,
            "processing_time": round(processing_time, 2),
            "entity_types_supported": entity_model.get_supported_entity_types()
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF实体提取错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge_graph")
async def generate_knowledge_graph(request: Dict[str, Any]):
    """
    为PDF内容生成知识图谱
    
    请求格式:
    {
        "file_id": "uuid",
        "text": "PDF文本内容",
        "entity_types": ["PERSON", "ORG", "DATE", "LOCATION"],
        "relation_extraction": true
    }
    
    响应格式:
    {
        "status": "success",
        "nodes": [...],
        "edges": [...],
        "processing_time": 2.5
    }
    """
    try:
        # 检查模型是否初始化
        if not entity_model:
            raise HTTPException(status_code=503, detail="实体识别服务暂时不可用")
        
        # 获取请求参数
        text = request.get('text', '')
        entity_types = request.get('entity_types', [])
        relation_extraction = request.get('relation_extraction', True)
        
        if not text:
            raise HTTPException(status_code=400, detail="文本内容不能为空")
        
        # 记录请求开始时间
        start_time = time.time()
        
        # 执行实体识别
        entities = entity_model.recognize_entities(text)
        
        # 提取关系
        relations = []
        if relation_extraction:
            relations = entity_model.extract_entity_relations(text)
        
        # 转换为知识图谱格式
        nodes = []
        edges = []
        entity_id_map = {}
        
        # 创建节点
        for i, entity in enumerate(entities):
            entity_id = f"entity_{i}"
            entity_id_map[entity['text']] = entity_id
            nodes.append({
                "id": entity_id,
                "label": entity['text'],
                "type": entity['type'],
                "confidence": entity.get('confidence', 0.0)
            })
        
        # 创建边
        for relation in relations:
            subject = relation.get('subject', '')
            object = relation.get('object', '')
            relation_type = relation.get('relation', '')
            
            if subject in entity_id_map and object in entity_id_map:
                edges.append({
                    "source": entity_id_map[subject],
                    "target": entity_id_map[object],
                    "type": relation_type
                })
        
        # 计算处理时间
        processing_time = time.time() - start_time
        
        # 构建响应
        response = {
            "status": "success",
            "nodes": nodes,
            "edges": edges,
            "processing_time": round(processing_time, 2),
            "entity_count": len(nodes),
            "relation_count": len(edges)
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"知识图谱生成错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/info")
def get_pdf_info():
    """
    获取PDF处理服务信息
    
    响应格式:
    {
        "status": "success",
        "service": "PDF Processing API",
        "version": "1.0.0",
        "features": [
            "PDF text extraction",
            "Summary generation",
            "Entity recognition",
            "Knowledge graph generation"
        ],
        "supported_formats": ["PDF"],
        "max_file_size": "50MB"
    }
    """
    try:
        # 构建响应
        response = {
            "status": "success",
            "service": "PDF Processing API",
            "version": "1.0.0",
            "features": [
                "PDF text extraction",
                "Summary generation",
                "Entity recognition",
                "Knowledge graph generation",
                "Database storage"
            ],
            "supported_formats": ["PDF"],
            "max_file_size": "50MB",
            "services": {
                "pdf_ocr": "available" if pdf_parser else "unavailable",
                "summary": "available" if summary_model else "unavailable",
                "entity_recognition": "available" if entity_model else "unavailable",
                "database": "available" if db_integration else "unavailable"
            }
        }
        
        return response
        
    except Exception as e:
        logger.error(f"获取PDF处理服务信息错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 数据库集成API ====================

@router.post("/process_and_store")
async def process_and_store_pdf(
    file: UploadFile = File(...),
    user_id: str = Form(default="user_001"),
    title: str = Form(default=None),
    generate_summary: bool = Form(default=True),
    extract_entities: bool = Form(default=True),
    extract_tags: bool = Form(default=True)
):
    """
    完整的PDF处理流程：提取文本 + NLP分析 + 存入数据库
    
    请求格式: multipart/form-data
    - file: PDF文件
    - user_id: 用户ID (默认: user_001)
    - title: 文档标题 (默认: 文件名)
    - generate_summary: 是否生成摘要 (默认: true)
    - extract_entities: 是否提取实体 (默认: true)
    - extract_tags: 是否提取标签/关键词 (默认: true)
    
    响应格式:
    {
        "status": "success",
        "doc_id": "doc_xxx",
        "filename": "example.pdf",
        "text_length": 5000,
        "entities_count": 25,
        "summary": "...",
        "tags": ["关键词1", "关键词2"],
        "processing_time": 10.5,
        "stored_to_database": true
    }
    """
    try:
        # 检查必要服务
        if not pdf_parser:
            raise HTTPException(status_code=503, detail="PDF处理服务暂时不可用")
        
        # 检查文件类型
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="只支持PDF文件")
        
        # 设置默认标题
        if not title:
            title = os.path.splitext(file.filename)[0]
        
        # 获取文件大小
        file_content = await file.read()
        file_size = len(file_content)
        await file.seek(0)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            start_time = time.time()
            
            # 1. 提取文本
            logger.info(f"开始处理PDF: {file.filename}")
            extracted_text = pdf_parser.parse(temp_path)
            
            # 2. 生成摘要
            summary_dict = None
            if generate_summary and summary_model:
                try:
                    short_summary = summary_model.generate_textrank_summary(extracted_text[:5000])
                    medium_summary = summary_model.select_best_summary(extracted_text[:10000], max_length=200, min_length=50)
                    summary_dict = {
                        "short": short_summary[:100] if short_summary else None,
                        "medium": medium_summary[:300] if medium_summary else None,
                        "long": medium_summary,
                        "method": "auto"
                    }
                    logger.info("摘要生成完成")
                except Exception as e:
                    logger.warning(f"摘要生成失败: {e}")
            
            # 3. 提取实体
            entities = []
            if extract_entities and entity_model:
                try:
                    entities = entity_model.recognize_entities(extracted_text[:20000])
                    logger.info(f"识别到 {len(entities)} 个实体")
                except Exception as e:
                    logger.warning(f"实体提取失败: {e}")
            
            # 4. 提取关键词作为标签
            tags = []
            if extract_tags and entities:
                # 使用高频实体作为标签
                from collections import Counter
                entity_texts = [e.get('text', '') for e in entities if len(e.get('text', '')) > 1]
                tag_counts = Counter(entity_texts)
                tags = [tag for tag, count in tag_counts.most_common(10)]
            
            processing_time = time.time() - start_time
            
            # 5. 存入数据库
            stored_to_database = False
            doc_id = None
            
            if db_integration:
                try:
                    # 保存文件到uploads目录
                    upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), 'uploads')
                    os.makedirs(upload_dir, exist_ok=True)
                    
                    file_id = f"pdf_{int(time.time())}_{hash(file.filename)}".replace('-', '_')
                    saved_path = os.path.join(upload_dir, f"{file_id}.pdf")
                    
                    with open(saved_path, 'wb') as f:
                        f.write(file_content)
                    
                    # 调用数据库集成服务
                    db_result = db_integration.process_and_store_pdf(
                        user_id=user_id,
                        title=title,
                        file_path=saved_path,
                        file_size=file_size,
                        extracted_text=extracted_text,
                        entities=entities,
                        summary=summary_dict,
                        tags=tags
                    )
                    
                    stored_to_database = db_result.get('success', False)
                    doc_id = db_result.get('doc_id')
                    
                    if stored_to_database:
                        logger.info(f"文档已存入数据库: {doc_id}")
                    else:
                        logger.warning(f"数据库存储失败: {db_result.get('errors')}")
                        
                except Exception as e:
                    logger.error(f"数据库存储异常: {e}")
            
            # 构建响应
            response = {
                "status": "success",
                "doc_id": doc_id,
                "filename": file.filename,
                "title": title,
                "text_length": len(extracted_text),
                "entities_count": len(entities),
                "summary": summary_dict.get('medium') if summary_dict else None,
                "tags": tags,
                "processing_time": round(processing_time, 2),
                "stored_to_database": stored_to_database
            }
            
            return response
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF处理存储错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_id}")
async def get_document_info(doc_id: str):
    """
    获取已存储文档的完整信息
    
    路径参数:
    - doc_id: 文档ID
    
    响应格式:
    {
        "status": "success",
        "document": {
            "doc_id": "xxx",
            "title": "文档标题",
            "summary": {...},
            "tags": [...],
            "entities": [...]
        }
    }
    """
    if not db_integration:
        raise HTTPException(status_code=503, detail="数据库服务未启用")
    
    try:
        result = db_integration.get_document(doc_id)
        
        if result.get('success'):
            return {
                "status": "success",
                "document": result.get('document')
            }
        else:
            raise HTTPException(status_code=404, detail=result.get('message', '文档不存在'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档信息错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/document/{doc_id}/statistics")
async def get_document_statistics(doc_id: str):
    """
    获取文档统计信息
    
    路径参数:
    - doc_id: 文档ID
    
    响应格式:
    {
        "status": "success",
        "statistics": {
            "entity_count": 25,
            "entity_type_distribution": {"person": 10, "organization": 8, ...},
            "tag_count": 5,
            "has_summary": true
        }
    }
    """
    if not db_integration:
        raise HTTPException(status_code=503, detail="数据库服务未启用")
    
    try:
        result = db_integration.get_document_statistics(doc_id)
        
        if result.get('success'):
            return {
                "status": "success",
                "statistics": result
            }
        else:
            raise HTTPException(status_code=404, detail=result.get('message', '文档不存在'))
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取文档统计信息错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
