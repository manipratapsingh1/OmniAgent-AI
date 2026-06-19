"""
Advanced Tools Service - Code Interpreter, Calculator, File Analyzer
Provides ChatGPT/Gemini-like tool capabilities
"""

import json
import math
import traceback
import ast
import operator as op
import sys
import io
import signal
from typing import Any, Dict, List, Optional
from contextlib import redirect_stdout, redirect_stderr
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
        """Execute Python code with sandboxing and stdout capture"""
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
                    'map': map,
                    'filter': filter,
                    'reversed': reversed,
                    'type': type,
                    'isinstance': isinstance,
                    'hasattr': hasattr,
                    'getattr': getattr,
                    'repr': repr,
                    'format': format,
                    'chr': chr,
                    'ord': ord,
                    'hex': hex,
                    'bin': bin,
                    'oct': oct,
                },
                **self.ALLOWED_MODULES,
                'variables': variables or {},
            }

            # Block dangerous operations
            dangerous_imports = ['os', 'sys', 'subprocess', 'socket', 'urllib', 'requests', 'shutil', 'pathlib']
            for dangerous in dangerous_imports:
                if dangerous in code.lower():
                    return {
                        'success': False,
                        'error': f'Cannot import {dangerous} - restricted for security',
                        'code': code
                    }

            # Capture stdout and stderr
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()

            exec_globals = safe_dict.copy()
            exec_locals = {}

            # Execute code with stdout/stderr capture
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                exec(code, exec_globals, exec_locals)

            # Get captured output
            stdout_output = stdout_capture.getvalue()
            stderr_output = stderr_capture.getvalue()

            # Extract results: prefer 'result' variable, then all locals
            output = exec_locals.get('result', None)
            if output is None:
                local_vars = {k: v for k, v in exec_locals.items() if not k.startswith('_')}
                if local_vars:
                    output = local_vars

            # Build combined output string
            output_parts = []
            if stdout_output:
                output_parts.append(stdout_output.rstrip())
            if output is not None:
                output_parts.append(str(output))
            if stderr_output:
                output_parts.append(f"[stderr] {stderr_output.rstrip()}")

            combined_output = "\n".join(output_parts) if output_parts else "(no output)"

            log.info("code_execution.success", code_len=len(code), has_stdout=bool(stdout_output))

            return {
                'success': True,
                'result': output,
                'code': code,
                'output': combined_output,
                'stdout': stdout_output,
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
    """Advanced calculator with safe AST-based evaluation"""

    # AST-safe operators
    _OPS = {
        ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv,
        ast.Pow: op.pow, ast.Mod: op.mod, ast.USub: op.neg, ast.FloorDiv: op.floordiv,
    }

    # Safe math functions
    _FUNCS = {
        "sin": math.sin, "cos": math.cos, "tan": math.tan,
        "sqrt": math.sqrt, "log": math.log, "ln": math.log,
        "exp": math.exp, "abs": abs, "round": round, "pow": math.pow,
        "ceil": math.ceil, "floor": math.floor, "factorial": math.factorial,
        "asin": math.asin, "acos": math.acos, "atan": math.atan,
        "degrees": math.degrees, "radians": math.radians,
    }

    # Constants
    _CONSTS = {"pi": math.pi, "e": math.e, "tau": math.tau, "inf": math.inf}

    @staticmethod
    def _eval_node(node):
        """Recursively evaluate AST nodes safely."""
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in Calculator._CONSTS:
                return Calculator._CONSTS[node.id]
            raise ValueError(f"Unknown variable: {node.id}")
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in Calculator._FUNCS:
                args = [Calculator._eval_node(arg) for arg in node.args]
                return Calculator._FUNCS[node.func.id](*args)
            raise ValueError(f"Unsupported function: {getattr(node.func, 'id', '?')}")
        if isinstance(node, ast.BinOp):
            op_type = type(node.op)
            if op_type not in Calculator._OPS:
                raise ValueError(f"Unsupported operator: {op_type.__name__}")
            return Calculator._OPS[op_type](Calculator._eval_node(node.left), Calculator._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_type = type(node.op)
            if op_type not in Calculator._OPS:
                raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
            return Calculator._OPS[op_type](Calculator._eval_node(node.operand))
        raise ValueError("Unsupported expression")

    @staticmethod
    def evaluate(expression: str) -> Dict[str, Any]:
        """Safely evaluate mathematical expression using AST parsing (no eval)"""
        try:
            if not expression or not expression.strip():
                return {'success': False, 'error': 'Empty expression'}

            # Pre-filter for restricted terms to match test assertions
            restricted = ['import', 'exec', 'eval', '__', 'open', 'file']
            for restricted_word in restricted:
                if restricted_word in expression.lower():
                    return {
                        'success': False,
                        'error': f'Operation {restricted_word} not allowed',
                        'expression': expression
                    }

            tree = ast.parse(expression.strip(), mode="eval")
            result = Calculator._eval_node(tree.body)

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
    """Analyze uploaded files and extract information (supports TXT, JSON, CSV, PDF, DOCX, XLSX, PPTX)"""

    SUPPORTED_FORMATS = {
        'txt': 'text',
        'json': 'json',
        'csv': 'csv',
        'md': 'markdown',
        'log': 'log',
        'pdf': 'pdf',
        'docx': 'docx',
        'xlsx': 'xlsx',
        'pptx': 'pptx',
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
                'rows': max(0, len(rows) - 1),  # Exclude header
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
    def analyze(filename: str, raw_bytes: bytes, text_content: Optional[str] = None) -> Dict[str, Any]:
        """Auto-detect and analyze file from raw bytes or text content"""
        ext = filename.split('.')[-1].lower()

        if not text_content:
            if ext in ('pdf', 'docx', 'xlsx', 'pptx', 'png', 'jpg', 'jpeg', 'webp', 'bmp'):
                try:
                    from app.rag.ingest import _extract_text
                    text_content = _extract_text(filename, raw_bytes)
                except Exception as e:
                    log.warning("file_analyzer.extract_failed", filename=filename, error=str(e))
                    text_content = ""
            else:
                try:
                    text_content = raw_bytes.decode('utf-8', errors='ignore')
                except Exception:
                    text_content = ""

        if ext == 'json':
            return FileAnalyzer.analyze_json(text_content)
        elif ext == 'csv':
            return FileAnalyzer.analyze_csv(text_content)

        words = text_content.split()
        lines = text_content.split('\n')
        wc = len(words)
        lc = len(lines)
        cc = len(text_content)

        # Basic key phrase extraction from the text using a simple Counter
        from collections import Counter
        from app.rag.query_rewriter import _STOP_WORDS
        clean_words = [w.strip(".,;:!?()\"'").lower() for w in words if len(w) > 4]
        meaningful_words = [w for w in clean_words if w not in _STOP_WORDS]
        most_common = [word for word, count in Counter(meaningful_words).most_common(5)]

        return {
            'type': ext,
            'lines': lc,
            'words': wc,
            'characters': cc,
            'key_phrases': most_common,
            'preview': text_content[:600] + ('...' if len(text_content) > 600 else ''),
            'avg_line_length': cc / lc if lc else 0,
            'unique_words': len(set(clean_words)),
        }


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
