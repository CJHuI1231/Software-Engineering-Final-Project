-- For user
CREATE TABLE IF NOT EXISTS sys_user (
    user_id VARCHAR(32) NOT NULL COMMENT '唯一用户ID（UUID生成）',
    username VARCHAR(50) NOT NULL COMMENT '用户名（不可重复）',
    email VARCHAR(100) NOT NULL COMMENT '登录账号（邮箱格式）',
    password VARCHAR(128) NOT NULL COMMENT '密码',
    role VARCHAR(20) NOT NULL COMMENT '用户角色：普通用户/科研人员/教师/管理员',
    status TINYINT DEFAULT 1 COMMENT '账号状态：1-正常，0-禁用',
    theme VARCHAR(20) DEFAULT 'light' COMMENT '界面主题：light-日间，dark-夜间',
    summary_length VARCHAR(10) DEFAULT 'medium' COMMENT '摘要长度偏好：short/medium/long',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后修改时间',
    -- 约束
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_email (email), -- 邮箱唯一，避免重复注册
    UNIQUE KEY uk_username (username), -- 用户名唯一
    -- 索引（优化登录、权限查询）
    INDEX idx_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户基础信息表';

-- For document
CREATE TABLE IF NOT EXISTS doc_document (
    doc_id VARCHAR(32) NOT NULL COMMENT '唯一文档ID（UUID生成）',
    user_id VARCHAR(32) NOT NULL COMMENT '所属用户ID（关联sys_user.user_id）',
    title VARCHAR(255) NOT NULL COMMENT '文档标题（解析自PDF或用户修改）',
    author VARCHAR(255) DEFAULT NULL COMMENT '文档作者（解析自PDF）',
    upload_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '上传时间',
    file_path VARCHAR(512) NOT NULL COMMENT '文档存储路径（云端URL或本地路径）',
    file_size BIGINT NOT NULL COMMENT '文档大小（单位：字节）',
    file_format VARCHAR(10) DEFAULT 'pdf' COMMENT '文档格式（仅支持PDF）',
    category VARCHAR(50) DEFAULT NULL COMMENT '文档分类（用户自定义：如课程论文/科研文献）',
    is_deleted TINYINT DEFAULT 0 COMMENT '逻辑删除：0-未删除，1-已删除',
    -- 约束
    PRIMARY KEY (doc_id),
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化文档列表查询、检索功能）
    INDEX idx_user_deleted (user_id, is_deleted), -- 用户查询自己的未删除文档
    INDEX idx_title (title), -- 按标题检索文档
    INDEX idx_author (author) -- 按作者检索文档
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档元信息表';


CREATE TABLE IF NOT EXISTS doc_summary (
    summary_id VARCHAR(32) NOT NULL COMMENT '唯一摘要ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    content TEXT NOT NULL COMMENT '摘要内容（若过长可存文件，此处存核心摘要）',
    length_type VARCHAR(10) NOT NULL COMMENT '摘要长度类型：short/medium/long',
    generate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    -- 约束
    PRIMARY KEY (summary_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化文档-摘要关联查询）
    UNIQUE KEY uk_doc_id (doc_id) -- 一篇文档对应一条摘要，避免重复
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档摘要表';

CREATE TABLE IF NOT EXISTS doc_tag (
    tag_id VARCHAR(32) NOT NULL COMMENT '唯一标签ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    keyword VARCHAR(50) NOT NULL COMMENT '标签关键词（如：机器学习、NLP）',
    synonyms VARCHAR(255) DEFAULT NULL COMMENT '同义词（多个用逗号分隔）',
    generate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    -- 约束
    PRIMARY KEY (tag_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化按标签筛选文档）
    INDEX idx_doc_keyword (doc_id, keyword),
    INDEX idx_keyword (keyword) -- 按关键词检索关联文档
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档标签表';


CREATE TABLE IF NOT EXISTS doc_entity (
    entity_id VARCHAR(32) NOT NULL COMMENT '唯一实体ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    name VARCHAR(100) NOT NULL COMMENT '实体名称（如：BART模型、TF-IDF算法）',
    type VARCHAR(50) NOT NULL COMMENT '实体类型：算法/数据集/任务/公式等',
    recognize_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '识别时间',
    -- 约束
    PRIMARY KEY (entity_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化实体查询、图谱关联）
    INDEX idx_doc_entity (doc_id, name),
    INDEX idx_entity_type (type) -- 按实体类型筛选
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档实体表（关联Neo4j图谱）';

CREATE TABLE IF NOT EXISTS sys_operation_log (
    log_id VARCHAR(32) NOT NULL COMMENT '唯一日志ID（UUID生成）',
    user_id VARCHAR(32) NOT NULL COMMENT '操作人ID（关联sys_user.user_id）',
    doc_id VARCHAR(32) DEFAULT NULL COMMENT '关联文档ID（无则为NULL）',
    operation_type VARCHAR(20) NOT NULL COMMENT '操作类型：upload/export/annotate/delete',
    operation_result VARCHAR(20) NOT NULL COMMENT '操作结果：success/fail',
    operation_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    device_info VARCHAR(255) DEFAULT NULL COMMENT '操作设备（如：Chrome-Windows11）',
    error_msg TEXT DEFAULT NULL COMMENT '失败原因（成功则为NULL）',
    -- 约束
    PRIMARY KEY (log_id),
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化日志查询、数据统计）
    INDEX idx_user_time (user_id, operation_time),
    INDEX idx_operation_type (operation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统操作日志表';

-- 6.2 文本解析与内容提取 - 图片和表格存储
CREATE TABLE IF NOT EXISTS doc_media (
    media_id VARCHAR(32) NOT NULL COMMENT '唯一媒体ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    media_type VARCHAR(10) NOT NULL COMMENT '媒体类型：image/table',
    file_name VARCHAR(255) NOT NULL COMMENT '媒体文件名',
    file_path VARCHAR(512) NOT NULL COMMENT '媒体存储路径',
    file_size BIGINT DEFAULT NULL COMMENT '文件大小（字节）',
    page_number INT DEFAULT NULL COMMENT '所在页码',
    position_info TEXT DEFAULT NULL COMMENT '位置信息（JSON格式：x,y,width,height）',
    extract_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '提取时间',
    description TEXT DEFAULT NULL COMMENT '媒体描述（AI生成或用户编辑）',
    -- 约束
    PRIMARY KEY (media_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化媒体查询）
    INDEX idx_doc_media_type (doc_id, media_type),
    INDEX idx_page_number (page_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档媒体资源表（图片/表格）';

-- 6.2 文本解析与内容提取 - OCR结果存储
CREATE TABLE IF NOT EXISTS doc_ocr_result (
    ocr_id VARCHAR(32) NOT NULL COMMENT '唯一OCR结果ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    page_number INT NOT NULL COMMENT '页码',
    raw_text TEXT NOT NULL COMMENT 'OCR识别的原始文本',
    confidence_score DECIMAL(5,2) DEFAULT NULL COMMENT '识别置信度（0-100）',
    language VARCHAR(10) DEFAULT 'zh' COMMENT '识别语言：zh/en等',
    process_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '处理时间',
    bbox_data TEXT DEFAULT NULL COMMENT '文本边界框数据（JSON格式）',
    -- 约束
    PRIMARY KEY (ocr_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化OCR查询）
    INDEX idx_doc_page (doc_id, page_number),
    INDEX idx_confidence (confidence_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档OCR识别结果表';

-- 6.4.2 关系图谱生成 - 实体关系存储
CREATE TABLE IF NOT EXISTS entity_relation (
    relation_id VARCHAR(32) NOT NULL COMMENT '唯一关系ID（UUID生成）',
    source_entity_id VARCHAR(32) NOT NULL COMMENT '源实体ID（关联doc_entity.entity_id）',
    target_entity_id VARCHAR(32) NOT NULL COMMENT '目标实体ID（关联doc_entity.entity_id）',
    relation_type VARCHAR(50) NOT NULL COMMENT '关系类型：uses/contains/implements/refers_to等',
    confidence_score DECIMAL(5,2) DEFAULT NULL COMMENT '关系置信度（0-100）',
    source_doc_id VARCHAR(32) DEFAULT NULL COMMENT '来源文档ID（关联doc_document.doc_id）',
    evidence_text TEXT DEFAULT NULL COMMENT '证据文本片段',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    is_manual TINYINT DEFAULT 0 COMMENT '是否人工标注：0-自动生成，1-人工标注',
    -- 约束
    PRIMARY KEY (relation_id),
    FOREIGN KEY (source_entity_id) REFERENCES doc_entity (entity_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES doc_entity (entity_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (source_doc_id) REFERENCES doc_document (doc_id) ON DELETE SET NULL ON UPDATE CASCADE,
    -- 索引（优化关系查询）
    INDEX idx_source_entity (source_entity_id, relation_type),
    INDEX idx_target_entity (target_entity_id, relation_type),
    INDEX idx_doc_relation (source_doc_id, relation_type),
    INDEX idx_confidence (confidence_score),
    -- 避免重复关系的唯一约束
    UNIQUE KEY uk_relation_unique (source_entity_id, target_entity_id, relation_type, evidence_text(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实体关系表（支持图谱构建）';

-- 6.6 内容导出 - 导出管理
CREATE TABLE IF NOT EXISTS doc_export (
    export_id VARCHAR(32) NOT NULL COMMENT '唯一导出ID（UUID生成）',
    user_id VARCHAR(32) NOT NULL COMMENT '用户ID（关联sys_user.user_id）',
    export_type VARCHAR(20) NOT NULL COMMENT '导出类型：graph/summary/document/tags',
    format VARCHAR(10) NOT NULL COMMENT '导出格式：png/jpg/pdf/html/json',
    doc_ids TEXT DEFAULT NULL COMMENT '关联文档ID列表（JSON数组）',
    file_path VARCHAR(512) DEFAULT NULL COMMENT '导出文件路径',
    file_size BIGINT DEFAULT NULL COMMENT '导出文件大小（字节）',
    export_params TEXT DEFAULT NULL COMMENT '导出参数（JSON格式：分辨率、样式等）',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '导出状态：pending/processing/completed/failed',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    complete_time DATETIME DEFAULT NULL COMMENT '完成时间',
    error_msg TEXT DEFAULT NULL COMMENT '错误信息（失败时记录）',
    download_count INT DEFAULT 0 COMMENT '下载次数',
    -- 约束
    PRIMARY KEY (export_id),
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    -- 索引（优化导出查询）
    INDEX idx_user_status (user_id, status),
    INDEX idx_create_time (create_time),
    INDEX idx_export_type (export_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档导出管理表';

-- 字段元数据管理表
CREATE TABLE IF NOT EXISTS sys_field_metadata (
    field_id VARCHAR(32) NOT NULL COMMENT '唯一字段ID（UUID生成）',
    table_name VARCHAR(64) NOT NULL COMMENT '表名',
    field_name VARCHAR(64) NOT NULL COMMENT '字段名',
    field_type VARCHAR(32) NOT NULL COMMENT '字段类型：string/int/decimal/datetime/text等',
    field_length INT DEFAULT NULL COMMENT '字段长度',
    field_label VARCHAR(100) NOT NULL COMMENT '字段显示标签（中文描述）',
    field_description TEXT DEFAULT NULL COMMENT '字段详细描述',
    is_required TINYINT DEFAULT 0 COMMENT '是否必填：0-否，1-是',
    is_searchable TINYINT DEFAULT 0 COMMENT '是否可搜索：0-否，1-是',
    is_display TINYINT DEFAULT 1 COMMENT '是否显示：0-否，1-是',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    default_value TEXT DEFAULT NULL COMMENT '默认值',
    validation_rule TEXT DEFAULT NULL COMMENT '验证规则（JSON格式）',
    input_type VARCHAR(20) DEFAULT 'text' COMMENT '输入类型：text/select/textarea/date等',
    select_options TEXT DEFAULT NULL COMMENT '选择项（JSON格式，用于select类型）',
    is_primary_key TINYINT DEFAULT 0 COMMENT '是否主键：0-否，1-是',
    is_foreign_key TINYINT DEFAULT 0 COMMENT '是否外键：0-否，1-是',
    foreign_table VARCHAR(64) DEFAULT NULL COMMENT '外键关联表',
    foreign_field VARCHAR(64) DEFAULT NULL COMMENT '外键关联字段',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 约束
    PRIMARY KEY (field_id),
    UNIQUE KEY uk_table_field (table_name, field_name), -- 表名+字段名唯一
    -- 索引（优化字段查询）
    INDEX idx_table_name (table_name),
    INDEX idx_field_name (field_name),
    INDEX idx_is_display (is_display),
    INDEX idx_display_order (display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='字段元数据表';

-- 表元数据管理表
CREATE TABLE IF NOT EXISTS sys_table_metadata (
    table_id VARCHAR(32) NOT NULL COMMENT '唯一表ID（UUID生成）',
    table_name VARCHAR(64) NOT NULL COMMENT '表名',
    table_label VARCHAR(100) NOT NULL COMMENT '表显示标签（中文描述）',
    table_description TEXT DEFAULT NULL COMMENT '表详细描述',
    module_name VARCHAR(50) DEFAULT NULL COMMENT '所属模块名称',
    is_system TINYINT DEFAULT 0 COMMENT '是否系统表：0-否，1-是',
    table_type VARCHAR(20) DEFAULT 'business' COMMENT '表类型：business/system/log/config等',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    -- 约束
    PRIMARY KEY (table_id),
    UNIQUE KEY uk_table_name (table_name), -- 表名唯一
    -- 索引（优化表查询）
    INDEX idx_module_name (module_name),
    INDEX idx_table_type (table_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表元数据表';

-- ============================================
-- 触发器：自动同步字段元数据更新
-- ============================================

-- 监听sys_user表结构变更的触发器
DELIMITER //
CREATE TRIGGER IF NOT EXISTS tr_sys_user_metadata_update
AFTER UPDATE ON sys_user
FOR EACH ROW
BEGIN
    -- 当user_id发生变化时，更新字段元数据中的相关信息
    IF OLD.user_id != NEW.user_id THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            field_description = CONCAT(
                COALESCE(field_description, ''), 
                IF(field_description IS NULL OR field_description = '', '', '\n'),
                '用户ID于', DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'), '从', OLD.user_id, '更新为', NEW.user_id
            )
        WHERE table_name = 'sys_user' AND field_name = 'user_id';
    END IF;
    
    -- 当字段属性发生变化时，同步更新元数据
    IF OLD.role != NEW.role THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            field_description = CONCAT(
                COALESCE(field_description, ''), 
                IF(field_description IS NULL OR field_description = '', '', '\n'),
                '角色字段默认值于', DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'), '更新'
            )
        WHERE table_name = 'sys_user' AND field_name = 'role';
    END IF;
    
    IF OLD.status != NEW.status THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            default_value = CAST(NEW.status AS CHAR)
        WHERE table_name = 'sys_user' AND field_name = 'status';
    END IF;
    
    IF OLD.theme != NEW.theme THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            default_value = NEW.theme
        WHERE table_name = 'sys_user' AND field_name = 'theme';
    END IF;
    
    IF OLD.summary_length != NEW.summary_length THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            default_value = NEW.summary_length
        WHERE table_name = 'sys_user' AND field_name = 'summary_length';
    END IF;
END//
DELIMITER ;

-- 监听doc_document表结构变更的触发器
DELIMITER //
CREATE TRIGGER IF NOT EXISTS tr_doc_document_metadata_update
AFTER UPDATE ON doc_document
FOR EACH ROW
BEGIN
    -- 当user_id发生变化时，更新字段元数据
    IF OLD.user_id != NEW.user_id THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            field_description = CONCAT(
                COALESCE(field_description, ''), 
                IF(field_description IS NULL OR field_description = '', '', '\n'),
                '文档用户关联于', DATE_FORMAT(NOW(), '%Y-%m-%d %H:%i:%s'), '从', OLD.user_id, '更新为', NEW.user_id
            )
        WHERE table_name = 'doc_document' AND field_name = 'user_id';
    END IF;
    
    -- 当文件格式发生变化时
    IF OLD.file_format != NEW.file_format THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP,
            default_value = NEW.file_format
        WHERE table_name = 'doc_document' AND field_name = 'file_format';
    END IF;
    
    -- 当分类发生变化时
    IF OLD.category != NEW.category THEN
        UPDATE sys_field_metadata 
        SET update_time = CURRENT_TIMESTAMP
        WHERE table_name = 'doc_document' AND field_name = 'category';
    END IF;
END//
DELIMITER ;

-- ============================================
-- 存储过程：批量更新字段元数据
-- ============================================

DELIMITER //
CREATE PROCEDURE IF NOT EXISTS sp_sync_field_metadata(
    IN p_table_name VARCHAR(64),
    IN p_operation VARCHAR(20) -- 'CREATE', 'ALTER', 'DROP'
)
BEGIN
    DECLARE v_field_count INT DEFAULT 0;
    
    IF p_operation = 'CREATE' THEN
        -- 创建表时，自动初始化字段元数据
        INSERT IGNORE INTO sys_field_metadata (
            field_id, table_name, field_name, field_type, field_label,
            is_primary_key, is_foreign_key, foreign_table, foreign_field, create_time
        )
        SELECT 
            UUID(),
            p_table_name,
            COLUMN_NAME,
            CASE 
                WHEN DATA_TYPE = 'varchar' THEN 'string'
                WHEN DATA_TYPE = 'int' THEN 'int'
                WHEN DATA_TYPE = 'bigint' THEN 'int'
                WHEN DATA_TYPE = 'decimal' THEN 'decimal'
                WHEN DATA_TYPE = 'datetime' THEN 'datetime'
                WHEN DATA_TYPE = 'text' THEN 'text'
                WHEN DATA_TYPE = 'tinyint' THEN 'int'
                ELSE DATA_TYPE
            END,
            CONCAT(
                CASE COLUMN_NAME
                    WHEN 'user_id' THEN '用户ID'
                    WHEN 'username' THEN '用户名'
                    WHEN 'email' THEN '邮箱'
                    WHEN 'password' THEN '密码'
                    WHEN 'role' THEN '用户角色'
                    WHEN 'status' THEN '账号状态'
                    WHEN 'theme' THEN '界面主题'
                    WHEN 'summary_length' THEN '摘要长度偏好'
                    WHEN 'doc_id' THEN '文档ID'
                    WHEN 'title' THEN '文档标题'
                    WHEN 'author' THEN '文档作者'
                    WHEN 'file_path' THEN '文件路径'
                    WHEN 'file_size' THEN '文件大小'
                    WHEN 'file_format' THEN '文件格式'
                    WHEN 'category' THEN '文档分类'
                    WHEN 'is_deleted' THEN '逻辑删除'
                    ELSE COLUMN_NAME
                END,
                '（', 
                CASE 
                    WHEN IS_NULLABLE = 'NO' THEN '必填'
                    ELSE '可选'
                END,
                '）'
            ),
            CASE COLUMN_KEY WHEN 'PRI' THEN 1 ELSE 0 END,
            CASE 
                WHEN COLUMN_NAME LIKE '%_id' AND COLUMN_NAME != (SELECT SUBSTRING(TABLE_NAME, 5) FROM information_schema.TABLES WHERE TABLE_NAME = p_table_name LIMIT 1) THEN 1
                ELSE 0
            END,
            CASE 
                WHEN COLUMN_NAME = 'user_id' THEN 'sys_user'
                WHEN COLUMN_NAME = 'doc_id' THEN 'doc_document'
                WHEN COLUMN_NAME = 'summary_id' THEN 'doc_summary'
                WHEN COLUMN_NAME = 'tag_id' THEN 'doc_tag'
                WHEN COLUMN_NAME = 'entity_id' THEN 'doc_entity'
                WHEN COLUMN_NAME = 'log_id' THEN 'sys_operation_log'
                WHEN COLUMN_NAME = 'export_id' THEN 'doc_export'
                WHEN COLUMN_NAME = 'media_id' THEN 'doc_media'
                WHEN COLUMN_NAME = 'ocr_id' THEN 'doc_ocr_result'
                WHEN COLUMN_NAME = 'relation_id' THEN 'entity_relation'
                WHEN COLUMN_NAME = 'field_id' THEN 'sys_field_metadata'
                WHEN COLUMN_NAME = 'table_id' THEN 'sys_table_metadata'
                ELSE NULL
            END,
            'id',
            NOW()
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = p_table_name;
        
    ELSEIF p_operation = 'DROP' THEN
        -- 删除表时，清理相关字段元数据
        DELETE FROM sys_field_metadata WHERE table_name = p_table_name;
        
    END IF;
END//
DELIMITER ;

-- ============================================
-- 初始化字段元数据数据
-- ============================================

-- 初始化sys_user表的字段元数据
INSERT IGNORE INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_label, field_description, is_required, is_primary_key, is_foreign_key, foreign_table, foreign_field, create_time) VALUES
(UUID(), 'sys_user', 'user_id', 'string', '用户ID', '唯一用户标识，UUID生成', 1, 1, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'username', 'string', '用户名', '用户登录名，不可重复', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'email', 'string', '邮箱', '登录账号，邮箱格式，不可重复', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'password', 'string', '密码', '用户登录密码，加密存储', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'role', 'string', '用户角色', '用户角色：普通用户/科研人员/教师/管理员', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'status', 'int', '账号状态', '账号状态：1-正常，0-禁用', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'theme', 'string', '界面主题', '界面主题：light-日间，dark-夜间', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'summary_length', 'string', '摘要长度偏好', '摘要长度偏好：short/medium/long', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'create_time', 'datetime', '注册时间', '用户注册时间', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'sys_user', 'update_time', 'datetime', '最后修改时间', '用户信息最后修改时间', 0, 0, 0, NULL, NULL, NOW());

-- 初始化doc_document表的字段元数据
INSERT IGNORE INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_label, field_description, is_required, is_primary_key, is_foreign_key, foreign_table, foreign_field, create_time) VALUES
(UUID(), 'doc_document', 'doc_id', 'string', '文档ID', '唯一文档标识，UUID生成', 1, 1, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'user_id', 'string', '所属用户ID', '文档所属用户的ID，关联sys_user表', 1, 0, 1, 'sys_user', 'user_id', NOW()),
(UUID(), 'doc_document', 'title', 'string', '文档标题', '文档标题，解析自PDF或用户修改', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'author', 'string', '文档作者', '文档作者，解析自PDF', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'upload_date', 'datetime', '上传时间', '文档上传时间', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'file_path', 'string', '文件路径', '文档存储路径，云端URL或本地路径', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'file_size', 'int', '文件大小', '文档大小，单位：字节', 1, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'file_format', 'string', '文件格式', '文档格式，仅支持PDF', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'category', 'string', '文档分类', '文档分类，用户自定义：如课程论文/科研文献', 0, 0, 0, NULL, NULL, NOW()),
(UUID(), 'doc_document', 'is_deleted', 'int', '逻辑删除', '逻辑删除标记：0-未删除，1-已删除', 0, 0, 0, NULL, NULL, NOW());

-- 初始化表元数据数据
INSERT IGNORE INTO sys_table_metadata (table_id, table_name, table_label, table_description, module_name, is_system, table_type, create_time) VALUES
(UUID(), 'sys_user', '用户表', '用户基础信息表，存储用户的基本账户信息和偏好设置', '用户管理', 1, 'business', NOW()),
(UUID(), 'doc_document', '文档表', '文档元信息表，存储PDF文档的基本信息和元数据', '文档管理', 0, 'business', NOW()),
(UUID(), 'doc_summary', '文档摘要表', '文档摘要表，存储AI生成的文档摘要内容', '文档处理', 0, 'business', NOW()),
(UUID(), 'doc_tag', '文档标签表', '文档标签表，存储从文档中提取的关键词标签', '文档处理', 0, 'business', NOW()),
(UUID(), 'doc_entity', '文档实体表', '文档实体表，存储从文档中识别的实体信息', '文档处理', 0, 'business', NOW()),
(UUID(), 'sys_operation_log', '操作日志表', '系统操作日志表，记录用户的所有操作行为', '系统管理', 1, 'log', NOW()),
(UUID(), 'doc_media', '媒体资源表', '文档媒体资源表，存储从PDF中提取的图片和表格', '文档处理', 0, 'business', NOW()),
(UUID(), 'doc_ocr_result', 'OCR结果表', '文档OCR识别结果表，存储文本识别结果', '文档处理', 0, 'business', NOW()),
(UUID(), 'entity_relation', '实体关系表', '实体关系表，存储实体间的关系信息，支持知识图谱构建', '文档处理', 0, 'business', NOW()),
(UUID(), 'doc_export', '导出管理表', '文档导出管理表，管理用户的导出任务和结果', '文档管理', 0, 'business', NOW()),
(UUID(), 'sys_field_metadata', '字段元数据表', '字段元数据表，管理数据库字段的元信息', '系统管理', 1, 'metadata', NOW()),
(UUID(), 'sys_table_metadata', '表元数据表', '表元数据表，管理数据库表的元信息', '系统管理', 1, 'metadata', NOW());

-- ============================================
-- 视图：字段依赖关系视图
-- ============================================

CREATE OR REPLACE VIEW v_field_dependencies AS
SELECT 
    t1.table_name AS source_table,
    t1.field_name AS source_field,
    t1.foreign_table AS target_table,
    t1.foreign_field AS target_field,
    t2.table_label AS target_table_label,
    '外键依赖' AS dependency_type,
    '级联更新和级联删除' AS cascade_action
FROM sys_field_metadata t1
LEFT JOIN sys_table_metadata t2 ON t1.foreign_table = t2.table_name
WHERE t1.is_foreign_key = 1 AND t1.foreign_table IS NOT NULL
UNION ALL
SELECT 
    'sys_user' AS source_table,
    'user_id' AS source_field,
    t.table_name AS target_table,
    'user_id' AS target_field,
    t.table_label AS target_table_label,
    '主键依赖' AS dependency_type,
    '当用户ID更新时，所有关联表的user_id会自动更新；当用户删除时，所有关联记录会自动删除' AS cascade_action
FROM sys_table_metadata t
WHERE t.table_name IN ('doc_document', 'sys_operation_log', 'doc_export');

-- ============================================
-- 函数：检查字段依赖关系
-- ============================================

DELIMITER //
CREATE FUNCTION IF NOT EXISTS fn_check_field_dependencies(
    p_table_name VARCHAR(64),
    p_field_name VARCHAR(64)
) RETURNS TEXT
READS SQL DATA
DETERMINISTIC
BEGIN
    DECLARE v_result TEXT DEFAULT '';
    DECLARE v_dependency_count INT DEFAULT 0;
    
    -- 检查该字段是否被其他表作为外键引用
    SELECT COUNT(*) INTO v_dependency_count
    FROM sys_field_metadata
    WHERE foreign_table = p_table_name AND foreign_field = p_field_name;
    
    IF v_dependency_count > 0 THEN
        SET v_result = CONCAT(
            '字段 ', p_table_name, '.', p_field_name, ' 被 ', v_dependency_count, ' 个其他表作为外键引用。'
        );
        
        -- 获取具体的依赖表信息
        SELECT GROUP_CONCAT(CONCAT(table_name, '.', field_name) SEPARATOR ', ') INTO v_result
        FROM (
            SELECT CONCAT(table_name, '.', field_name) AS dependency
            FROM sys_field_metadata
            WHERE foreign_table = p_table_name AND foreign_field = p_field_name
        ) AS deps;
        
        SET v_result = CONCAT(v_result, ' 依赖表：', v_result);
    ELSE
        SET v_result = CONCAT('字段 ', p_table_name, '.', p_field_name, ' 没有被其他表作为外键引用。');
    END IF;
    
    RETURN v_result;
END//
DELIMITER ;
