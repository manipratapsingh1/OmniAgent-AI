# backend/app/knowledge/code_analyzer.py
"""
Developer Assistant Mode - Code Analysis, Suggestions, Explanations
"""
from typing import Dict, List, Optional, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import ast
import json


class CodeAnalyzer:
    """Analyzes code and provides suggestions"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4", temperature=0.7)
    
    # ============= CODE ANALYSIS =============
    def analyze_code(self, code: str, language: str = "python") -> Dict:
        """Analyze code for issues, style, and improvements"""
        
        analysis = {
            "language": language,
            "syntax_valid": self._check_syntax(code, language),
            "issues": [],
            "suggestions": [],
            "complexity": self._analyze_complexity(code, language),
            "security_concerns": []
        }
        
        if language == "python":
            analysis.update(self._analyze_python(code))
        elif language == "javascript":
            analysis.update(self._analyze_javascript(code))
        
        return analysis
    
    def _check_syntax(self, code: str, language: str) -> bool:
        """Check if code has valid syntax"""
        try:
            if language == "python":
                ast.parse(code)
                return True
            # Add other language parsers as needed
            return True
        except SyntaxError:
            return False
    
    def _analyze_python(self, code: str) -> Dict:
        """Python-specific analysis"""
        issues = []
        
        try:
            tree = ast.parse(code)
            
            # Check for unused variables
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Basic unused variable detection
                    pass
                elif isinstance(node, ast.Import):
                    # Check unused imports
                    pass
        
        except:
            pass
        
        return {
            "python_issues": issues,
            "pep8_violations": self._check_pep8(code)
        }
    
    def _analyze_javascript(self, code: str) -> Dict:
        """JavaScript-specific analysis"""
        # Use regex or other tools for JS analysis
        return {"js_issues": []}
    
    def _check_pep8(self, code: str) -> List[str]:
        """Check PEP8 compliance"""
        violations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # Line length
            if len(line) > 79:
                violations.append(f"Line {i}: Too long ({len(line)} > 79 chars)")
            
            # Trailing whitespace
            if line.rstrip() != line:
                violations.append(f"Line {i}: Trailing whitespace")
        
        return violations
    
    def _analyze_complexity(self, code: str, language: str) -> Dict:
        """Analyze code complexity"""
        lines_of_code = len(code.split('\n'))
        cyclomatic_complexity = self._calculate_cyclomatic_complexity(code, language)
        
        return {
            "lines_of_code": lines_of_code,
            "cyclomatic_complexity": cyclomatic_complexity,
            "rating": self._rate_complexity(cyclomatic_complexity)
        }
    
    def _calculate_cyclomatic_complexity(self, code: str, language: str) -> int:
        """Calculate cyclomatic complexity"""
        if language == "python":
            tree = ast.parse(code)
            complexity = 1
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                    complexity += 1
            
            return complexity
        
        return 1
    
    def _rate_complexity(self, complexity: int) -> str:
        """Rate complexity level"""
        if complexity <= 3:
            return "Low"
        elif complexity <= 7:
            return "Moderate"
        elif complexity <= 10:
            return "High"
        else:
            return "Very High"
    
    # ============= CODE SUGGESTIONS =============
    def suggest_fixes(self, code: str, issues: List[str]) -> List[Dict]:
        """Suggest fixes for identified issues"""
        
        suggest_prompt = PromptTemplate(
            template="""Analyze this code and provide specific fixes for these issues:

Code:
{code}

Issues:
{issues}

For each issue, provide:
1. The problem
2. A code fix
3. Explanation

Format as JSON with 'fixes' array.""",
            input_variables=["code", "issues"]
        )
        
        response = self.llm.invoke(suggest_prompt.format(
            code=code,
            issues="\n".join(issues)
        ))
        
        try:
            return json.loads(response.content).get("fixes", [])
        except:
            return [{"fix": response.content}]
    
    # ============= CODE EXPLANATION =============
    def explain_code(self, code: str) -> Dict:
        """Explain what code does"""
        
        explain_prompt = PromptTemplate(
            template="""Explain this code in detail, as if teaching a junior developer.

Code:
{code}

Provide:
1. High-level purpose
2. Key components/logic
3. Important details
4. Potential improvements

Format as JSON.""",
            input_variables=["code"]
        )
        
        response = self.llm.invoke(explain_prompt.format(code=code))
        
        try:
            return json.loads(response.content)
        except:
            return {"explanation": response.content}
    
    # ============= REFACTORING SUGGESTIONS =============
    def suggest_refactoring(self, code: str) -> Dict:
        """Suggest refactoring improvements"""
        
        refactor_prompt = PromptTemplate(
            template="""Suggest refactoring improvements for this code:

{code}

Provide suggestions for:
1. Code duplication
2. Function extraction
3. Naming improvements
4. Structure improvements
5. Performance optimizations

Format as JSON with 'suggestions' array.""",
            input_variables=["code"]
        )
        
        response = self.llm.invoke(refactor_prompt.format(code=code))
        
        try:
            return json.loads(response.content)
        except:
            return {"suggestions": [response.content]}
    
    # ============= DEPENDENCY ANALYSIS =============
    def analyze_dependencies(self, code: str, language: str = "python") -> Dict:
        """Analyze code dependencies"""
        
        if language == "python":
            tree = ast.parse(code)
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append({"module": alias.name, "type": "import"})
                elif isinstance(node, ast.ImportFrom):
                    imports.append({
                        "module": node.module,
                        "items": [alias.name for alias in node.names],
                        "type": "from_import"
                    })
            
            return {
                "language": language,
                "imports": imports,
                "external_dependencies": self._filter_external(imports)
            }
        
        return {"error": "Language not supported"}
    
    def _filter_external(self, imports: List[Dict]) -> List[str]:
        """Filter external (non-stdlib) dependencies"""
        stdlib = {
            "os", "sys", "re", "json", "datetime", "time", "math",
            "random", "collections", "itertools", "functools", "abc"
        }
        
        external = []
        for imp in imports:
            module = imp.get("module", "").split(".")[0]
            if module and module not in stdlib:
                external.append(module)
        
        return list(set(external))
  