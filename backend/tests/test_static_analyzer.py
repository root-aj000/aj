"""
Unit Tests for Static Analyzer
"""

import pytest
from src.intelligence.static_analyzer import StaticAnalyzer


class TestStaticAnalyzer:
    """Test suite for StaticAnalyzer."""
    
    def test_initialization(self):
        """Test analyzer initialization."""
        analyzer = StaticAnalyzer()
        assert analyzer is not None
    
    def test_detect_long_function(self):
        """Test detection of long functions."""
        analyzer = StaticAnalyzer()
        
        # Create a long function (>50 lines)
        code = "def long_function():\n" + "    pass\n" * 60
        
        smells = analyzer.analyze(code, "python")
        
        long_func_smells = [s for s in smells if s['type'] == 'long_function']
        assert len(long_func_smells) > 0
    
    def test_detect_high_complexity(self):
        """Test detection of high cyclomatic complexity."""
        analyzer = StaticAnalyzer()
        
        # Create complex function with many branches
        code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                return 1
            return 2
        return 3
    return 4
"""
        
        smells = analyzer.analyze(code, "python")
        complexity = analyzer.calculate_complexity(code)
        
        assert complexity > 1
    
    def test_detect_many_parameters(self):
        """Test detection of functions with too many parameters."""
        analyzer = StaticAnalyzer()
        
        code = "def many_params(a, b, c, d, e, f, g): pass"
        
        smells = analyzer.analyze(code, "python")
        
        param_smells = [s for s in smells if s['type'] == 'too_many_parameters']
        assert len(param_smells) > 0
    
    def test_detect_commented_code(self):
        """Test detection of commented-out code."""
        analyzer = StaticAnalyzer()
        
        code = """
def test():
    # old_function_call()
    # another_line = 42
    pass
"""
        
        smells = analyzer.analyze(code, "python")
        
        commented_smells = [s for s in smells if s['type'] == 'commented_code']
        assert len(commented_smells) > 0
    
    def test_maintainability_index(self):
        """Test maintainability index calculation."""
        analyzer = StaticAnalyzer()
        
        # Simple, maintainable code
        simple_code = "def add(a, b):\n    return a + b"
        
        index = analyzer.calculate_maintainability_index(simple_code)
        
        assert 0 <= index <= 100
        assert index > 50  # Simple code should have decent maintainability
    
    def test_no_smells_for_clean_code(self):
        """Test that clean code has minimal smells."""
        analyzer = StaticAnalyzer()
        
        clean_code = """
def calculate_sum(numbers):
    \"\"\"Calculate sum of numbers.\"\"\"
    total = 0
    for num in numbers:
        total += num
    return total
"""
        
        smells = analyzer.analyze(clean_code, "python")
        
        # Should have no major smells
        assert len(smells) == 0 or all(s['severity'] == 'low' for s in smells)
