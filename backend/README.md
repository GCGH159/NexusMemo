# NexusMemo 后端项目说明文档

## 📋 项目概述

NexusMemo 是一个智能速记系统，基于 FastAPI + Neo4j + Redis 架构，提供用户注册登录、速记创建、智能分类、关系提取、图数据库存储和智能搜索等功能。

### 核心特性

- **用户认证系统**：基于 Token 的会话管理，支持 Redis 缓存
- **智能速记处理**：使用 LangGraph Agent 工作流自动分类、提取实体、建立关系
- **图数据库存储**：Neo4j 存储用户、分类、速记及其关系
- **智能搜索**：基于 Agent 的多策略搜索（全文搜索、图查询、多跳遍历）
- **Redis 组件**：延迟队列、广播通知、缓存组件

---

## 🛠 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12+ | 主要开发语言 |
| FastAPI | Latest | Web 框架 |
| SQLAlchemy | 2.0+ | ORM（MySQL） |
| Neo4j | 5.x | 图数据库 |
| Redis | 7.x | 缓存、消息队列 |
| LangGraph | Latest | Agent 工作流编排 |
| LangChain | Latest | LLM 集成 |
| Alembic | Latest | 数据库迁移 |
| Pytest | Latest | 测试框架 |

---

## 📁 目录结构

```
backend/
├── app/                          # 应用主目录
│   ├── api/                      # API 路由层
│   │   └── v1/                   # API v1 版本
│   │       ├── auth.py           # 认证接口（注册、登录、注销）
│   │       ├── memos.py          # 速记接口（创建、查询、更新、删除）
│   │       ├── preferences.py    # 用户偏好接口
│   │       └── search.py         # 搜索接口
│   ├── db/                       # 数据库配置
│   │   ├── config.py             # 数据库连接配置（MySQL、Neo4j、Redis）
│   │   └── init.py               # 数据库初始化
│   ├── models/                   # SQLAlchemy 数据模型
│   │   └── user.py               # 用户、会话、速记模型
│   ├── redis_components/         # Redis 组件
│   │   ├── cache.py              # 缓存组件
│   │   ├── broadcast.py          # 广播通知组件
│   │   └── delay_queue.py        # 延迟队列组件
│   ├── services/                 # 业务逻辑层
│   │   ├── auth.py               # 认证服务（密码哈希、Token 生成、会话管理）
│   │   ├── category.py           # 分类服务（一级分类、二级分类生成）
│   │   └── user_preference.py    # 用户偏好服务
│   ├── __init__.py
│   └── main.py                   # FastAPI 应用入口
├── memo_agent/                   # 速记处理 Agent
│   ├── nodes/                    # Agent 节点
│   │   ├── bind_events.py        # 绑定事件节点
│   │   ├── classify.py           # 分类节点
│   │   ├── extract.py            # 提取标签和实体节点
│   │   ├── find_relations.py     # 查找关系节点
│   │   ├── future_reminder.py    # 将来事项提醒节点
│   │   ├── judge_relations.py    # 判定关系节点
│   │   ├── load_context.py       # 加载用户图谱上下文节点
│   │   └── persist_graph.py      # 持久化到 Neo4j 节点
│   ├── schemas/                  # Agent 数据模式
│   ├── state.py                  # Agent 状态定义
│   └── workflow.py               # Agent 工作流编排
├── search_agent/                 # 搜索 Agent
│   ├── nodes/                    # Agent 节点
│   │   ├── cypher_search.py      # Cypher 查询节点
│   │   ├── decide_strategy.py    # 决策搜索策略节点
│   │   ├── fulltext_search.py    # 全文搜索节点
│   │   ├── merge_results.py      # 融合结果节点
│   │   ├── rank_results.py       # LLM 排序节点
│   │   └── traversal_search.py   # 多跳遍历节点
│   ├── state.py                  # Agent 状态定义
│   └── workflow.py               # Agent 工作流编排
├── scripts/                      # 脚本工具
│   ├── cleanup_test_data.py      # 清理测试数据
│   ├── create_mysql_db.py        # 创建 MySQL 数据库
│   ├── init_neo4j.cypher         # Neo4j 初始化脚本
│   └── run_neo4j_init.py         # 运行 Neo4j 初始化
├── tests/                        # 测试目录
│   ├── conftest.py               # 测试配置和 fixtures
│   ├── test_auth.py              # 认证测试
│   ├── test_memos.py             # 速记测试
│   ├── test_preferences.py       # 用户偏好测试
│   ├── test_redis_components.py  # Redis 组件测试
│   ├── test_search.py            # 搜索测试
│   └── TEST_REPORT.md            # 测试报告
├── alembic/                      # 数据库迁移
│   ├── versions/                 # 迁移版本
│   └── env.py                    # Alembic 配置
├── alembic.ini                   # Alembic 配置文件
├── requirements.txt              # Python 依赖
└── .env                          # 环境变量配置
```

---

## 📂 详细文件说明

### `app/` - 应用主目录

#### `app/main.py`
FastAPI 应用入口文件，负责：
- 创建 FastAPI 应用实例
- 配置 CORS 中间件
- 注册 API 路由
- 应用生命周期管理（启动/关闭）
- 健康检查接口

#### `app/api/v1/` - API 路由层

##### `app/api/v1/auth.py`
用户认证 API，提供以下接口：
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/logout` - 用户注销
- `GET /api/v1/auth/categories/primary` - 获取一级分类
- `POST /api/v1/auth/categories/generate-sub` - 生成二级分类
- `GET /api/v1/auth/me` - 获取当前用户信息

##### `app/api/v1/memos.py`
速记管理 API，提供以下接口：
- `POST /api/v1/memos/` - 创建速记
- `POST /api/v1/memos/audio` - 上传音频创建速记（待实现）
- `GET /api/v1/memos/{memo_id}` - 获取速记详情
- `GET /api/v1/memos/` - 获取速记列表
- `PUT /api/v1/memos/{memo_id}` - 更新速记
- `DELETE /api/v1/memos/{memo_id}` - 删除速记（软删除）

##### `app/api/v1/preferences.py`
用户偏好管理 API，提供以下接口：
- `POST /api/v1/preferences/add` - 添加偏好
- `GET /api/v1/preferences/list` - 获取偏好列表
- `PUT /api/v1/preferences/update` - 更新偏好
- `DELETE /api/v1/preferences/delete` - 删除偏好
- `GET /api/v1/preferences/selected-categories` - 获取已选分类

##### `app/api/v1/search.py`
智能搜索 API，提供以下接口：
- `POST /api/v1/search/` - 执行智能搜索

#### `app/db/` - 数据库配置

##### `app/db/config.py`
数据库连接配置，包含：
- `Settings` 类：从 `.env` 加载配置
- MySQL 异步引擎和会话工厂
- Neo4j 连接管理器
- Redis 连接管理器
- 依赖注入函数：`get_db()`, `get_neo4j_session()`, `get_redis()`

#### `app/models/` - 数据模型

##### `app/models/user.py`
SQLAlchemy 数据模型定义：
- `User`：用户模型（用户名、密码哈希、邮箱、偏好）
- `Session`：会话模型（Token、过期时间）
- `Memo`：速记模型（标题、内容、类型、状态、处理标记）
- `UserCategoryPreference`：用户分类偏好模型
- `MemoType`：速记类型枚举（quick_note, event）
- `MemoStatus`：速记状态枚举（active, archived, deleted）

#### `app/redis_components/` - Redis 组件

##### `app/redis_components/cache.py`
缓存组件，提供：
- 基本操作：`get()`, `set()`, `delete()`, `exists()`
- 过期时间：`expire()`, `ttl()`
- 批量操作：`get_many()`, `set_many()`, `delete_many()`
- 计数器：`increment()`, `decrement()`
- 统计信息：`get_stats()`
- 支持多种序列化方式：JSON、Pickle、Raw

##### `app/redis_components/broadcast.py`
广播通知组件，提供：
- 频道订阅：`subscribe()`, `unsubscribe()`
- 消息发布：`publish()`
- 订阅者管理：`get_subscriber_count()`, `clear_subscribers()`
- 基于 Redis Pub/Sub 实现

##### `app/redis_components/delay_queue.py`
延迟队列组件，提供：
- 任务管理：`push()`, `pop()`, `cancel()`
- 工作线程：`start_worker()`, `stop_worker()`
- 队列管理：`count()`, `clear()`
- 基于 Redis Sorted Set 实现

#### `app/services/` - 业务逻辑层

##### `app/services/auth.py`
认证服务，提供：
- 密码哈希和验证：`hash_password()`, `verify_password()`
- Token 生成：`generate_token()`
- 用户管理：`create_user()`, `authenticate_user()`
- 会话管理：`create_session()`, `verify_session()`, `delete_session()`
- 过期会话清理：`cleanup_expired_sessions()`
- 支持 Redis 缓存加速会话验证

##### `app/services/category.py`
分类服务，提供：
- 一级分类验证：`validate_primary_category()`
- 获取一级分类：`get_primary_categories()`
- 生成二级分类：`generate_subcategories()`（使用 LLM）

##### `app/services/user_preference.py`
用户偏好服务，提供：
- 偏好管理：`add_preference()`, `get_preference()`, `update_preference()`, `delete_preference()`
- 批量操作：`batch_add_preferences()`, `get_selected_categories()`
- 获取用户偏好列表：`get_user_preferences()`

### `memo_agent/` - 速记处理 Agent

#### `memo_agent/state.py`
定义 Agent 状态：
- `MemoProcessState`：包含用户ID、速记ID、类型、标题、内容、分类结果、提取结果、关系候选、最终关系、事件链接等

#### `memo_agent/workflow.py`
Agent 工作流编排，定义处理流程：
1. `load_context` - 加载用户图谱上下文
2. `classify` - 匹配分类
3. `extract` - 提取标签和实体
4. `find_relations` - 查找相关内容
5. `judge_relations` - 判定关联关系（仅速记）
6. `bind_events` - 绑定事件（仅速记）
7. `persist_graph` - 写入 Neo4j

#### `memo_agent/nodes/` - Agent 节点

##### `memo_agent/nodes/load_context.py`
加载用户图谱上下文节点，从 Neo4j 获取用户的分类偏好和历史速记。

##### `memo_agent/nodes/classify.py`
分类节点，使用 LLM 将速记分类到用户偏好的一级/二级分类。

##### `memo_agent/nodes/extract.py`
提取节点，使用 LLM 从速记内容中提取标签、实体和时间信息。

##### `memo_agent/nodes/find_relations.py`
查找关系节点：
- 速记：被动匹配相关内容，包括查询用户的将来事项
- 事件：使用 ReAct Agent 主动搜索相关内容

##### `memo_agent/nodes/future_reminder.py`
将来事项提醒节点：
- 识别将来要做的事情（基于时间信息提取）
- 通过延迟队列设置定时提醒
- 通过Redis广播通知关系发现Agent
- 支持多种时间格式（ISO、相对时间、自然语言）
- 支持多种提醒类型（deadline、appointment、task）

##### `memo_agent/nodes/judge_relations.py`
判定关系节点，使用 LLM 判定候选关系的相关性。

##### `memo_agent/nodes/bind_events.py`
绑定事件节点，将速记与相关事件建立关联。

##### `memo_agent/nodes/persist_graph.py`
持久化节点，将处理结果写入 Neo4j 图数据库。

### `search_agent/` - 搜索 Agent

#### `search_agent/state.py`
定义 Agent 状态：
- `SearchState`：包含用户ID、查询、搜索策略、全文搜索结果、Cypher 搜索结果、遍历结果、融合结果、排序结果、最终答案、来源等

#### `search_agent/workflow.py`
Agent 工作流编排，定义搜索流程：
1. `decide_strategy` - 决策搜索策略
2. 根据策略执行搜索（fulltext/cypher/traversal）
3. `merge_results` - 融合搜索结果
4. `rank_results` - LLM 排序并生成最终答案

#### `search_agent/nodes/` - Agent 节点

##### `search_agent/nodes/decide_strategy.py`
决策搜索策略节点，使用 LLM 根据查询内容智能选择搜索策略（全文搜索、图查询、多跳遍历）。

##### `search_agent/nodes/fulltext_search.py`
全文搜索节点，使用 Neo4j 全文索引进行关键词匹配。

##### `search_agent/nodes/cypher_search.py`
Cypher 查询节点，使用 LLM 生成 Cypher 查询语句，支持复杂图关系查询。

##### `search_agent/nodes/traversal_search.py`
多跳遍历节点，探索关系链，查找相关内容，最多 3 跳。

##### `search_agent/nodes/merge_results.py`
融合结果节点，合并来自不同搜索策略的结果，去重并计算综合分数。

##### `search_agent/nodes/rank_results.py`
LLM 排序节点，对搜索结果进行相关性排序，生成简洁的总结性答案，提取来源信息。

### `scripts/` - 脚本工具

#### `scripts/cleanup_test_data.py`
清理测试数据脚本，删除测试用户、速记和会话。

#### `scripts/create_mysql_db.py`
创建 MySQL 数据库脚本。

#### `scripts/init_neo4j.cypher`
Neo4j 初始化 Cypher 脚本，创建索引和约束。

#### `scripts/run_neo4j_init.py`
运行 Neo4j 初始化脚本。

### `tests/` - 测试目录

#### `tests/conftest.py`
测试配置和 fixtures，提供数据库连接、测试用户创建等。

#### `tests/test_auth.py`
认证测试，包含 20 个测试用例，覆盖注册、登录、注销、会话验证等功能。

#### `tests/test_memos.py`
速记测试，包含 9 个测试用例，覆盖创建、查询、更新、删除等功能。

#### `tests/test_preferences.py`
用户偏好测试，包含 12 个测试用例，覆盖偏好管理功能。

#### `tests/test_redis_components.py`
Redis 组件测试，包含 15 个测试用例，覆盖缓存、广播、延迟队列功能。

#### `tests/test_search.py`
搜索测试，包含 6 个测试用例，覆盖搜索策略决策、结果融合等功能。

### `alembic/` - 数据库迁移

#### `alembic/versions/`
数据库迁移版本文件，记录数据库结构变更。

#### `alembic/env.py`
Alembic 配置文件，定义迁移环境。

---

## 🗄 数据库设计

### MySQL 数据模型

#### users 表
用户信息表，存储用户基本信息和偏好。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| username | String(64) | 用户名（唯一） |
| password_hash | String(256) | 密码哈希 |
| email | String(128) | 邮箱（可选） |
| preferences | JSON | 用户偏好 |
| created_at | TIMESTAMP | 创建时间 |

#### sessions 表
会话表，存储用户登录会话。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 用户ID（外键） |
| token | String(512) | 会话Token（唯一） |
| expires_at | TIMESTAMP | 过期时间 |
| created_at | TIMESTAMP | 创建时间 |

#### memos 表
速记表，存储速记和事件。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 用户ID（外键） |
| type | Enum | 类型（quick_note/event） |
| title | String(256) | 标题 |
| content | Text | 内容 |
| audio_url | String(512) | 音频URL（可选） |
| status | Enum | 状态（active/archived/deleted） |
| processed | Boolean | 是否已处理 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

#### user_category_preferences 表
用户分类偏好表。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger | 主键 |
| user_id | BigInteger | 用户ID（外键） |
| category_level | Integer | 分类层级（1=一级，2=二级） |
| category_name | String(128) | 分类名称 |
| selected | Boolean | 是否选中 |
| created_at | TIMESTAMP | 创建时间 |

### Neo4j 图模型

#### 节点类型

- **User**：用户节点
  - 属性：user_id, name, created_at

- **Category**：分类节点
  - 属性：name, level（1=一级，2=二级）

- **Memo**：速记节点
  - 属性：memo_id, title, content, type, created_at

- **Entity**：实体节点
  - 属性：name, type

- **Event**：事件节点
  - 属性：event_id, title, content, created_at

#### 关系类型

- **PREFERS**：用户偏好分类
  - User -> Category

- **CHILD_OF**：分类层级关系
  - Category -> Category

- **HAS_MEMO**：用户拥有速记
  - User -> Memo

- **BELONGS_TO**：速记属于分类
  - Memo -> Category

- **HAS_ENTITY**：速记包含实体
  - Memo -> Entity

- **RELATED_TO**：速记关联速记
  - Memo -> Memo

- **LINKED_TO**：速记关联事件
  - Memo -> Event

---

## 🔌 API 接口说明

### 认证接口

#### 注册
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123",
  "email": "test@example.com",
  "primary_categories": ["学习资料"],
  "sub_categories": ["Python", "机器学习"]
}
```

#### 登录
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "testuser",
  "password": "password123"
}
```

#### 注销
```http
POST /api/v1/auth/logout
Content-Type: application/json

{
  "token": "session_token_here"
}
```

### 速记接口

#### 创建速记
```http
POST /api/v1/memos/
Content-Type: application/json

{
  "title": "学习笔记",
  "content": "今天学习了 Python 的异步编程...",
  "type": "quick_note",
  "user_id": 1
}
```

#### 获取速记列表
```http
GET /api/v1/memos/?user_id=1&skip=0&limit=20
```

### 搜索接口

#### 智能搜索
```http
POST /api/v1/search/
Content-Type: application/json

{
  "user_id": 1,
  "query": "Python 异步编程"
}
```

---

## 🤖 Agent 工作流说明

### 速记处理 Agent 工作流

```
load_context → classify → extract → find_relations
                                        ↓
                                   [判断类型]
                                        ↓
                    ┌───────────────────┴───────────────────┐
                    ↓                                       ↓
            quick_note_path                          event_path
                    ↓                                       ↓
        judge_relations → bind_events → persist_graph   persist_graph
```

### 搜索 Agent 工作流

```
decide_strategy → [根据策略选择搜索节点]
                    ↓
        ┌───────────┼───────────┐
        ↓           ↓           ↓
fulltext  cypher  traversal
        ↓           ↓           ↓
        └───────────┼───────────┘
                    ↓
            merge_results → rank_results
```

---

## ⚡ Redis 组件说明

### 缓存组件

用于加速数据访问，支持：
- 字符串、JSON、Pickle 序列化
- 过期时间设置
- 批量操作
- 计数器操作

### 广播通知组件

用于实时消息推送，支持：
- 多频道订阅
- 消息广播
- 异步消息处理

### 延迟队列组件

用于定时任务，支持：
- 延迟任务添加
- 工作线程自动执行
- 任务取消

---

## 🧪 测试说明

### 运行测试

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### 测试覆盖

- 认证测试：20/20 通过
- 速记测试：9/9 通过
- 用户偏好测试：12/12 通过
- Redis 组件测试：15/15 通过
- 搜索测试：6/6 通过

**总计：62/62 测试通过（100%）**

---

## 🚀 启动说明

### 环境配置

1. 复制 `.env` 文件并配置数据库连接
2. 创建 MySQL 数据库：`python scripts/create_mysql_db.py`
3. 初始化 Neo4j：`python scripts/run_neo4j_init.py`

### 启动服务

```bash
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 健康检查

```bash
curl http://localhost:8000/health
```

---

## 📝 开发规范

### 代码风格

- 使用 PEP 8 规范
- 使用类型注解
- 编写 docstring

### 提交规范

```
feat: 新功能
fix: 修复问题
docs: 文档更新
test: 测试相关
refactor: 重构
```

---

## 🔐 安全说明

- 密码使用 bcrypt 哈希存储
- Token 使用 secrets.token_urlsafe() 生成
- 会话支持 Redis 缓存加速
- 支持 CORS 配置

---

## 📞 联系方式

如有问题，请联系开发团队。
