"""
Advanced Tools Service - Code Interpreter, Calculator, File Analyzer
Provides ChatGPT/Gemini-like tool capabilities
"""

import json
import math
import traceback
from typing import Any, Dict, List, Optional
from io import BytesIO
import structlog

log = structlog.get_logger("tools")


class CodeInterpreter:
    """Execute Python code safely with restricted environment"""

    ALLOWED_MODULES = {
        'math': math,
        'json': json,
        'datetime': __import__('datetime'),
        'statistics': __import__('statistics'),
        'collections': __import__('collections'),
    }

    def __init__(self):
        self.execution_history = []

    def execute(self, code: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute Python code with sandboxing"""
        try:
            # Prepare safe environment
            safe_dict = {
                '__builtins__': {
                    'range': range,
                    'len': len,
                    'sum': sum,
                    'max': max,
                    'min': min,
                    'sorted': sorted,
                    'enumerate': enumerate,
                    'zip': zip,
                    'list': list,
                    'dict': dict,
                    'set': set,
                    'tuple': tuple,
                    'str': str,
                    'int': int,
                    'float': float,
                    'bool': bool,
                    'abs': abs,
                    'round': round,
                    'pow': pow,
                    'all': all,
                    'any': any,
                    'print': print,
                },
                **self.ALLOWED_MODULES,
                'variables': variables or {},
            }

            # Block dangerous operations
            dangerous_imports = ['os', 'sys', 'subprocess', 'socket', 'urllib', 'requests']
            for dangerous in dangerous_imports:
                if dangerous in code.lower():
                    return {
                        'success': False,
                        'error': f'Cannot import {dangerous} - restricted for security',
                        'code': code
                    }

            # Execute code
            exec_globals = safe_dict.copy()
            exec_locals = {}
            
            exec(code, exec_globals, exec_locals)

            # Extract results
            output = exec_locals.get('result', None)
            if output is None:
                output = {k: v for k, v in exec_locals.items() if not k.startswith('_')}

            log.info("code_execution.success", code_len=len(code))

            return {
                'success': True,
                'result': output,
                'code': code,
                'output': str(output)
            }

        except SyntaxError as e:
            return {
                'success': False,
                'error': f'Syntax Error: {str(e)}',
                'code': code
            }
        except Exception as e:
            log.exception("code_execution.failed", error=str(e))
            return {
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'traceback': traceback.format_exc(),
                'code': code
            }


class Calculator:
    """Advanced calculator with scientific functions"""

    OPERATIONS = {
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'sqrt': math.sqrt,
        'log': math.log,
        'ln': math.log,
        'exp': math.exp,
        'abs': abs,
        'round': round,
    }

    @staticmethod
    def evaluate(expression: str) -> Dict[str, Any]:
        """Safely evaluate mathematical expression"""
        try:
            # Replace function names with math module references
            safe_expr = expression
            for op_name, op_func in Calculator.OPERATIONS.items():
                safe_expr = safe_expr.replace(op_name, f'math.{op_name}')

            # Check for restricted characters
            restricted = ['import', 'exec', 'eval', '__', 'open', 'file']
            for restricted_word in restricted:
                if restricted_word in safe_expr.lower():
                    return {'success': False, 'error': f'Operation {restricted_word} not allowed'}

            # Evaluate
            result = eval(safe_expr, {'math': math, '__builtins__': {}})

            log.info("calculator.evaluate", expression=expression, result=result)

            return {
                'success': True,
                'expression': expression,
                'result': result,
                'type': type(result).__name__
            }

        except ZeroDivisionError:
            return {'success': False, 'error': 'Division by zero', 'expression': expression}
        except Exception as e:
            return {
                'success': False,
                'error': f'{type(e).__name__}: {str(e)}',
                'expression': expression
            }


class FileAnalyzer:
    """Analyze uploaded files and extract information"""

    SUPPORTED_FORMATS = {
        'txt': 'text',
        'json': 'json',
        'csv': 'csv',
        'md': 'markdown',
        'log': 'log',
    }

    @staticmethod
    def analyze_text(content: str) -> Dict[str, Any]:
        """Analyze text file"""
        lines = content.split('\n')
        words = content.split()

        return {
            'type': 'text',
            'lines': len(lines),
            'words': len(words),
            'characters': len(content),
            'avg_line_length': len(content) / len(lines) if lines else 0,
            'unique_words': len(set(word.lower() for word in words)),
            'preview': content[:500] + ('...' if len(content) > 500 else '')
        }

    @staticmethod
    def analyze_json(content: str) -> Dict[str, Any]:
        """Analyze JSON file"""
        try:
            data = json.loads(content)
            return {
                'type': 'json',
                'valid': True,
                'keys': list(data.keys()) if isinstance(data, dict) else None,
                'structure': type(data).__name__,
                'size': len(json.dumps(data)),
                'preview': json.dumps(data, indent=2)[:500]
            }
        except json.JSONDecodeError as e:
            return {
                'type': 'json',
                'valid': False,
                'error': str(e)
            }

    @staticmethod
    def analyze_csv(content: str) -> Dict[str, Any]:
        """Analyze CSV file"""
        try:
            import csv
            lines = content.split('\n')
            reader = csv.reader(lines)
            rows = list(reader)
            headers = rows[0] if rows else []

            return {
                'type': 'csv',
                'rows': len(rows) - 1,  # Exclude header
                'columns': len(headers),
                'headers': headers,
                'preview': rows[:5]
            }
        except Exception as e:
            return {
                'type': 'csv',
                'error': str(e)
            }

    @staticmethod
    def analyze(filename: str, content: str) -> Dict[str, Any]:
        """Auto-detect and analyze file"""
        ext = filename.split('.')[-1].lower()

        if ext == 'json':
            return FileAnalyzer.analyze_json(content)
        elif ext == 'csv':
            return FileAnalyzer.analyze_csv(content)
        else:
            return FileAnalyzer.analyze_text(content)


class DataVisualizer:
    """Generate visualization data for charts and graphs"""

    @staticmethod
    def generate_chart_data(data: List[Dict], chart_type: str = 'line') -> Dict[str, Any]:
        """Generate chart data from provided data"""
        try:
            if not data:
                return {'success': False, 'error': 'No data provided'}

            # Extract labels and values
            labels = [item.get('label', f'Item {i}') for i, item in enumerate(data)]
            values = [item.get('value', 0) for item in data]

            chart_config = {
                'type': chart_type,
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Data',
                        'data': values,
                        'backgroundColor': [
                            'rgba(255, 99, 132, 0.5)',
                            'rgba(54, 162, 235, 0.5)',
                            'rgba(255, 206, 86, 0.5)',
                            'rgba(75, 192, 192, 0.5)',
                            'rgba(153, 102, 255, 0.5)',
                        ] * (len(values) // 5 + 1)
                    }
                ]
            }

            return {
                'success': True,
                'chart': chart_config,
                'stats': {
                    'count': len(values),
                    'sum': sum(values),
                    'avg': sum(values) / len(values) if values else 0,
                    'max': max(values) if values else 0,
                    'min': min(values) if values else 0,
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    @staticmethod
    def generate_from_csv(rows: List[List]) -> Dict[str, Any]:
        """Generate visualization from CSV data"""
        try:
            if len(rows) < 2:
                return {'success': False, 'error': 'Insufficient data'}

            headers = rows[0]
            data_rows = rows[1:]

            # Convert to chart data
            chart_data = [
                {'label': row[0], 'value': float(row[1]) if len(row) > 1 else 0}
                for row in data_rows if row
            ]

            return DataVisualizer.generate_chart_data(chart_data, 'bar')

        except Exception as e:
            return {'success': False, 'error': str(e)}


# Initialize tools
code_interpreter = CodeInterpreter()
calculator = Calculator()
file_analyzer = FileAnalyzer()
visualizer = DataVisualizer()
