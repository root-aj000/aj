"""
Graph API Routes

Endpoints for code graph exploration.
"""

from fastapi import APIRouter
from typing import Dict, Any, Optional
import logging

from ..config import get_settings
from ...graphs.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/graph", tags=["graph"])

# Lazy initialization
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Optional[Neo4jClient]:
    """Get or create Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        try:
            settings = get_settings()
            _neo4j_client = Neo4jClient(
                uri=settings.neo4j_url,
                username=settings.neo4j_username,
                password=settings.neo4j_password
            )
        except Exception as e:
            logger.warning(f"Could not initialize Neo4j: {e}")
            return None
    return _neo4j_client


@router.get("/overview")
async def get_graph_overview():
    """
    Get overview of the code graph.
    
    Returns:
        Graph statistics and summary
    """
    try:
        neo4j_client = get_neo4j_client()
        
        if not neo4j_client:
            return {
                'nodes': {'functions': 0, 'classes': 0, 'files': 0},
                'relationships': {'calls': 0, 'contains': 0, 'imports': 0},
                'total_nodes': 0,
                'total_relationships': 0,
                'error': 'Neo4j not available'
            }
        
        with neo4j_client.driver.session() as session:
            # Count nodes by type
            functions_count = session.run("MATCH (fn:Function) RETURN count(fn) as count").single()['count']
            files_count = session.run("MATCH (f:File) RETURN count(f) as count").single()['count']
            classes_count = session.run("MATCH (c:Class) RETURN count(c) as count").single()['count']
            
            # Count relationships by type
            calls_count = session.run("MATCH ()-[r:CALLS]->() RETURN count(r) as count").single()['count']
            contains_count = session.run("MATCH ()-[r:CONTAINS]->() RETURN count(r) as count").single()['count']
            imports_count = session.run("MATCH ()-[r:IMPORTS]->() RETURN count(r) as count").single()['count']
            
            # Total counts
            total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
            
            return {
                'nodes': {
                    'functions': functions_count,
                    'classes': classes_count,
                    'files': files_count
                },
                'relationships': {
                    'calls': calls_count,
                    'contains': contains_count,
                    'imports': imports_count
                },
                'total_nodes': total_nodes,
                'total_relationships': total_rels
            }
    
    except Exception as e:
        logger.error(f"Graph overview failed: {e}", exc_info=True)
        return {
            'nodes': {'functions': 0, 'classes': 0, 'files': 0},
            'relationships': {'calls': 0, 'contains': 0, 'imports': 0},
            'total_nodes': 0,
            'total_relationships': 0,
            'error': str(e)
        }


@router.get("/function/{function_name}/callers")
async def get_function_callers(function_name: str, file_path: Optional[str] = None):
    """
    Get functions that call a specific function.
    
    Args:
        function_name: Function name
        file_path: Optional file path filter
    
    Returns:
        Caller functions
    """
    try:
        neo4j_client = get_neo4j_client()
        
        if not neo4j_client:
            return {
                'function': function_name,
                'file': file_path,
                'callers': [],
                'error': 'Neo4j not available'
            }
        
        with neo4j_client.driver.session() as session:
            query = """
            MATCH (caller:Function)-[:CALLS]->(fn:Function {name: $name})
            """
            
            params = {'name': function_name}
            
            if file_path:
                query += " WHERE fn.file = $file"
                params['file'] = file_path
            
            query += """
            RETURN caller.name as caller_name, caller.file as caller_file,
                   caller.start_line as start_line
            """
            
            result = session.run(query, params)
            
            callers = [
                {
                    'name': record['caller_name'],
                    'file': record['caller_file'],
                    'start_line': record['start_line']
                }
                for record in result
            ]
            
            return {
                'function': function_name,
                'file': file_path,
                'callers': callers,
                'total': len(callers)
            }
    
    except Exception as e:
        logger.error(f"Get callers failed: {e}", exc_info=True)
        return {
            'function': function_name,
            'file': file_path,
            'callers': [],
            'error': str(e)
        }


@router.get("/function/{function_name}/callees")
async def get_function_callees(function_name: str, file_path: Optional[str] = None):
    """
    Get functions called by a specific function.
    
    Args:
        function_name: Function name
        file_path: Optional file path filter
    
    Returns:
        Called functions
    """
    try:
        neo4j_client = get_neo4j_client()
        
        if not neo4j_client:
            return {
                'function': function_name,
                'file': file_path,
                'callees': [],
                'error': 'Neo4j not available'
            }
        
        with neo4j_client.driver.session() as session:
            query = """
            MATCH (fn:Function {name: $name})-[:CALLS]->(callee:Function)
            """
            
            params = {'name': function_name}
            
            if file_path:
                query += " WHERE fn.file = $file"
                params['file'] = file_path
            
            query += """
            RETURN callee.name as callee_name, callee.file as callee_file,
                   callee.start_line as start_line
            """
            
            result = session.run(query, params)
            
            callees = [
                {
                    'name': record['callee_name'],
                    'file': record['callee_file'],
                    'start_line': record['start_line']
                }
                for record in result
            ]
            
            return {
                'function': function_name,
                'file': file_path,
                'callees': callees,
                'total': len(callees)
            }
    
    except Exception as e:
        logger.error(f"Get callees failed: {e}", exc_info=True)
        return {
            'function': function_name,
            'file': file_path,
            'callees': [],
            'error': str(e)
        }


@router.get("/file/{file_path:path}/dependencies")
async def get_file_dependencies(file_path: str):
    """
    Get dependencies for a file.
    
    Args:
        file_path: File path
    
    Returns:
        File dependencies
    """
    try:
        neo4j_client = get_neo4j_client()
        
        if not neo4j_client:
            return {
                'file': file_path,
                'dependencies': [],
                'dependents': [],
                'error': 'Neo4j not available'
            }
        
        with neo4j_client.driver.session() as session:
            # Get files this file imports
            deps_result = session.run("""
                MATCH (f:File {path: $path})-[:IMPORTS]->(dep:File)
                RETURN dep.path as file_path
            """, path=file_path)
            
            dependencies = [record['file_path'] for record in deps_result]
            
            # Get files that import this file
            dependents_result = session.run("""
                MATCH (dependent:File)-[:IMPORTS]->(f:File {path: $path})
                RETURN dependent.path as file_path
            """, path=file_path)
            
            dependents = [record['file_path'] for record in dependents_result]
            
            return {
                'file': file_path,
                'dependencies': dependencies,
                'dependents': dependents,
                'dependencies_count': len(dependencies),
                'dependents_count': len(dependents)
            }
    
    except Exception as e:
        logger.error(f"Get dependencies failed: {e}", exc_info=True)
        return {
            'file': file_path,
            'dependencies': [],
            'dependents': [],
            'error': str(e)
        }
