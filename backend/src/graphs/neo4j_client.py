"""
Neo4j Client

Handles all interactions with Neo4j graph database.
"""

from typing import Dict, List, Any, Optional
import logging
from neo4j import GraphDatabase, Driver, Session

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Client for Neo4j graph database operations.
    """
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j client.
        
        Args:
            uri: Neo4j connection URI (bolt://...)
            username: Database username
            password: Database password
        """
        self.uri = uri
        self.driver: Optional[Driver] = None
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(username, password))
            logger.info(f"Connected to Neo4j at {uri}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def verify_connectivity(self) -> bool:
        """Verify database connection."""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1")
                result.single()
            return True
        except Exception as e:
            logger.error(f"Connectivity check failed: {e}")
            return False
    
    def create_indexes(self):
        """Create database indexes for performance."""
        with self.driver.session() as session:
            # Function indexes
            session.run("""
                CREATE INDEX function_name_idx IF NOT EXISTS
                FOR (f:Function) ON (f.name)
            """)
            
            session.run("""
                CREATE INDEX function_file_idx IF NOT EXISTS
                FOR (f:Function) ON (f.file)
            """)
            
            # Class indexes
            session.run("""
                CREATE INDEX class_name_idx IF NOT EXISTS
                FOR (c:Class) ON (c.name)
            """)
            
            # File indexes
            session.run("""
                CREATE INDEX file_path_idx IF NOT EXISTS
                FOR (f:File) ON (f.path)
            """)
            
            logger.info("Created Neo4j indexes")
    
    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)."""
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
            logger.warning("Cleared entire Neo4j database")
    
    def create_function_node(self, function_data: Dict[str, Any]) -> str:
        """
        Create a function node.
        
        Args:
            function_data: Function metadata
        
        Returns:
            Node ID
        """
        with self.driver.session() as session:
            result = session.run("""
                CREATE (f:Function {
                    name: $name,
                    file: $file,
                    start_line: $start_line,
                    end_line: $end_line,
                    signature: $signature,
                    language: $language,
                    complexity: $complexity
                })
                RETURN elementId(f) as id
            """, **function_data)
            
            return result.single()["id"]
    
    def create_class_node(self, class_data: Dict[str, Any]) -> str:
        """Create a class node."""
        with self.driver.session() as session:
            result = session.run("""
                CREATE (c:Class {
                    name: $name,
                    file: $file,
                    start_line: $start_line,
                    end_line: $end_line,
                    language: $language
                })
                RETURN elementId(c) as id
            """, **class_data)
            
            return result.single()["id"]
    
    def create_file_node(self, file_data: Dict[str, Any]) -> str:
        """Create a file node."""
        with self.driver.session() as session:
            result = session.run("""
                MERGE (f:File {path: $path})
                ON CREATE SET 
                    f.language = $language,
                    f.size_bytes = $size_bytes,
                    f.created_at = datetime()
                RETURN elementId(f) as id
            """, **file_data)
            
            return result.single()["id"]
    
    def create_relationship(
        self,
        from_node: str,
        to_node: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None
    ):
        """
        Create a relationship between nodes.
        
        Args:
            from_node: Source node ID
            to_node: Target node ID
            rel_type: Relationship type (CALLS, DEFINES, etc.)
            properties: Optional relationship properties
        """
        props = properties or {}
        
        with self.driver.session() as session:
            # Using elementId for Neo4j 5+
            query = f"""
                MATCH (a), (b)
                WHERE elementId(a) = $from_id AND elementId(b) = $to_id
                CREATE (a)-[r:{rel_type}]->(b)
            """
            
            if props:
                query += " SET " + ", ".join([f"r.{k} = ${k}" for k in props.keys()])
            
            session.run(query, from_id=from_node, to_id=to_node, **props)
    
    def find_function(self, name: str, file: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Find a function by name and optionally file."""
        with self.driver.session() as session:
            if file:
                result = session.run("""
                    MATCH (f:Function {name: $name, file: $file})
                    RETURN elementId(f) as id, f
                    LIMIT 1
                """, name=name, file=file)
            else:
                result = session.run("""
                    MATCH (f:Function {name: $name})
                    RETURN elementId(f) as id, f
                    LIMIT 1
                """, name=name)
            
            record = result.single()
            if record:
                return {"id": record["id"], **dict(record["f"])}
            return None
    
    def get_function_callers(self, function_id: str) -> List[Dict[str, Any]]:
        """Get all functions that call a specific function."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (caller:Function)-[:CALLS]->(f)
                WHERE elementId(f) = $function_id
                RETURN elementId(caller) as id, caller
            """, function_id=function_id)
            
            return [{"id": r["id"], **dict(r["caller"])} for r in result]
    
    def get_function_callees(self, function_id: str) -> List[Dict[str, Any]]:
        """Get all functions called by a specific function."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (f)-[:CALLS]->(callee:Function)
                WHERE elementId(f) = $function_id
                RETURN elementId(callee) as id, callee
            """, function_id=function_id)
            
            return [{"id": r["id"], **dict(r["callee"])} for r in result]
    
    def get_file_functions(self, file_path: str) -> List[Dict[str, Any]]:
        """Get all functions in a file."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (f:Function {file: $file})
                RETURN elementId(f) as id, f
                ORDER BY f.start_line
            """, file=file_path)
            
            return [{"id": r["id"], **dict(r["f"])} for r in result]
    
    def get_graph_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        with self.driver.session() as session:
            result = session.run("""
                MATCH (n)
                RETURN 
                    count(n) as total_nodes,
                    count{(n:Function)} as functions,
                    count{(n:Class)} as classes,
                    count{(n:File)} as files,
                    count { MATCH ()-[r]->() RETURN r } AS total_relationships
            """)
            
            record = result.single()
            return dict(record) if record else {}
    
    def execute_cypher(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a custom Cypher query.
        
        Args:
            query: Cypher query string
            parameters: Query parameters
        
        Returns:
            List of result records
        """
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def main():
    """CLI entry point for testing."""
    import sys
    from ..app.config import get_settings
    
    settings = get_settings()
    
    with Neo4jClient(settings.neo4j_url, settings.neo4j_username, settings.neo4j_password) as client:
        if client.verify_connectivity():
            print("✅ Connected to Neo4j successfully")
            
            # Get stats
            stats = client.get_graph_stats()
            print(f"\n📊 Database Stats:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Failed to connect to Neo4j")


if __name__ == "__main__":
    main()
