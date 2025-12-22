-- ==============================================
-- 00_init_all.sql - Docker MySQL 初始化脚本
-- 整合所有初始化步骤，确保正确执行顺序
-- ==============================================

-- 1. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS rjgc
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE rjgc;

SET sql_mode = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';

-- ==============================================
-- 2. 创建表结构
-- ==============================================

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
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_email (email),
    UNIQUE KEY uk_username (username),
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
    PRIMARY KEY (doc_id),
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_user_deleted (user_id, is_deleted),
    INDEX idx_title (title),
    INDEX idx_author (author)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档元信息表';

CREATE TABLE IF NOT EXISTS doc_summary (
    summary_id VARCHAR(32) NOT NULL COMMENT '唯一摘要ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    content TEXT NOT NULL COMMENT '摘要内容（若过长可存文件，此处存核心摘要）',
    length_type VARCHAR(10) NOT NULL COMMENT '摘要长度类型：short/medium/long',
    generate_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '生成时间',
    PRIMARY KEY (summary_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_length_type (length_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档摘要表';

CREATE TABLE IF NOT EXISTS doc_tag (
    tag_id VARCHAR(32) NOT NULL COMMENT '唯一标签ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    tag_name VARCHAR(50) NOT NULL COMMENT '标签名称',
    tag_type VARCHAR(20) DEFAULT 'keyword' COMMENT '标签类型：keyword（关键词）/category（分类）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (tag_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_tag_name (tag_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档标签表';

CREATE TABLE IF NOT EXISTS doc_entity (
    entity_id VARCHAR(32) NOT NULL COMMENT '唯一实体ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    name VARCHAR(255) NOT NULL COMMENT '实体名称',
    type VARCHAR(50) NOT NULL COMMENT '实体类型：algorithm/model/dataset/metric/task/method/person/organization/location/date/other',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (entity_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_name (name),
    INDEX idx_type (type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档实体表';

CREATE TABLE IF NOT EXISTS entity_relation (
    relation_id VARCHAR(32) NOT NULL COMMENT '唯一关系ID（UUID生成）',
    source_entity_id VARCHAR(32) NOT NULL COMMENT '源实体ID（关联doc_entity.entity_id）',
    target_entity_id VARCHAR(32) NOT NULL COMMENT '目标实体ID（关联doc_entity.entity_id）',
    relation_type VARCHAR(50) NOT NULL COMMENT '关系类型：uses/improves/compares/based_on/evaluates_on/other',
    confidence DECIMAL(4,3) DEFAULT 1.000 COMMENT '关系置信度（0-1）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (relation_id),
    FOREIGN KEY (source_entity_id) REFERENCES doc_entity (entity_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (target_entity_id) REFERENCES doc_entity (entity_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_source (source_entity_id),
    INDEX idx_target (target_entity_id),
    INDEX idx_type (relation_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='实体关系表';

CREATE TABLE IF NOT EXISTS doc_media (
    media_id VARCHAR(32) NOT NULL COMMENT '唯一媒体ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    media_type VARCHAR(20) NOT NULL COMMENT '媒体类型：image/table',
    file_path VARCHAR(512) NOT NULL COMMENT '媒体文件存储路径',
    page_number INT DEFAULT NULL COMMENT '所在PDF页码',
    caption TEXT DEFAULT NULL COMMENT '媒体标题/描述',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (media_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_media_type (media_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档媒体表（图片、表格）';

CREATE TABLE IF NOT EXISTS doc_ocr_result (
    ocr_id VARCHAR(32) NOT NULL COMMENT '唯一OCR记录ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    page_number INT NOT NULL COMMENT 'PDF页码',
    text_content LONGTEXT NOT NULL COMMENT 'OCR识别的文本内容',
    confidence DECIMAL(4,3) DEFAULT NULL COMMENT '识别置信度（0-1）',
    bounding_box JSON DEFAULT NULL COMMENT '文本区域坐标（JSON格式：{x, y, width, height}）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    PRIMARY KEY (ocr_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_page (page_number)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='OCR识别结果表';

CREATE TABLE IF NOT EXISTS sys_operation_log (
    log_id VARCHAR(32) NOT NULL COMMENT '唯一日志ID（UUID生成）',
    user_id VARCHAR(32) NOT NULL COMMENT '操作用户ID（关联sys_user.user_id）',
    doc_id VARCHAR(32) DEFAULT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    operation_type VARCHAR(20) NOT NULL COMMENT '操作类型：upload/export/annotate/delete/view/edit',
    operation_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    ip_address VARCHAR(45) DEFAULT NULL COMMENT '操作IP地址',
    details JSON DEFAULT NULL COMMENT '操作详情（JSON格式）',
    PRIMARY KEY (log_id),
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_doc_id (doc_id),
    INDEX idx_operation_time (operation_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户操作日志表';

CREATE TABLE IF NOT EXISTS doc_export (
    export_id VARCHAR(32) NOT NULL COMMENT '唯一导出记录ID（UUID生成）',
    doc_id VARCHAR(32) NOT NULL COMMENT '关联文档ID（关联doc_document.doc_id）',
    user_id VARCHAR(32) NOT NULL COMMENT '导出用户ID（关联sys_user.user_id）',
    export_type VARCHAR(20) NOT NULL COMMENT '导出类型：graph/summary/tags/full',
    export_format VARCHAR(10) NOT NULL COMMENT '导出格式：json/csv/txt/pdf',
    file_path VARCHAR(512) DEFAULT NULL COMMENT '导出文件存储路径',
    export_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '导出时间',
    status VARCHAR(20) DEFAULT 'pending' COMMENT '导出状态：pending/processing/completed/failed',
    PRIMARY KEY (export_id),
    FOREIGN KEY (doc_id) REFERENCES doc_document (doc_id) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (user_id) REFERENCES sys_user (user_id) ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_doc_id (doc_id),
    INDEX idx_user_id (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='文档导出记录表';

CREATE TABLE IF NOT EXISTS sys_field_metadata (
    field_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '字段元数据ID',
    table_name VARCHAR(50) NOT NULL COMMENT '所属表名',
    field_name VARCHAR(50) NOT NULL COMMENT '字段名',
    field_label VARCHAR(100) NOT NULL COMMENT '字段中文标签',
    field_type VARCHAR(20) NOT NULL COMMENT '字段类型：text/number/date/select/boolean',
    is_required TINYINT DEFAULT 0 COMMENT '是否必填：0-否，1-是',
    is_visible TINYINT DEFAULT 1 COMMENT '是否显示：0-否，1-是',
    is_editable TINYINT DEFAULT 1 COMMENT '是否可编辑：0-否，1-是',
    display_order INT DEFAULT 0 COMMENT '显示顺序',
    default_value VARCHAR(255) DEFAULT NULL COMMENT '默认值',
    options JSON DEFAULT NULL COMMENT '选项列表（JSON格式，用于select类型）',
    validation_rules JSON DEFAULT NULL COMMENT '验证规则（JSON格式）',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_table_field (table_name, field_name),
    INDEX idx_table_name (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='字段元数据表';

CREATE TABLE IF NOT EXISTS sys_table_metadata (
    table_id INT AUTO_INCREMENT PRIMARY KEY COMMENT '表元数据ID',
    table_name VARCHAR(50) NOT NULL COMMENT '表名',
    table_label VARCHAR(100) NOT NULL COMMENT '表中文名',
    description TEXT DEFAULT NULL COMMENT '表描述',
    is_system TINYINT DEFAULT 0 COMMENT '是否系统表：0-否，1-是',
    create_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    update_time DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    UNIQUE KEY uk_table_name (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='表元数据表';

-- ==============================================
-- 3. 初始化字段元数据
-- ==============================================

-- 表元数据
INSERT IGNORE INTO sys_table_metadata (table_name, table_label, description, is_system) VALUES
('sys_user', '用户信息表', '存储系统用户的基本信息和配置', 1),
('doc_document', '文档信息表', '存储上传的PDF文档元信息', 0),
('doc_summary', '文档摘要表', '存储文档的AI生成摘要', 0),
('doc_tag', '文档标签表', '存储文档的关键词和分类标签', 0),
('doc_entity', '文档实体表', '存储从文档中提取的命名实体', 0),
('entity_relation', '实体关系表', '存储实体之间的关系', 0),
('doc_media', '文档媒体表', '存储从文档中提取的图片和表格', 0),
('doc_ocr_result', 'OCR识别结果表', '存储PDF页面的OCR识别结果', 0),
('sys_operation_log', '操作日志表', '记录用户操作历史', 1),
('doc_export', '导出记录表', '记录文档导出任务', 0);

-- 用户表字段元数据
INSERT IGNORE INTO sys_field_metadata (table_name, field_name, field_label, field_type, is_required, is_visible, is_editable, display_order, options) VALUES
('sys_user', 'user_id', '用户ID', 'text', 1, 1, 0, 1, NULL),
('sys_user', 'username', '用户名', 'text', 1, 1, 1, 2, NULL),
('sys_user', 'email', '邮箱', 'text', 1, 1, 1, 3, NULL),
('sys_user', 'password', '密码', 'password', 1, 0, 1, 4, NULL),
('sys_user', 'role', '角色', 'select', 1, 1, 1, 5, '["普通用户", "科研人员", "教师", "管理员"]'),
('sys_user', 'status', '状态', 'select', 1, 1, 1, 6, '[{"value": 1, "label": "正常"}, {"value": 0, "label": "禁用"}]'),
('sys_user', 'theme', '主题', 'select', 0, 1, 1, 7, '["light", "dark"]'),
('sys_user', 'summary_length', '摘要长度偏好', 'select', 0, 1, 1, 8, '["short", "medium", "long"]');

-- 文档表字段元数据
INSERT IGNORE INTO sys_field_metadata (table_name, field_name, field_label, field_type, is_required, is_visible, is_editable, display_order, options) VALUES
('doc_document', 'doc_id', '文档ID', 'text', 1, 1, 0, 1, NULL),
('doc_document', 'user_id', '所属用户', 'text', 1, 1, 0, 2, NULL),
('doc_document', 'title', '文档标题', 'text', 1, 1, 1, 3, NULL),
('doc_document', 'author', '作者', 'text', 0, 1, 1, 4, NULL),
('doc_document', 'upload_date', '上传时间', 'date', 1, 1, 0, 5, NULL),
('doc_document', 'file_path', '文件路径', 'text', 1, 0, 0, 6, NULL),
('doc_document', 'file_size', '文件大小', 'number', 1, 1, 0, 7, NULL),
('doc_document', 'category', '分类', 'text', 0, 1, 1, 8, NULL);

-- 实体表字段元数据
INSERT IGNORE INTO sys_field_metadata (table_name, field_name, field_label, field_type, is_required, is_visible, is_editable, display_order, options) VALUES
('doc_entity', 'entity_id', '实体ID', 'text', 1, 1, 0, 1, NULL),
('doc_entity', 'doc_id', '关联文档', 'text', 1, 1, 0, 2, NULL),
('doc_entity', 'name', '实体名称', 'text', 1, 1, 1, 3, NULL),
('doc_entity', 'type', '实体类型', 'select', 1, 1, 1, 4, '["algorithm", "model", "dataset", "metric", "task", "method", "person", "organization", "location", "date", "other"]');

-- ==============================================
-- 4. 插入测试数据（可选）
-- ==============================================

-- 插入测试用户
INSERT IGNORE INTO sys_user (user_id, username, email, password, role, status, theme, summary_length) VALUES
('user_001', 'admin', 'admin@example.com', 'admin123', '管理员', 1, 'light', 'medium'),
('user_002', 'researcher', 'researcher@example.com', 'research123', '科研人员', 1, 'dark', 'long'),
('user_003', 'teacher', 'teacher@example.com', 'teacher123', '教师', 1, 'light', 'medium'),
('user_004', 'student', 'student@example.com', 'student123', '普通用户', 1, 'light', 'short'),
('user_005', 'test_user', 'test@example.com', 'test123', '普通用户', 1, 'light', 'medium');

-- 完成提示
SELECT 'Database initialization completed successfully!' AS message;
