# NexusMemo 后端测试用例

## 测试结构

```
tests/
├── __init__.py          # 测试包初始化
├── conftest.py          # Pytest 配置和全局 fixtures
├── test_api.py          # API 接口测试
└── test_nodes.py        # LangGraph 节点测试
```

## 运行测试

### 运行所有测试
```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

### 运行特定测试文件
```bash
pytest tests/test_api.py -v
pytest tests/test_nodes.py -v
```

### 运行特定测试类
```bash
pytest tests/test_api.py::TestHealthAPI -v
pytest tests/test_api.py::TestMemoAPI -v
```

### 运行特定测试方法
```bash
pytest tests/test_api.py::TestMemoAPI::test_get_memo -v
```

### 生成测试覆盖率报告
```bash
pytest tests/ --cov=app --cov=memo_agent --cov-report=html
```

## 测试说明

### API 接口测试 (test_api.py)

#### TestHealthAPI
- `test_health_check`: 测试健康检查接口

#### TestMemoAPI
- `test_create_memo`: 测试创建速记
- `test_get_memo`: 测试获取指定速记
- `test_list_memos`: 测试获取速记列表
- `test_get_nonexistent_memo`: 测试获取不存在的速记
- `test_create_memo_without_user`: 测试创建速记时用户不存在

#### TestMemoValidation
- `test_create_memo_missing_title`: 测试创建速记时缺少标题
- `test_create_memo_missing_content`: 测试创建速记时缺少内容
- `test_create_memo_invalid_type`: 测试创建速记时类型无效

### LangGraph 节点测试 (test_nodes.py)

#### TestLoadContextNode
- `test_load_user_graph_context`: 测试加载用户图谱上下文

#### TestClassifyNode
- `test_classify_node`: 测试分类节点

#### TestExtractNode
- `test_extract_tags_entities_node`: 测试提取标签和实体节点

## 注意事项

1. **LLM API 依赖**: 部分测试需要调用 LLM API，如果 API 不可用或返回错误，测试会被跳过
2. **数据库依赖**: 测试需要 MySQL、Neo4j 和 Redis 数据库运行
3. **测试数据**: 测试会创建测试用户（user_id=1），测试完成后不会自动清理
4. **异步测试**: 所有测试都是异步的，使用 pytest-asyncio 插件

## 已知问题

1. **POST /api/v1/memos/** 接口测试可能失败，因为 LLM 模型可能返回非 JSON 格式的响应
2. 部分节点测试需要 LLM API，如果 API 不可用会被跳过

## 测试覆盖率

当前测试覆盖了以下功能：
- ✅ 健康检查接口
- ✅ 获取速记接口
- ✅ 获取速记列表接口
- ✅ 数据验证
- ⚠️ 创建速记接口（部分成功，LLM 处理可能失败）
- ⚠️ LangGraph 节点（需要 LLM API）
