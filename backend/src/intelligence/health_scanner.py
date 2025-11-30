"""
Code Health Scanner

Calculates per-function health scores and identifies bug hotspots.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import logging

from static_analyzer import StaticAnalyzer, CodeSmell

logger = logging.getLogger(__name__)


@dataclass
class HealthScore:
    """Health score for a code entity."""
    entity_type: str  # 'file' or 'function'
    entity_name: str
    file_path: str
    score: float  # 0-100 (higher is better)
    complexity: float
    smell_count: int
    bug_risk: str  # 'low', 'medium', 'high'
    churn_rate: float  # placeholder for git history
    recommendations: List[str]


class CodeHealthScanner:
    """
    Scan code and calculate health scores.
    """
    
    def __init__(self):
        """Initialize code health scanner."""
        self.analyzer = StaticAnalyzer()
    
    def scan_file(
        self,
        file_path: str,
        content: str,
        language: str,
        functions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Scan a file and calculate health metrics.
        
        Args:
            file_path: Path to file
            content: File content
            language: Programming language
            functions: List of function metadata
        
        Returns:
            Dictionary of health metrics
        """
        # Get code smells
        smells = self.analyzer.analyze_file(file_path, content, language, functions)
        
        # Get file-level metrics
        metrics = self.analyzer.calculate_metrics(functions, content)
        
        # Calculate file health score
        file_score = self._calculate_file_health(metrics, smells)
        
        # Calculate function-level scores
        function_scores = []
        
        for func in functions:
            func_score = self._calculate_function_health(
                file_path,
                func,
                content.splitlines(),
                language,
                smells
            )
            function_scores.append(func_score)
        
        return {
            'file_path': file_path,
            'file_health_score': file_score.score,
            'file_bug_risk': file_score.bug_risk,
            'metrics': metrics,
            'smells': [
                {
                    'type': s.smell_type,
                    'line': s.line,
                    'severity': s.severity,
                    'message': s.message,
                    'suggestion': s.suggestion
                }
                for s in smells
            ],
            'function_health': [
                {
                    'name': fs.entity_name,
                    'score': fs.score,
                    'complexity': fs.complexity,
                    'bug_risk': fs.bug_risk,
                    'recommendations': fs.recommendations
                }
                for fs in function_scores
            ]
        }
    
    def _calculate_file_health(
        self,
        metrics: Dict[str, Any],
        smells: List[CodeSmell]
    ) -> HealthScore:
        """Calculate file-level health score."""
        score = 100.0
        
        # Penalize based on maintainability index
        mi = metrics.get('maintainability_index', 50)
        score -= (100 - mi) * 0.3
        
        # Penalize based on smells
        high_severity = sum(1 for s in smells if s.severity == 'high')
        medium_severity = sum(1 for s in smells if s.severity == 'medium')
        low_severity = sum(1 for s in smells if s.severity == 'low')
        
        score -= high_severity * 10
        score -= medium_severity * 5
        score -= low_severity * 2
        
        score = max(0, min(100, score))
        
        # Determine bug risk
        if score >= 70:
            bug_risk = 'low'
        elif score >= 40:
            bug_risk = 'medium'
        else:
            bug_risk = 'high'
        
        # Generate recommendations
        recommendations = []
        
        if high_severity > 0:
            recommendations.append(f"Address {high_severity} high-severity issues immediately")
        
        if mi < 50:
            recommendations.append("Improve maintainability through refactoring")
        
        if metrics.get('avg_function_length', 0) > 50:
            recommendations.append("Break down large functions into smaller units")
        
        return HealthScore(
            entity_type='file',
            entity_name='',
            file_path='',
            score=score,
            complexity=0,
            smell_count=len(smells),
            bug_risk=bug_risk,
            churn_rate=0.0,
            recommendations=recommendations
        )
    
    def _calculate_function_health(
        self,
        file_path: str,
        function: Dict[str, Any],
        lines: List[str],
        language: str,
        all_smells: List[CodeSmell]
    ) -> HealthScore:
        """Calculate function-level health score."""
        func_name = function.get('name', 'unknown')
        start_line = function.get('start_line', 1)
        end_line = function.get('end_line', 1)
        
        score = 100.0
        
        # Get function content
        func_lines = lines[start_line-1:end_line]
        func_content = '\n'.join(func_lines)
        
        # Calculate complexity
        complexity = self.analyzer._estimate_cyclomatic_complexity(func_content, language)
        
        # Penalize complexity
        if complexity > 10:
            score -= (complexity - 10) * 5
        
        # Count function-specific smells
        func_smells = [
            s for s in all_smells
            if start_line <= s.line <= end_line
        ]
        
        # Penalize smells
        for smell in func_smells:
            if smell.severity == 'high':
                score -= 15
            elif smell.severity == 'medium':
                score -= 8
            else:
                score -= 3
        
        # Penalize length
        func_length = end_line - start_line + 1
        if func_length > 50:
            score -= (func_length - 50) * 0.5
        
        score = max(0, min(100, score))
        
        # Determine bug risk
        if score >= 70:
            bug_risk = 'low'
        elif score >= 40:
            bug_risk = 'medium'
        else:
            bug_risk = 'high'
        
        # Generate recommendations
        recommendations = []
        
        if complexity > 10:
            recommendations.append(f"Reduce complexity (current: {complexity})")
        
        if func_length > 50:
            recommendations.append(f"Function too long ({func_length} lines), consider splitting")
        
        if len(func_smells) > 0:
            recommendations.append(f"Fix {len(func_smells)} code smell(s)")
        
        return HealthScore(
            entity_type='function',
            entity_name=func_name,
            file_path=file_path,
            score=score,
            complexity=complexity,
            smell_count=len(func_smells),
            bug_risk=bug_risk,
            churn_rate=0.0,
            recommendations=recommendations
        )
    
    def identify_bug_hotspots(
        self,
        health_results: List[Dict[str, Any]],
        threshold: float = 50.0
    ) -> List[Dict[str, Any]]:
        """
        Identify bug hotspots (low health score functions).
        
        Args:
            health_results: List of health scan results
            threshold: Health score threshold (below = hotspot)
        
        Returns:
            List of hotspots
        """
        hotspots = []
        
        for result in health_results:
            file_path = result['file_path']
            
            # Check file-level health
            if result['file_health_score'] < threshold:
                hotspots.append({
                    'type': 'file',
                    'file': file_path,
                    'score': result['file_health_score'],
                    'risk': result['file_bug_risk']
                })
            
            # Check function-level health
            for func_health in result.get('function_health', []):
                if func_health['score'] < threshold:
                    hotspots.append({
                        'type': 'function',
                        'file': file_path,
                        'function': func_health['name'],
                        'score': func_health['score'],
                        'complexity': func_health['complexity'],
                        'risk': func_health['bug_risk'],
                        'recommendations': func_health['recommendations']
                    })
        
        # Sort by score (lowest first)
        hotspots.sort(key=lambda x: x['score'])
        
        return hotspots


def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python health_scanner.py <file_path> <language>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else 'python'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Mock function data
    functions = [{'name': 'test', 'start_line': 1, 'end_line': 10}]
    
    scanner = CodeHealthScanner()
    result = scanner.scan_file(file_path, content, language, functions)
    
    print(f"\n📊 Health Report for {file_path}")
    print(f"  File Health Score: {result['file_health_score']:.1f}/100")
    print(f"  Bug Risk: {result['file_bug_risk'].upper()}")
    print(f"  Code Smells: {len(result['smells'])}")
    
    if result['function_health']:
        print(f"\n📦 Function Health:")
        for fh in result['function_health']:
            print(f"  {fh['name']}: {fh['score']:.1f}/100 (complexity: {fh['complexity']})")


if __name__ == "__main__":
    main()
