"""
Database initialization utilities.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.config import Base, async_engine, neo4j_conn
import logging

logger = logging.getLogger(__name__)


async def init_mysql():
    """Initialize MySQL database tables."""
    try:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("MySQL database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MySQL database: {e}")
        raise


async def init_neo4j():
    """Initialize Neo4j database with indexes and constraints."""
    try:
        driver = await neo4j_conn.connect()
        async with driver.session() as session:
            # Create indexes for User
            await session.run("CREATE INDEX FOR (u:User) ON (u.user_id) IF NOT EXISTS")
            
            # Create indexes for Memo
            await session.run("CREATE INDEX FOR (m:Memo) ON (m.memo_id) IF NOT EXISTS")
            
            # Create indexes for Event
            await session.run("CREATE INDEX FOR (e:Event) ON (e.event_id) IF NOT EXISTS")
            
            # Create indexes for Category
            await session.run("CREATE INDEX FOR (c:Category) ON (c.name) IF NOT EXISTS")
            
            # Create indexes for Tag
            await session.run("CREATE INDEX FOR (t:Tag) ON (t.name) IF NOT EXISTS")
            
            # Create indexes for Entity
            await session.run("CREATE INDEX FOR (en:Entity) ON (en.name) IF NOT EXISTS")
            
            # Create indexes for TimePeriod
            await session.run("CREATE INDEX FOR (tp:TimePeriod) ON (tp.date) IF NOT EXISTS")
            
            # Create fulltext indexes for search
            await session.run("""
                CREATE FULLTEXT INDEX memoContent 
                FOR (m:Memo) ON EACH [m.title, m.content] 
                OPTIONS {indexConfig: {`fulltext.analyzer`: 'standard'}}
                IF NOT EXISTS
            """)
            
            await session.run("""
                CREATE FULLTEXT INDEX eventContent 
                FOR (e:Event) ON EACH [e.title, e.description] 
                OPTIONS {indexConfig: {`fulltext.analyzer`: 'standard'}}
                IF NOT EXISTS
            """)
            
            # Create vector index for semantic search (if supported)
            try:
                await session.run("""
                    CALL db.index.vector.createNodeIndex(
                        'memo_embeddings', 'Memo', 'embedding', 1536, 'cosine'
                    ) IF NOT EXISTS
                """)
                logger.info("Neo4j vector index created successfully")
            except Exception as e:
                logger.warning(f"Vector index creation failed (may not be supported): {e}")
            
        logger.info("Neo4j database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Neo4j database: {e}")
        raise


async def close_connections():
    """Close all database connections."""
    await neo4j_conn.close()
    await async_engine.dispose()
    logger.info("All database connections closed")
