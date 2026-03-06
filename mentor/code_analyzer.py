"""Code Analyzer - Core analysis engine combining Llama AI with AST parsing"""
import logging
from typing import Dict, Any
from .llama_client import LlamaClient
from .ast_parser import ASTParser

logger = logging.getLogger(__name__)

TEACHER_SYSTEM = "You are an expert programming teacher. Be clear, educational, and use markdown formatting."
ELI5_SYSTEM = "Explain code like the person is 5 years old. Use simple words and fun analogies. Avoid jargon."


class CodeAnalyzer:
      def __init__(self, llama_client: LlamaClient, ast_parser: ASTParser):
                self.llama = llama_client
                self.parser = ast_parser

      async def explain_code(self, code: str, language: str = "python", eli5: bool = False) -> Dict[str, Any]:
                """Explain code line by line like a teacher."""
                structure = self.parser.parse(code) if language == "python" else None
                system = ELI5_SYSTEM if eli5 else TEACHER_SYSTEM
                if eli5:
                              prompt = f"Explain this {language} code like I am 5 years old using simple words and fun analogies:\n\n```{language}\n{code}\n```"
else:
            prompt = f"""Explain this {language} code line by line like a teacher:

            ```{language}
            {code}
            ```

            Provide:
            1. **Overview**: What does this code do?
            2. **Line-by-Line**: Explain each important line
            3. **Key Concepts**: What programming concepts are used?
            4. **Execution Flow**: How does it run step by step?"""

        explanation = await self.llama.generate(prompt, system=system)
        result = {"explanation": explanation, "eli5_mode": eli5, "language": language, "line_count": len(code.splitlines())}
        if structure:
                      result["structure"] = {
                                        "functions": [f.name for f in structure.functions],
                                        "classes": [c.get("name", "") for c in structure.classes],
                                        "imports": structure.imports[:10],
                                        "syntax_valid": structure.syntax_valid,
                                        "syntax_error": structure.syntax_error
                      }
                  return result

    async def suggest_improvements(self, code: str, language: str = "python") -> Dict[str, Any]:
              """Suggest code improvements."""
              structure = self.parser.parse(code) if language == "python" else None
              metrics = f"Complexity: {structure.cyclomatic_complexity}, Nesting: {structure.max_nesting_depth}" if structure else ""
              prompt = f"""Analyze this {language} code and suggest improvements. {metrics}

      ```{language}
      {code}
      ```

      Categories:
      1. **Code Quality** - Readability, naming, style
      2. **Performance** - Efficiency improvements
      3. **Best Practices** - Language-specific conventions
      4. **Error Handling** - Robustness
      5. **Documentation** - Missing docs
      6. **Security** - Any concerns

      Show BEFORE/AFTER for each suggestion."""

        suggestions = await self.llama.generate(prompt, system=TEACHER_SYSTEM)
        return {
                      "suggestions": suggestions, "language": language,
                      "complexity_score": structure.cyclomatic_complexity if structure else None,
                      "has_syntax_errors": not structure.syntax_valid if structure else False
        }

    async def generate_tests(self, code: str, language: str = "python") -> Dict[str, Any]:
              """Generate unit tests."""
              structure = self.parser.parse(code) if language == "python" else None
              fn_list = ", ".join(f.name for f in structure.functions) if structure and structure.functions else "all functions"
              prompt = f"""Generate comprehensive unit tests for: {fn_list}

      ```{language}
      {code}
      ```

      Cover: Happy path, edge cases, error cases, boundary values. Use pytest for Python."""

        tests = await self.llama.generate(prompt, system=TEACHER_SYSTEM)
        return {
                      "tests": tests, "language": language,
                      "functions_tested": [f.name for f in structure.functions] if structure else [],
                      "test_framework": "pytest" if language == "python" else "jest"
        }

    async def analyze_complexity(self, code: str, language: str = "python") -> Dict[str, Any]:
              """Analyze time and space complexity."""
              structure = self.parser.parse(code) if language == "python" else None
              ast_metrics = {}
              if structure:
                            ast_metrics = {
                                              "cyclomatic_complexity": structure.cyclomatic_complexity,
                                              "max_nesting_depth": structure.max_nesting_depth,
                                              "function_count": len(structure.functions),
                                              "line_count": structure.line_count
                            }
                            cc, nd = structure.cyclomatic_complexity, structure.max_nesting_depth
                            if cc <= 2 and nd <= 1: rating = "O(1) to O(n)"
              elif cc <= 5 and nd <= 2: rating = "O(n) to O(n log n)"
elif cc <= 10 and nd <= 3: rating = "O(n^2)"
else: rating = "O(n^2) or higher"
else:
            rating = "Unknown"

        prompt = f"""Analyze time and space complexity of this {language} code:

        ```{language}
        {code}
        ```

        Provide:
        1. **Time Complexity** - Big O notation with explanation
        2. **Space Complexity** - Memory usage
        3. **Per-Function Analysis**
        4. **Bottlenecks** - Most expensive operations
        5. **Optimization Tips**"""

        analysis = await self.llama.generate(prompt, system=TEACHER_SYSTEM)
        return {"analysis": analysis, "ast_metrics": ast_metrics, "estimated_complexity": rating, "language": language}

    async def debug_code(self, code: str, error_message: str = "", language: str = "python") -> Dict[str, Any]:
              """Provide debugging suggestions."""
              structure = self.parser.parse(code) if language == "python" else None
              error_ctx = f"\nError: {error_message}" if error_message else ""
              syntax_ctx = f"\nSyntax error: {structure.syntax_error}" if structure and not structure.syntax_valid else ""
              prompt = f"""Debug this {language} code:{error_ctx}{syntax_ctx}

      ```{language}
      {code}
      ```

      Provide:
      1. **Problem Diagnosis** - What's wrong
      2. **Root Cause** - Why it happens
      3. **Step-by-Step Fix**
      4. **Fixed Code** - Corrected version
      5. **Prevention** - Avoid in future"""

        debug_info = await self.llama.generate(prompt, system=TEACHER_SYSTEM)
        return {
                      "debug_suggestions": debug_info,
                      "has_syntax_error": structure and not structure.syntax_valid if structure else False,
                      "syntax_error_detail": structure.syntax_error if structure and not structure.syntax_valid else None,
                      "error_provided": bool(error_message), "language": language
        }

    async def analyze_all(self, code: str, language: str = "python", eli5: bool = False) -> Dict[str, Any]:
              """Run all analyses."""
              import asyncio
              results = await asyncio.gather(
                  self.explain_code(code, language, eli5),
                  self.suggest_improvements(code, language),
                  self.analyze_complexity(code, language),
                  return_exceptions=True
              )
              def safe(r, k): return r if not isinstance(r, Exception) else {k: str(r)}
                        return {
                                      "explanation": safe(results[0], "explanation"),
                                      "improvements": safe(results[1], "suggestions"),
                                      "complexity": safe(results[2], "analysis"),
                                      "language": language, "eli5_mode": eli5
                        }
