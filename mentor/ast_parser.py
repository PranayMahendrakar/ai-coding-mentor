"""AST Parser - Analyzes Python code structure using Abstract Syntax Trees"""
import ast
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class FunctionInfo:
      name: str
      args: List[str]
      returns: Optional[str]
      docstring: Optional[str]
      line_start: int
      line_end: int
      is_async: bool


@dataclass
class CodeStructure:
      functions: List[FunctionInfo]
      classes: List[Any]
      imports: List[str]
      line_count: int
      syntax_valid: bool
      syntax_error: Optional[str]
      cyclomatic_complexity: int
      max_nesting_depth: int


class ASTParser:
      def parse(self, code: str) -> CodeStructure:
                """Parse Python code and extract structure information."""
                try:
                              tree = ast.parse(code)
                              return CodeStructure(
                                  functions=self._extract_functions(tree),
                                  classes=self._extract_classes(tree),
                                  imports=self._extract_imports(tree),
                                  line_count=len(code.splitlines()),
                                  syntax_valid=True,
                                  syntax_error=None,
                                  cyclomatic_complexity=self._calc_cyclomatic_complexity(tree),
                                  max_nesting_depth=self._calc_max_nesting(tree)
                              )
except SyntaxError as e:
            return CodeStructure(
                              functions=[], classes=[], imports=[],
                              line_count=len(code.splitlines()),
                              syntax_valid=False, syntax_error=str(e),
                              cyclomatic_complexity=0, max_nesting_depth=0
            )

    def _extract_functions(self, tree: ast.AST) -> List[FunctionInfo]:
              functions = []
              for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                              functions.append(FunctionInfo(
                                                                    name=node.name,
                                                                    args=[arg.arg for arg in node.args.args],
                                                                    returns=ast.unparse(node.returns) if node.returns else None,
                                                                    docstring=ast.get_docstring(node),
                                                                    line_start=node.lineno,
                                                                    line_end=getattr(node, 'end_lineno', node.lineno),
                                                                    is_async=isinstance(node, ast.AsyncFunctionDef)
                                              ))
                                      return functions

    def _extract_classes(self, tree: ast.AST) -> List[Dict]:
              classes = []
              for node in ast.walk(tree):
                            if isinstance(node, ast.ClassDef):
                                              classes.append({
                                                                    "name": node.name,
                                                                    "methods": [n.name for n in ast.walk(node) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))],
                                                                    "line": node.lineno
                                              })
                                      return classes

    def _extract_imports(self, tree: ast.AST) -> List[str]:
              imports = []
              for node in ast.walk(tree):
                            if isinstance(node, ast.Import):
                                              imports.extend(alias.name for alias in node.names)
elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                imports.extend(f"{module}.{alias.name}" for alias in node.names)
        return imports

    def _calc_cyclomatic_complexity(self, tree: ast.AST) -> int:
              complexity = 1
              for node in ast.walk(tree):
                            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler,
                                                                                   ast.With, ast.Assert, ast.comprehension)):
                                                                                                     complexity += 1
                elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def _calc_max_nesting(self, tree: ast.AST) -> int:
              def get_depth(node, current=0):
                            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                                              current += 1
                                          max_depth = current
            for child in ast.iter_child_nodes(node):
                              max_depth = max(max_depth, get_depth(child, current))
                          return max_depth
        return get_depth(tree)

    def get_line_info(self, code: str) -> List[Dict[str, Any]]:
              """Get type info for each line of code."""
        lines = code.splitlines()
        result = []
        for i, line in enumerate(lines, 1):
                      stripped = line.strip()
            if not stripped:
                              continue
                          if stripped.startswith("#"):
                                            ltype = "comment"
elif stripped.startswith(('"""', "'''")):
                ltype = "docstring"
elif stripped.startswith(("def ", "async def ")):
                ltype = "function_def"
elif stripped.startswith("class "):
                ltype = "class_def"
elif stripped.startswith(("import ", "from ")):
                ltype = "import"
elif stripped.startswith(("return ", "yield ")):
                  ltype = "return"
elif "=" in stripped and not stripped.startswith(("if ", "while ")):
                  ltype = "assignment"
else:
                  ltype = "statement"
              result.append({"line_number": i, "content": line, "type": ltype})
        return result

    def detect_language(self, code: str) -> str:
              """Basic language detection from code patterns."""
              if re.search(r'\bdef \w+\s*\(|\bimport \w+|\bfrom \w+ import', code):
                            return "python"
                        if re.search(r'\bfunction\s+\w+\s*\(|\bconst\b|\blet\b|\bvar\b', code):
                                      return "javascript"
                                  if re.search(r'\bpublic\s+\w+\s*\(|\bprivate\b|\bSystem\.out', code):
                                                return "java"
                                            if re.search(r'#include\s*<|::\w+|std::', code):
                                                          return "cpp"
                                                      return "unknown"
