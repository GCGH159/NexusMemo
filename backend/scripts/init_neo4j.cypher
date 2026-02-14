// Neo4j 图数据库初始化脚本
// 此脚本为 NexusMemo 设置索引、约束和初始架构

// ============================================================================
// 1. 节点索引
// ============================================================================

// 用户节点索引
CREATE INDEX FOR (u:User) ON (u.user_id) IF NOT EXISTS;

// 速记节点索引
CREATE INDEX FOR (m:Memo) ON (m.memo_id) IF NOT EXISTS;

// 事件节点索引
CREATE INDEX FOR (e:Event) ON (e.event_id) IF NOT EXISTS;

// 分类节点索引
CREATE INDEX FOR (c:Category) ON (c.name) IF NOT EXISTS;

// 标签节点索引
CREATE INDEX FOR (t:Tag) ON (t.name) IF NOT EXISTS;

// 实体节点索引
CREATE INDEX FOR (en:Entity) ON (en.name) IF NOT EXISTS;

// 时间段节点索引
CREATE INDEX FOR (tp:TimePeriod) ON (tp.date) IF NOT EXISTS;

// ============================================================================
// 2. 全文索引（用于搜索）
// ============================================================================

// 速记内容全文索引（标题和内容）
CREATE FULLTEXT INDEX memoContent 
FOR (m:Memo) ON EACH [m.title, m.content] 
OPTIONS {indexConfig: {`fulltext.analyzer`: 'standard'}}
IF NOT EXISTS;

// 事件内容全文索引（标题和描述）
CREATE FULLTEXT INDEX eventContent 
FOR (e:Event) ON EACH [e.title, e.description] 
OPTIONS {indexConfig: {`fulltext.analyzer`: 'standard'}}
IF NOT EXISTS;

// ============================================================================
// 3. 向量索引（用于语义搜索）
// ============================================================================

// 速记嵌入向量索引（1536维，适配OpenAI嵌入）
// 注意：需要 Neo4j 5.11+ 版本和图数据科学插件
CALL db.index.vector.createNodeIndex(
    'memo_embeddings', 
    'Memo', 
    'embedding', 
    1536, 
    'cosine'
) IF NOT EXISTS;

// ============================================================================
// 4. 唯一约束
// ============================================================================

// 确保用户节点的 user_id 唯一
CREATE CONSTRAINT FOR (u:User) REQUIRE u.user_id IS UNIQUE IF NOT EXISTS;

// 确保速记节点的 memo_id 唯一
CREATE CONSTRAINT FOR (m:Memo) REQUIRE m.memo_id IS UNIQUE IF NOT EXISTS;

// 确保事件节点的 event_id 唯一
CREATE CONSTRAINT FOR (e:Event) REQUIRE e.event_id IS UNIQUE IF NOT EXISTS;

// 确保分类节点的 name 唯一
CREATE CONSTRAINT FOR (c:Category) REQUIRE c.name IS UNIQUE IF NOT EXISTS;

// 确保标签节点的 name 唯一
CREATE CONSTRAINT FOR (t:Tag) REQUIRE t.name IS UNIQUE IF NOT EXISTS;

// ============================================================================
// 5. 示例数据（可选 - 用于测试）
// ============================================================================

// 取消以下行的注释以创建示例数据用于测试

// // 创建示例用户
// CREATE (u:User {user_id: 1, name: '张三', email: 'zhangsan@example.com'});

// // 创建示例分类
// CREATE (c1:Category {name: '学习资料', level: 1});
// CREATE (c2:Category {name: 'Python编程', level: 2});
// CREATE (c3:Category {name: '运动', level: 1});
// CREATE (c4:Category {name: '跑步训练', level: 2});

// // 创建分类层级关系
// CREATE (c2)-[:CHILD_OF]->(c1);
// CREATE (c4)-[:CHILD_OF]->(c3);

// // 创建用户分类偏好
// CREATE (u)-[:PREFERS]->(c1);
// CREATE (u)-[:PREFERS]->(c3);

// // 创建示例标签
// CREATE (tag1:Tag {name: 'LangChain'});
// CREATE (tag2:Tag {name: 'AI'});
// CREATE (tag3:Tag {name: 'Python'});

// // 创建示例实体
// CREATE (entity:Entity {name: 'LangChain', type: 'Technology'});

// // 创建示例速记
// CREATE (memo:Memo {
//     memo_id: 101,
//     title: '学习LangChain笔记',
//     content: '今天学了LangChain的Agent机制，比之前的AgentExecutor灵活很多',
//     created_at: datetime()
// });

// // 创建示例事件
// CREATE (event:Event {
//     event_id: 201,
//     title: '完成AI项目',
//     description: '用LangChain+Neo4j搭建知识图谱系统',
//     status: 'in_progress',
//     priority: 'high',
//     event_type: 'project',
//     keywords: ['LangChain', 'Neo4j', '知识图谱'],
//     created_at: datetime()
// });

// // 创建关系
// CREATE (u)-[:OWNS]->(memo);
// CREATE (u)-[:OWNS]->(event);
// CREATE (memo)-[:BELONGS_TO]->(c2);
// CREATE (memo)-[:HAS_TAG]->(tag1);
// CREATE (memo)-[:HAS_TAG]->(tag2);
// CREATE (memo)-[:MENTIONS]->(entity);
// CREATE (memo)-[:LINKED_TO]->(event);
// CREATE (event)-[:BELONGS_TO]->(c2);

// ============================================================================
// 6. 验证查询
// ============================================================================

// 显示所有索引
SHOW INDEXES;

// 显示所有约束
SHOW CONSTRAINTS;
