-- 字段表初始化数据脚本
-- 为sys_field_metadata和sys_table_metadata表插入元数据

-- 1. 表元数据初始化
INSERT INTO sys_table_metadata (table_id, table_name, table_label, table_description, module_name, is_system, table_type) VALUES
('tbl_001', 'sys_user', '用户表', '系统用户基础信息，包括用户账号、角色、偏好设置等', '用户管理', 1, 'system'),
('tbl_002', 'doc_document', '文档表', '文档元信息表，存储PDF文档的基本信息和分类', '文档管理', 0, 'business'),
('tbl_003', 'doc_summary', '文档摘要表', '存储系统生成的文档摘要信息', '文档分析', 0, 'business'),
('tbl_004', 'doc_tag', '文档标签表', '存储文档的标签和关键词信息', '文档分析', 0, 'business'),
('tbl_005', 'doc_entity', '文档实体表', '存储从文档中识别的实体信息，用于知识图谱构建', '文档分析', 0, 'business'),
('tbl_006', 'doc_media', '媒体资源表', '存储从PDF中提取的图片和表格资源', '文档处理', 0, 'business'),
('tbl_007', 'doc_ocr_result', 'OCR结果表', '存储PDF扫描件的OCR识别结果', '文档处理', 0, 'business'),
('tbl_008', 'entity_relation', '实体关系表', '存储实体之间的关系，用于构建知识图谱', '知识图谱', 0, 'business'),
('tbl_009', 'sys_operation_log', '操作日志表', '记录用户在系统中的各种操作日志', '系统管理', 1, 'log'),
('tbl_010', 'doc_export', '导出管理表', '管理用户的导出任务和结果', '文档导出', 0, 'business'),
('tbl_011', 'sys_field_metadata', '字段元数据表', '管理系统中所有表的字段元数据信息', '系统管理', 1, 'config'),
('tbl_012', 'sys_table_metadata', '表元数据表', '管理系统中所有表的元数据信息', '系统管理', 1, 'config');

-- 2. sys_user表字段元数据
INSERT INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_length, field_label, field_description, is_required, is_searchable, is_display, display_order, input_type, is_primary_key) VALUES
('fld_001', 'sys_user', 'user_id', 'string', 32, '用户ID', '系统唯一用户标识，使用UUID生成', 1, 0, 0, 1, 'text', 1),
('fld_002', 'sys_user', 'username', 'string', 50, '用户名', '用户登录名，不可重复', 1, 1, 1, 2, 'text', 0),
('fld_003', 'sys_user', 'email', 'string', 100, '邮箱', '用户登录邮箱，也是账号标识', 1, 1, 1, 3, 'email', 0),
('fld_004', 'sys_user', 'password', 'string', 128, '密码', '用户登录密码，存储哈希值', 1, 0, 0, 4, 'password', 0),
('fld_005', 'sys_user', 'role', 'string', 20, '用户角色', '用户在系统中的角色：普通用户/科研人员/教师/管理员', 1, 1, 1, 5, 'select', 0),
('fld_006', 'sys_user', 'status', 'int', null, '账号状态', '用户账号状态：1-正常，0-禁用', 1, 1, 1, 6, 'select', 0),
('fld_007', 'sys_user', 'theme', 'string', 20, '界面主题', '用户界面主题偏好：light-日间，dark-夜间', 0, 0, 1, 7, 'select', 0),
('fld_008', 'sys_user', 'summary_length', 'string', 10, '摘要长度偏好', '用户偏好的摘要长度：short/medium/long', 0, 0, 1, 8, 'select', 0),
('fld_009', 'sys_user', 'create_time', 'datetime', null, '注册时间', '用户注册时间', 1, 1, 1, 9, 'datetime', 0),
('fld_010', 'sys_user', 'update_time', 'datetime', null, '最后修改时间', '用户信息最后修改时间', 1, 1, 1, 10, 'datetime', 0);

-- 3. doc_document表字段元数据
INSERT INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_length, field_label, field_description, is_required, is_searchable, is_display, display_order, input_type, is_primary_key, is_foreign_key, foreign_table, foreign_field) VALUES
('fld_011', 'doc_document', 'doc_id', 'string', 32, '文档ID', '文档唯一标识，使用UUID生成', 1, 0, 0, 1, 'text', 1, 0, null, null),
('fld_012', 'doc_document', 'user_id', 'string', 32, '所属用户ID', '文档所属的用户ID', 1, 1, 1, 2, 'select', 0, 1, 'sys_user', 'user_id'),
('fld_013', 'doc_document', 'title', 'string', 255, '文档标题', '文档标题，可从PDF解析或用户修改', 1, 1, 1, 3, 'text', 0, 0, null, null),
('fld_014', 'doc_document', 'author', 'string', 255, '文档作者', '文档作者信息，从PDF解析', 0, 1, 1, 4, 'text', 0, 0, null, null),
('fld_015', 'doc_document', 'upload_date', 'datetime', null, '上传时间', '文档上传时间', 1, 1, 1, 5, 'datetime', 0, 0, null, null),
('fld_016', 'doc_document', 'file_path', 'string', 512, '文件路径', '文档存储路径，可以是云端URL或本地路径', 1, 0, 0, 6, 'text', 0, 0, null, null),
('fld_017', 'doc_document', 'file_size', 'bigint', null, '文件大小', '文档文件大小，单位字节', 1, 0, 1, 7, 'number', 0, 0, null, null),
('fld_018', 'doc_document', 'file_format', 'string', 10, '文件格式', '文档格式，目前仅支持PDF', 0, 1, 1, 8, 'text', 0, 0, null, null),
('fld_019', 'doc_document', 'category', 'string', 50, '文档分类', '用户自定义的文档分类，如课程论文/科研文献', 0, 1, 1, 9, 'text', 0, 0, null, null),
('fld_020', 'doc_document', 'is_deleted', 'int', null, '逻辑删除', '是否已删除：0-未删除，1-已删除', 1, 0, 0, 10, 'select', 0, 0, null, null);

-- 4. doc_summary表字段元数据
INSERT INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_length, field_label, field_description, is_required, is_searchable, is_display, display_order, input_type, is_primary_key, is_foreign_key, foreign_table, foreign_field) VALUES
('fld_021', 'doc_summary', 'summary_id', 'string', 32, '摘要ID', '摘要唯一标识，使用UUID生成', 1, 0, 0, 1, 'text', 1, 0, null, null),
('fld_022', 'doc_summary', 'doc_id', 'string', 32, '关联文档ID', '关联的文档ID', 1, 0, 0, 2, 'select', 0, 1, 'doc_document', 'doc_id'),
('fld_023', 'doc_summary', 'content', 'text', null, '摘要内容', '系统生成的文档摘要内容', 1, 1, 1, 3, 'textarea', 0, 0, null, null),
('fld_024', 'doc_summary', 'length_type', 'string', 10, '摘要长度', '摘要长度类型：short/medium/long', 1, 1, 1, 4, 'select', 0, 0, null, null),
('fld_025', 'doc_summary', 'generate_time', 'datetime', null, '生成时间', '摘要生成时间', 1, 1, 1, 5, 'datetime', 0, 0, null, null);

-- 5. doc_tag表字段元数据
INSERT INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_length, field_label, field_description, is_required, is_searchable, is_display, display_order, input_type, is_primary_key, is_foreign_key, foreign_table, foreign_field) VALUES
('fld_026', 'doc_tag', 'tag_id', 'string', 32, '标签ID', '标签唯一标识，使用UUID生成', 1, 0, 0, 1, 'text', 1, 0, null, null),
('fld_027', 'doc_tag', 'doc_id', 'string', 32, '关联文档ID', '关联的文档ID', 1, 0, 0, 2, 'select', 0, 1, 'doc_document', 'doc_id'),
('fld_028', 'doc_tag', 'keyword', 'string', 50, '关键词', '标签关键词，如：机器学习、NLP', 1, 1, 1, 3, 'text', 0, 0, null, null),
('fld_029', 'doc_tag', 'synonyms', 'string', 255, '同义词', '关键词的同义词，多个用逗号分隔', 0, 1, 1, 4, 'text', 0, 0, null, null),
('fld_030', 'doc_tag', 'generate_time', 'datetime', null, '生成时间', '标签生成时间', 1, 1, 1, 5, 'datetime', 0, 0, null, null);

-- 6. doc_entity表字段元数据
INSERT INTO sys_field_metadata (field_id, table_name, field_name, field_type, field_length, field_label, field_description, is_required, is_searchable, is_display, display_order, input_type, is_primary_key, is_foreign_key, foreign_table, foreign_field) VALUES
('fld_031', 'doc_entity', 'entity_id', 'string', 32, '实体ID', '实体唯一标识，使用UUID生成', 1, 0, 0, 1, 'text', 1, 0, null, null),
('fld_032', 'doc_entity', 'doc_id', 'string', 32, '关联文档ID', '关联的文档ID', 1, 0, 0, 2, 'select', 0, 1, 'doc_document', 'doc_id'),
('fld_033', 'doc_entity', 'name', 'string', 100, '实体名称', '实体名称，如：BART模型、TF-IDF算法', 1, 1, 1, 3, 'text', 0, 0, null, null),
('fld_034', 'doc_entity', 'type', 'string', 50, '实体类型', '实体类型：算法/数据集/任务/公式等', 1, 1, 1, 4, 'select', 0, 0, null, null),
('fld_035', 'doc_entity', 'recognize_time', 'datetime', null, '识别时间', '实体识别时间', 1, 1, 1, 5, 'datetime', 0, 0, null, null);

-- 验证插入结果
SELECT '表元数据记录数:' as info, COUNT(*) as count FROM sys_table_metadata
UNION ALL
SELECT '字段元数据记录数:', COUNT(*) FROM sys_field_metadata
UNION ALL
SELECT '用户表字段数:', COUNT(*) FROM sys_field_metadata WHERE table_name = 'sys_user'
UNION ALL
SELECT '文档表字段数:', COUNT(*) FROM sys_field_metadata WHERE table_name = 'doc_document'
UNION ALL
SELECT '摘要表字段数:', COUNT(*) FROM sys_field_metadata WHERE table_name = 'doc_summary'
UNION ALL
SELECT '标签表字段数:', COUNT(*) FROM sys_field_metadata WHERE table_name = 'doc_tag'
UNION ALL
SELECT '实体表字段数:', COUNT(*) FROM sys_field_metadata WHERE table_name = 'doc_entity';
