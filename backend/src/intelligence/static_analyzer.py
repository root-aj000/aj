"""
Static Code Analyzer

Detects code smells, complexity issues, and quality metrics.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import re
from pathlib import Path


@dataclass
class CodeSmell:
    """Represents a detected code smell."""
    file: str
    line: int
    smell_type: str
    severity: str  # 'low', 'medium', 'high'
    message: str
    suggestion: Optional[str] = None


class StaticAnalyzer:
    """
    Analyze code for quality issues and complexity metrics.
    """
    
    # Thresholds
    MAX_FUNCTION_LINES = 50
    MAX_LINE_LENGTH = 120
    MAX_PARAMETERS = 5
    MAX_COMPLEXITY = 10
    
    def __init__(self):
        """Initialize static analyzer."""
        pass
    
    def analyze_file(
        self,
        file_path: str,
        content: str,
        language: str,
        functions: List[Dict[str, Any]]
    ) -> List[CodeSmell]:
        """
        Analyze a file for code smells.
        
        Args:
            file_path: Path to file
            content: File content
            language: Programming language
            functions: List of function metadata
        
        Returns:
            List of detected code smells
        """
        smells: List[CodeSmell] = []
        lines = content.splitlines()
        
        # Analyze functions
        for func in functions:
            func_smells = self._analyze_function(file_path, func, lines, language)
            smells.extend(func_smells)
        
        # Analyze overall file
        file_smells = self._analyze_file_level(file_path, lines, language)
        smells.extend(file_smells)
        
        return smells
    
    def _analyze_function(
        self,
        file_path: str,
        function: Dict[str, Any],
        lines: List[str],
        language: str
    ) -> List[CodeSmell]:
        """Analyze a single function."""
        smells: List[CodeSmell] = []
        
        func_name = function.get('name', 'unknown')
        start_line = function.get('start_line', 1)
        end_line = function.get('end_line', 1)
        
        # Calculate function length
        func_length = end_line - start_line + 1
        
        if func_length > self.MAX_FUNCTION_LINES:
            smells.append(CodeSmell(
                file=file_path,
                line=start_line,
                smell_type='long_function',
                severity='medium',
                message=f"Function '{func_name}' is {func_length} lines (max: {self.MAX_FUNCTION_LINES})",
                suggestion="Consider breaking into smaller functions"
            ))
        
        # Get function content
        func_lines = lines[start_line-1:end_line]
        func_content = '\n'.join(func_lines)
        
        # Check for complexity indicators
        complexity = self._estimate_cyclomatic_complexity(func_content, language)
        
        if complexity > self.MAX_COMPLEXITY:
            smells.append(CodeSmell(
                file=file_path,
                line=start_line,
                smell_type='high_complexity',
                severity='high',
                message=f"Function '{func_name}' has complexity {complexity} (max: {self.MAX_COMPLEXITY})",
                suggestion="Simplify logic or extract helper functions"
            ))
        
        # Check parameter count
        param_count = self._count_parameters(func_lines[0] if func_lines else '', language)
        
        if param_count > self.MAX_PARAMETERS:
            smells.append(CodeSmell(
                file=file_path,
                line=start_line,
                smell_type='too_many_parameters',
                severity='medium',
                message=f"Function '{func_name}' has {param_count} parameters (max: {self.MAX_PARAMETERS})",
                suggestion="Consider using parameter objects or configuration"
            ))
        
        # Check for code duplication patterns
        if self._has_code_duplication(func_content):
            smells.append(CodeSmell(
                file=file_path,
                line=start_line,
                smell_type='code_duplication',
                severity='low',
                message=f"Function '{func_name}' may contain duplicated code",
                suggestion="Extract common patterns into helper functions"
            ))
        
        return smells
    
    def _analyze_file_level(
        self,
        file_path: str,
        lines: List[str],
        language: str
    ) -> List[CodeSmell]:
        """Analyze file-level issues."""
        smells: List[CodeSmell] = []
        
        # Check line lengths
        for i, line in enumerate(lines, 1):
            if len(line) > self.MAX_LINE_LENGTH:
                smells.append(CodeSmell(
                    file=file_path,
                    line=i,
                    smell_type='long_line',
                    severity='low',
                    message=f"Line exceeds {self.MAX_LINE_LENGTH} characters ({len(line)})",
                    suggestion="Break into multiple lines"
                ))
        
        # Check for commented-out code
        commented_lines = self._find_commented_code(lines, language)
        
        if len(commented_lines) > 10:
            smells.append(CodeSmell(
                file=file_path,
                line=commented_lines[0],
                smell_type='commented_code',
                severity='low',
                message=f"File contains {len(commented_lines)} lines of commented code",
                suggestion="Remove dead code or use version control"
            ))
        
        # Check for TODO/FIXME
        todos = self._find_todos(lines)
        
        for line_num in todos:
            smells.append(CodeSmell(
                file=file_path,
                line=line_num,
                smell_type='todo',
                severity='low',
                message="TODO/FIXME comment found",
                suggestion="Track in issue tracker instead"
            ))
        
        return smells
    
    def _estimate_cyclomatic_complexity(self, content: str, language: str) -> int:
        """
        Estimate cyclomatic complexity (rough approximation).
        
        Real complexity = 1 + number of decision points
        """
        complexity = 1
        
        # Count decision points
        decision_keywords = [
            r'\bif\b', r'\belif\b', r'\belse\b',
            r'\bfor\b', r'\bwhile\b',
            r'\bcase\b', r'\bswitch\b',
            r'\band\b', r'\bor\b',
            r'\?', r'\&\&', r'\|\|'
        ]
        
        for keyword in decision_keywords:
            complexity += len(re.findall(keyword, content, re.IGNORECASE))
        
        return complexity
    
    def _count_parameters(self, signature: str, language: str) -> int:
        """Count function parameters from signature."""
        # Simple approach: count commas in parameter list
        # Extract content between parentheses
        match = re.search(r'\(([^)]*)\)', signature)
        
        if not match:
            return 0
        
        params = match.group(1).strip()
        
        if not params:
            return 0
        
        # Count commas + 1
        return params.count(',') + 1
    
    def _has_code_duplication(self, content: str) -> bool:
        """Detect potential code duplication (simplified)."""
        lines = [l.strip() for l in content.splitlines() if l.strip() and not l.strip().startswith('#')]
        
        if len(lines) < 10:
            return False
        
        # Look for repeated line patterns
        line_counts: Dict[str, int] = {}
        
        for line in lines:
            if len(line) > 10:  # Ignore short lines
                line_counts[line] = line_counts.get(line, 0) + 1
        
        # If same line appears 3+ times, likely duplication
        for count in line_counts.values():
            if count >= 3:
                return True
        
        return False
    
    def _find_commented_code(self, lines: List[str], language: str) -> List[int]:
        """Find lines that appear to be commented-out code."""
        commented = []
        
        comment_prefix = '#' if language == 'python' else '//'
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            if stripped.startswith(comment_prefix):
                # Check if it looks like code (has operators, keywords, etc.)
                uncommented = stripped[len(comment_prefix):].strip()
                
                if self._looks_like_code(uncommented, language):
                    commented.append(i)
        
        return commented
    
    def _looks_like_code(self, text: str, language: str) -> bool:
        """Check if text looks like commented-out code."""
        code_indicators = ['=', '(', ')', '{', '}', '[', ']', ';', 'def ', 'class ', 'import ', 'const ', 'let ', 'var ']
        
        for indicator in code_indicators:
            if indicator in text:
                return True
        
        return False
    
    def _find_todos(self, lines: List[str]) -> List[int]:
        """Find TODO/FIXME comments."""
        todos = []
        
        for i, line in enumerate(lines, 1):
            if re.search(r'\b(TODO|FIXME|HACK|XXX)\b', line, re.IGNORECASE):
                todos.append(i)
        
        return todos
    
    def calculate_metrics(self, functions: List[Dict[str, Any]], content: str) -> Dict[str, Any]:
        """
        Calculate code quality metrics.
        
        Returns:
            Dictionary of metrics
        """
        lines = content.splitlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        return {
            'total_lines': len(lines),
            'code_lines': len(code_lines),
            'comment_lines': len(lines) - len(code_lines),
            'function_count': len(functions),
            'avg_function_length': sum(f['end_line'] - f['start_line'] + 1 for f in functions) / len(functions) if functions else 0,
            'maintainability_index': self._calculate_maintainability_index(content, functions)
        }
    
    def _calculate_maintainability_index(
        self,
        content: str,
        functions: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate maintainability index (simplified).
        
        Real MI formula is complex; this is a simplified approximation.
        Score: 0-100 (higher is better)
        """
        lines = content.splitlines()
        code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
        
        # Volume (lines of code)
        volume = len(code_lines)
        
        # Complexity (average across functions)
        avg_complexity = sum(
            self._estimate_cyclomatic_complexity('\n'.join(lines[f['start_line']-1:f['end_line']]), 'python')
            for f in functions
        ) / len(functions) if functions else 1
        
        # Simple formula: 100 - penalties
        score = 100
        score -= min(volume / 10, 30)  # Penalize large files
        score -= min(avg_complexity * 3, 40)  # Penalize complexity
        
        return max(0, score)


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python static_analyzer.py <file_path> <language>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'python'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Mock function data for demo
    functions = [{'name': 'test', 'start_line': 1, 'end_line': 10}]
    
    analyzer = StaticAnalyzer()
    smells = analyzer.analyze_file(file_path, content, language, functions)
    
    print(f"\n🔍 Found {len(smells)} code smells:")
    for smell in smells:
        print(f"\n  [{smell.severity.upper()}] {smell.smell_type}")
        print(f"  Line {smell.line}: {smell.message}")
        if smell.suggestion:
            print(f"  💡 {smell.suggestion}")


if __name__ == "__main__":
    main()
