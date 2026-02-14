#!/usr/bin/env python3
"""
创建 MySQL 数据库脚本
"""
import pymysql

# MySQL 连接配置
MYSQL_HOST = "11.163.69.213"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_DATABASE = "nexus_memo"

def create_database():
    """创建 MySQL 数据库"""
    try:
        # 连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 检查数据库是否存在
        cursor.execute(f"SHOW DATABASES LIKE '{MYSQL_DATABASE}'")
        result = cursor.fetchone()
        
        if result:
            print(f"数据库 '{MYSQL_DATABASE}' 已存在")
        else:
            # 创建数据库
            cursor.execute(f"CREATE DATABASE {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 '{MYSQL_DATABASE}' 创建成功")
        
        cursor.close()
        connection.close()
        
    except Exception as e:
        print(f"创建数据库失败: {e}")
        raise

if __name__ == "__main__":
    create_database()
