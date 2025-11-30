"""
CFG (Control Flow Graph) Builder

Constructs control flow graphs for functions showing:
- Basic blocks (sequences of statements)
- Control flow edges (jumps, branches, loops)
- Exception handling paths
"""

from typing import Dict, List, Any, Set, Optional
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class BasicBlock:
    """Represents a basic block in CFG."""
    id: str
    statements: List[str]
    start_line: int
    end_line: int
    successors: List[str]  # IDs of successor blocks
    block_type: str  # 'entry', 'exit', 'normal', 'branch', 'loop', 'exception'


class CFGBuilder:
    """
    Build Control Flow Graphs for functions.
    
    A CFG represents all paths that might be traversed through a function
    during its execution.
    """
    
    def __init__(self):
        """Initialize CFG builder."""
        self.blocks: Dict[str, BasicBlock] = {}
        self.current_id = 0
    
    def build_from_ast(self, ast_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build CFG from AST data.
        
        Args:
            ast_data: AST representation of function
        
        Returns:
            CFG data structure
        """
        function_name = ast_data.get('name', 'unknown')
        body = ast_data.get('body', [])
        
        logger.info(f"Building CFG for function: {function_name}")
        
        # Create entry block
        entry_block = self._create_block('entry', [], 0, 0)
        
        # Process function body
        current_block = entry_block
        for statement in body:
            current_block = self._process_statement(statement, current_block)
        
        # Create exit block
        exit_block = self._create_block('exit', [], 0, 0)
        
        # Connect last block to exit
        if current_block:
            current_block.successors.append(exit_block.id)
        
        return {
            'function': function_name,
            'entry_block': entry_block.id,
            'exit_block': exit_block.id,
            'blocks': {bid: self._block_to_dict(block) for bid, block in self.blocks.items()},
            'total_blocks': len(self.blocks),
            'has_loops': self._has_loops(),
            'has_branches': self._has_branches(),
            'has_exceptions': self._has_exceptions(),
        }
    
    def _create_block(
        self,
        block_type: str,
        statements: List[str],
        start_line: int,
        end_line: int
    ) -> BasicBlock:
        """Create a new basic block."""
        block_id = f"block_{self.current_id}"
        self.current_id += 1
        
        block = BasicBlock(
            id=block_id,
            statements=statements,
            start_line=start_line,
            end_line=end_line,
            successors=[],
            block_type=block_type
        )
        
        self.blocks[block_id] = block
        return block
    
    def _process_statement(
        self,
        statement: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """
        Process a statement and update CFG.
        
        Args:
            statement: AST statement node
            current_block: Current basic block
        
        Returns:
            Updated current block
        """
        stmt_type = statement.get('type', 'unknown')
        
        if stmt_type == 'if_statement':
            return self._process_if(statement, current_block)
        elif stmt_type == 'while_statement':
            return self._process_while(statement, current_block)
        elif stmt_type == 'for_statement':
            return self._process_for(statement, current_block)
        elif stmt_type == 'try_statement':
            return self._process_try(statement, current_block)
        elif stmt_type == 'return_statement':
            return self._process_return(statement, current_block)
        else:
            # Normal statement - add to current block
            current_block.statements.append(str(statement))
            return current_block
    
    def _process_if(
        self,
        if_stmt: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """Process if statement creating branch."""
        # Create branch block
        branch_block = self._create_block('branch', [], 0, 0)
        current_block.successors.append(branch_block.id)
        
        # Process then branch
        then_body = if_stmt.get('then_body', [])
        then_block = self._create_block('normal', [], 0, 0)
        branch_block.successors.append(then_block.id)
        
        # Process else branch if exists
        else_body = if_stmt.get('else_body', [])
        if else_body:
            else_block = self._create_block('normal', [], 0, 0)
            branch_block.successors.append(else_block.id)
        
        # Create merge block
        merge_block = self._create_block('normal', [], 0, 0)
        then_block.successors.append(merge_block.id)
        if else_body:
            else_block.successors.append(merge_block.id)
        else:
            branch_block.successors.append(merge_block.id)
        
        return merge_block
    
    def _process_while(
        self,
        while_stmt: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """Process while loop."""
        # Create loop header (condition check)
        loop_header = self._create_block('loop', [], 0, 0)
        current_block.successors.append(loop_header.id)
        
        # Create loop body
        loop_body = self._create_block('normal', [], 0, 0)
        loop_header.successors.append(loop_body.id)
        
        # Loop body goes back to header
        loop_body.successors.append(loop_header.id)
        
        # Create exit block
        exit_block = self._create_block('normal', [], 0, 0)
        loop_header.successors.append(exit_block.id)
        
        return exit_block
    
    def _process_for(
        self,
        for_stmt: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """Process for loop."""
        # Similar to while
        return self._process_while(for_stmt, current_block)
    
    def _process_try(
        self,
        try_stmt: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """Process try-except statement."""
        # Create try block
        try_block = self._create_block('exception', [], 0, 0)
        current_block.successors.append(try_block.id)
        
        # Create except blocks
        handlers = try_stmt.get('handlers', [])
        except_blocks = []
        for handler in handlers:
            except_block = self._create_block('exception', [], 0, 0)
            try_block.successors.append(except_block.id)
            except_blocks.append(except_block)
        
        # Create merge block
        merge_block = self._create_block('normal', [], 0, 0)
        try_block.successors.append(merge_block.id)
        for eb in except_blocks:
            eb.successors.append(merge_block.id)
        
        return merge_block
    
    def _process_return(
        self,
        return_stmt: Dict[str, Any],
        current_block: BasicBlock
    ) -> BasicBlock:
        """Process return statement."""
        current_block.statements.append("return")
        # Returns don't have successors in the normal flow
        return current_block
    
    def _block_to_dict(self, block: BasicBlock) -> Dict[str, Any]:
        """Convert block to dictionary."""
        return {
            'id': block.id,
            'type': block.block_type,
            'statements': block.statements,
            'start_line': block.start_line,
            'end_line': block.end_line,
            'successors': block.successors,
            'statement_count': len(block.statements),
        }
    
    def _has_loops(self) -> bool:
        """Check if CFG contains loops."""
        return any(b.block_type == 'loop' for b in self.blocks.values())
    
    def _has_branches(self) -> bool:
        """Check if CFG contains branches."""
        return any(b.block_type == 'branch' for b in self.blocks.values())
    
    def _has_exceptions(self) -> bool:
        """Check if CFG contains exception handling."""
        return any(b.block_type == 'exception' for b in self.blocks.values())
    
    def analyze_complexity(self) -> int:
        """
        Calculate cyclomatic complexity from CFG.
        
        M = E - N + 2P
        where E = edges, N = nodes, P = connected components
        """
        edges = sum(len(block.successors) for block in self.blocks.values())
        nodes = len(self.blocks)
        components = 1  # Assuming single connected component
        
        complexity = edges - nodes + 2 * components
        return max(1, complexity)


def main():
    """CLI entry point for testing."""
    # Example usage
    builder = CFGBuilder()
    
    # Example AST data
    ast_data = {
        'name': 'example_function',
        'body': [
            {'type': 'assignment', 'line': 1},
            {
                'type': 'if_statement',
                'condition': 'x > 0',
                'then_body': [{'type': 'assignment', 'line': 3}],
                'else_body': [{'type': 'assignment', 'line': 5}],
            },
            {'type': 'return_statement', 'line': 6},
        ],
    }
    
    cfg = builder.build_from_ast(ast_data)
    
    print(f"\n📊 CFG Analysis for '{cfg['function']}':")
    print(f"  Total blocks: {cfg['total_blocks']}")
    print(f"  Has loops: {cfg['has_loops']}")
    print(f"  Has branches: {cfg['has_branches']}")
    print(f"  Cyclomatic complexity: {builder.analyze_complexity()}")


if __name__ == "__main__":
    main()
