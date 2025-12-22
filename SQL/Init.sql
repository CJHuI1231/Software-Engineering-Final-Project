
-- 插入测试用户
INSERT INTO sys_user (user_id, username, email, password, role, status) VALUES
('user_001', 'cjh', 'cjh@qq.com', '123456', '普通用户', 1),
('user_002', 'cdx', 'cdx@qq.com', '123456', '科研人员', 1),
('user_003', 'zsj', 'zsj@qq.com', '123456', '教师', 1),
('user_004', 'lt', 'lt@qq.com', '123456', '管理员', 1),
('user_005', 'ccb', 'ccb@qq.com', '123456', '普通用户', 1);

-- 插入测试文档
INSERT INTO doc_document (doc_id, user_id, title, author, upload_date, file_path, file_size, file_format, category) VALUES
('doc_001', 'user_001', 'Transient hepatic reconstitution of trophic factors enhances aged immunity', 'Mirco J. Friedrich1,', NOW(), '/pdf/doc_001.pdf', 2048576, 'pdf', '科研文献'),
('doc_002', 'user_002', 'The hidden cost of video-call glitches', 'J.R.R. and M.S.B.', NOW(), '/pdf/doc_002.pdf', 1536789, 'pdf', '科研文献');

-- 插入文档摘要
INSERT INTO doc_summary (summary_id, doc_id, content, length_type) VALUES
('sum_001', 'doc_001', '本文综述了深度学习在自然语言处理领域的最新进展，重点介绍了Transformer架构、BERT模型和GPT系列的发展历程。文章详细分析了这些技术在文本分类、情感分析、机器翻译等任务中的应用效果，并对未来发展趋势进行了展望。', 'medium'),
('sum_002', 'doc_002', '机器学习技术在医疗诊断领域展现出巨大潜力。本文系统综述了深度学习、支持向量机、随机森林等算法在疾病诊断、医学影像分析等方面的应用案例，分析了算法的优势与局限性，并讨论了临床应用面临的挑战。', 'medium');
-- 插入文档标签
INSERT INTO doc_tag (tag_id, doc_id, keyword, synonyms) VALUES
('tag_001', 'doc_001', '深度学习', '神经网络,机器学习'),
('tag_002', 'doc_001', '自然语言处理', 'NLP,文本处理'),
('tag_003', 'doc_001', 'Transformer', '注意力机制'),
('tag_004', 'doc_002', '机器学习', '人工智能,ML'),
('tag_005', 'doc_002', '医疗诊断', '医学影像,疾病诊断');

-- 插入文档实体
INSERT INTO doc_entity (entity_id, doc_id, name, type) VALUES
('ent_001', 'doc_001', 'Transformer', '算法'),
('ent_002', 'doc_001', 'BERT', '模型'),
('ent_003', 'doc_001', 'GPT', '模型'),
('ent_004', 'doc_002', '支持向量机', '算法'),
('ent_005', 'doc_002', '随机森林', '算法');

-- 插入媒体资源（示例）
INSERT INTO doc_media (media_id, doc_id, media_type, file_name, file_path, page_number) VALUES
('med_001', 'doc_001', 'image', 'transformer_architecture.png', '/media/transformer_architecture.png', 3),
('med_002', 'doc_001', 'table', 'performance_comparison.csv', '/media/performance_comparison.csv', 5);

-- 插入OCR结果（示例）
INSERT INTO doc_ocr_result (ocr_id, doc_id, page_number, raw_text, confidence_score, language) VALUES
('ocr_001', 'doc_001', 1, '知识图谱构建技术与方法研究', 98.5, 'zh');

-- 插入实体关系
INSERT INTO entity_relation (relation_id, source_entity_id, target_entity_id, relation_type, confidence_score, source_doc_id, is_manual) VALUES
('rel_001', 'ent_001', 'ent_002', 'implements', 95.0, 'doc_001', 0),
('rel_002', 'ent_001', 'ent_003', 'implements', 94.5, 'doc_001', 0),
('rel_003', 'ent_002', 'ent_003', 'similar_to', 88.0, 'doc_001', 0);

-- 插入操作日志
INSERT INTO sys_operation_log (log_id, user_id, doc_id, operation_type, operation_result, operation_time) VALUES
('log_001', 'user_001', 'doc_001', 'upload', 'success', NOW()),
('log_002', 'user_002', 'doc_002', 'upload', 'success', NOW()),
('log_005', 'user_001', 'doc_001', 'export', 'success', NOW());

-- 插入导出记录
INSERT INTO doc_export (export_id, user_id, export_type, format, doc_ids, file_path, status) VALUES
('exp_001', 'user_001', 'summary', 'pdf', '["doc_001"]', '/exports/summary_doc_001.pdf', 'completed'),
('exp_002', 'user_002', 'graph', 'png', '["doc_002"]', '/exports/graph_doc_002.png', 'completed'),
('exp_003', 'user_001', 'tags', 'json', '["doc_001","doc_003"]', '/exports/tags_batch.json', 'pending');

-- 验证插入结果
SELECT '用户表记录数:' as table_info, COUNT(*) as count FROM sys_user
UNION ALL
SELECT '文档表记录数:', COUNT(*) FROM doc_document
UNION ALL
SELECT '摘要表记录数:', COUNT(*) FROM doc_summary
UNION ALL
SELECT '标签表记录数:', COUNT(*) FROM doc_tag
UNION ALL
SELECT '实体表记录数:', COUNT(*) FROM doc_entity
UNION ALL
SELECT '媒体资源表记录数:', COUNT(*) FROM doc_media
UNION ALL
SELECT 'OCR结果表记录数:', COUNT(*) FROM doc_ocr_result
UNION ALL
SELECT '实体关系表记录数:', COUNT(*) FROM entity_relation
UNION ALL
SELECT '操作日志表记录数:', COUNT(*) FROM sys_operation_log
UNION ALL
SELECT '导出记录表记录数:', COUNT(*) FROM doc_export;
