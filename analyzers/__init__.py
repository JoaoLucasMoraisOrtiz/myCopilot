"""
Analisadores específicos por linguagem de programação.
"""

from .python_analyzer import PythonAnalyzer
from .javascript_analyzer import JavaScriptAnalyzer
from .ruby_analyzer import RubyAnalyzer

__all__ = ["PythonAnalyzer", "JavaScriptAnalyzer", "RubyAnalyzer"]
