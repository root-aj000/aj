"""
Symbol Lineage Tracer

Traces symbols (variables, functions, classes) across files to understand:
- Where a symbol is defined
- Where it's imported
- Where it's used
- How it's renamed/refactored
"""

from typing import Dict, List, Any, Set, Optional
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class SymbolLineageTracer:
    """
    Trace symbol usage across codebase.
    
    Builds a lineage graph showing:
    - Definition location
    - Import chain
    - All usage locations
    - Type evolution
    """
    
    def __init__(self, neo4j_client=None):
        """
        Initialize tracer.
        
        Args:
            neo4j_client: Neo4j client for graph queries
        """
        self.neo4j_client = neo4j_client
        self.symbol_cache: Dict[str, Dict[str, Any]] = {}
    
    def trace_symbol(self, symbol_name: str, context_file: Optional[str] = None) -> Dict[str, Any]:
        """
        Trace a symbol's lineage.
        
        Args:
            symbol_name: Name of symbol to trace
            context_file: File where symbol is being referenced
        
        Returns:
            Symbol lineage data
        """
        logger.info(f"Tracing symbol: {symbol_name}")
        
        lineage = {
            'symbol': symbol_name,
            'definitions': [],
            'imports': [],
            'usages': [],
            'type_info': {},
            'lineage_chain': [],
        }
        
        # Find all definitions
        definitions = self._find_definitions(symbol_name)
        lineage['definitions'] = definitions
        
        # Find imports
        imports = self._find_imports(symbol_name, context_file)
        lineage['imports'] = imports
        
        # Find all usages
        usages = self._find_usages(symbol_name)
        lineage['usages'] = usages
        
        # Build lineage chain
        lineage['lineage_chain'] = self._build_lineage_chain(
            symbol_name,
            definitions,
            imports
        )
        
        return lineage
    
    def _find_definitions(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find all places where symbol is defined."""
        definitions = []
        
        if self.neo4j_client:
            # Query Neo4j for function/class nodes
            query = """
            MATCH (s)
            WHERE s.name = $symbol_name
            AND (s:Function OR s:Class)
            RETURN s.file as file, s.line as line, 
                   s.type as type, s.signature as signature
            """
            
            results = self.neo4j_client.execute_query(
                query,
                {'symbol_name': symbol_name}
            )
            
            for record in results:
                definitions.append({
                    'file': record['file'],
                    'line': record['line'],
                    'type': record['type'],
                    'signature': record.get('signature', ''),
                })
        
        return definitions
    
    def _find_imports(
        self,
        symbol_name: str,
        context_file: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Find all import statements for this symbol."""
        imports = []
        
        if self.neo4j_client:
            query = """
            MATCH (f:File)-[imp:IMPORTS]->(target)
            WHERE target.name = $symbol_name
            """
            
            if context_file:
                query += " AND f.path = $context_file"
            
            query += """
            RETURN f.path as file, imp.line as line,
                   imp.import_type as import_type,
                   imp.alias as alias
            """
            
            params = {'symbol_name': symbol_name}
            if context_file:
                params['context_file'] = context_file
            
            results = self.neo4j_client.execute_query(query, params)
            
            for record in results:
                imports.append({
                    'file': record['file'],
                    'line': record['line'],
                    'import_type': record['import_type'],
                    'alias': record.get('alias'),
                })
        
        return imports
    
    def _find_usages(self, symbol_name: str) -> List[Dict[str, Any]]:
        """Find all places where symbol is used."""
        usages = []
        
        # This would typically involve:
        # 1. Full-text search in code
        # 2. AST analysis to find references
        # 3. Graph traversal for call sites
        
        if self.neo4j_client:
            # Find functions that call this symbol
            query = """
            MATCH (caller:Function)-[:CALLS]->(callee)
            WHERE callee.name = $symbol_name
            RETURN caller.file as file, caller.name as caller_name,
                   caller.line as line
            """
            
            results = self.neo4j_client.execute_query(
                query,
                {'symbol_name': symbol_name}
            )
            
            for record in results:
                usages.append({
                    'file': record['file'],
                    'line': record['line'],
                    'caller': record['caller_name'],
                    'usage_type': 'function_call',
                })
        
        return usages
    
    def _build_lineage_chain(
        self,
        symbol_name: str,
        definitions: List[Dict[str, Any]],
        imports: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Build the lineage chain from definition to usage.
        
        Returns chain: definition -> imports -> usages
        """
        chain = []
        
        # Start with definition
        if definitions:
            primary_def = definitions[0]
            chain.append({
                'step': 'definition',
                'file': primary_def['file'],
                'line': primary_def['line'],
                'description': f"Defined in {primary_def['file']}",
            })
        
        # Add import steps
        for imp in imports:
            chain.append({
                'step': 'import',
                'file': imp['file'],
                'line': imp['line'],
                'description': f"Imported in {imp['file']}" + 
                              (f" as {imp['alias']}" if imp.get('alias') else ""),
            })
        
        return chain
    
    def find_rename_candidates(
        self,
        old_name: str,
        new_name: str
    ) -> List[Dict[str, Any]]:
        """
        Find all locations that would need to change for a rename.
        
        Args:
            old_name: Current symbol name
            new_name: Proposed new name
        
        Returns:
            List of locations to update
        """
        lineage = self.trace_symbol(old_name)
        
        candidates = []
        
        # Add definition locations
        for defn in lineage['definitions']:
            candidates.append({
                'file': defn['file'],
                'line': defn['line'],
                'change_type': 'definition',
                'old': old_name,
                'new': new_name,
            })
        
        # Add import locations
        for imp in lineage['imports']:
            candidates.append({
                'file': imp['file'],
                'line': imp['line'],
                'change_type': 'import',
                'old': old_name,
                'new': new_name,
            })
        
        # Add usage locations
        for usage in lineage['usages']:
            candidates.append({
                'file': usage['file'],
                'line': usage['line'],
                'change_type': 'usage',
                'old': old_name,
                'new': new_name,
            })
        
        return candidates
    
    def analyze_symbol_impact(self, symbol_name: str) -> Dict[str, Any]:
        """
        Analyze the impact of changing/removing a symbol.
        
        Returns:
            Impact analysis
        """
        lineage = self.trace_symbol(symbol_name)
        
        return {
            'symbol': symbol_name,
            'total_usages': len(lineage['usages']),
            'files_affected': len(set(u['file'] for u in lineage['usages'])),
            'import_count': len(lineage['imports']),
            'definition_count': len(lineage['definitions']),
            'impact_score': self._calculate_impact_score(lineage),
            'high_risk': len(lineage['usages']) > 10,
        }
    
    def _calculate_impact_score(self, lineage: Dict[str, Any]) -> float:
        """Calculate impact score (0-100)."""
        # More usages = higher impact
        usage_score = min(len(lineage['usages']) * 10, 60)
        
        # More files = higher impact
        files = set(u['file'] for u in lineage['usages'])
        file_score = min(len(files) * 5, 30)
        
        # Imports add impact
        import_score = min(len(lineage['imports']) * 2, 10)
        
        return usage_score + file_score + import_score


def main():
    """CLI entry point."""
    tracer = SymbolLineageTracer()
    
    print("\n🔍 Symbol Lineage Tracer")
    print("=" * 50)
    
    # Example trace
    symbol = "UserAuth"
    lineage = tracer.trace_symbol(symbol)
    
    print(f"\nTracing symbol: {symbol}")
    print(f"  Definitions: {len(lineage['definitions'])}")
    print(f"  Imports: {len(lineage['imports'])}")
    print(f"  Usages: {len(lineage['usages'])}")
    
    # Example impact analysis
    impact = tracer.analyze_symbol_impact(symbol)
    print(f"\n📊 Impact Analysis:")
    print(f"  Total usages: {impact['total_usages']}")
    print(f"  Files affected: {impact['files_affected']}")
    print(f"  Impact score: {impact['impact_score']:.1f}/100")
    print(f"  High risk: {'Yes' if impact['high_risk'] else 'No'}")


if __name__ == "__main__":
    main()
