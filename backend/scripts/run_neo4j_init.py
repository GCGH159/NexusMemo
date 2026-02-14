#!/usr/bin/env python3
"""
执行 Neo4j 初始化脚本
"""
import asyncio
from neo4j import AsyncGraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Neo4j 连接配置
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "")


async def run_cypher_script():
    """执行 Cypher 脚本文件"""
    driver = AsyncGraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    
    try:
        # 读取 Cypher 脚本文件
        script_path = os.path.join(os.path.dirname(__file__), "init_neo4j.cypher")
        with open(script_path, 'r', encoding='utf-8') as f:
            cypher_script = f.read()
        
        # 分割 Cypher 语句（按分号分割）
        statements = [stmt.strip() for stmt in cypher_script.split(';') if stmt.strip()]
        
        async with driver.session() as session:
            for i, statement in enumerate(statements, 1):
                # 跳过注释行
                if statement.startswith('//'):
                    continue
                
                try:
                    result = await session.run(statement)
                    # 消费结果以确保查询执行完成
                    await result.consume()
                    print(f"✓ 执行成功 ({i}/{len(statements)}): {statement[:50]}...")
                except Exception as e:
                    # 某些语句可能因为索引已存在而失败，这是正常的
                    if "already exists" in str(e) or "EquivalentSchemaRule" in str(e):
                        print(f"⊘ 已存在 ({i}/{len(statements)}): {statement[:50]}...")
                    else:
                        print(f"✗ 执行失败 ({i}/{len(statements)}): {statement[:50]}...")
                        print(f"  错误: {e}")
        
        print("\nNeo4j 初始化脚本执行完成！")
        
    except Exception as e:
        print(f"执行 Neo4j 初始化脚本失败: {e}")
        raise
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(run_cypher_script())
