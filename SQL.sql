-- 创建知识图谱三元组表
CREATE TABLE knowledge_triples (
    id INTEGER PRIMARY KEY AUTO_INCREMENT, -- 如果是MySQL请去掉 AUTOINCREMENT 改为 AUTO_INCREMENT
    head_entity VARCHAR(255) NOT NULL,    -- 头实体 (例如: 松材线虫)
    relation VARCHAR(255) NOT NULL,       -- 关系 (例如: 传播媒介)
    tail_entity VARCHAR(255) NOT NULL,    -- 尾实体 (例如: 褐梗天牛)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入一些松材线虫病领域的初始化测试数据
INSERT INTO knowledge_triples (head_entity, relation, tail_entity) VALUES 
('松材线虫', '引起', '松材线虫病'),
('松材线虫病', '别名', '松树萎蔫病'),
('褐梗天牛', '传播', '松材线虫'),
('松树', '易感', '松材线虫病'),
('松材线虫', '属于', '寄生线虫'),
('高温干旱', '加速', '松材线虫病扩散'),
('线虫', '入侵', '木质部'),
('药剂注射', '防治', '松材线虫病');

-- 创建一个存储所有可选关系的辅助表（用于限制AI生成关系时的范围）
CREATE TABLE valid_relations (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    relation_name VARCHAR(255) UNIQUE NOT NULL
);

-- 初始化允许的关系类型
INSERT INTO valid_relations (relation_name) VALUES 
('引起'), ('传播'), ('易感'), ('属于'), ('加速'), ('入侵'), ('防治'), ('别名');