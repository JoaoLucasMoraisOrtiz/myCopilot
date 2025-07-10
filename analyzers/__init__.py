"""
Analisadores específicos por linguagem de programação.
"""

from .java_analyzer import build_symbol_table as build_java_symbol_table
from .react_analyzer import build_symbol_table as build_react_symbol_table

__all__ = ['build_java_symbol_table', 'build_react_symbol_table']
