"""
Code Analysis Pipeline
Analyzes source code files through multiple stages:
1. Metadata extraction
2. Static analysis
3. AI documentation generation
4. Quality assessment
"""

import re
from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class CodeMetadata:
    """Metadata extracted from source code"""
    language: str = ""
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)


@dataclass
class StaticAnalysisResult:
    """Results from static code analysis"""
    issues: List[Dict[str, Any]] = field(default_factory=list)
    complexity_score: int = 0
    code_smells: List[str] = field(default_factory=list)


@dataclass
class PipelineResult:
    """Complete pipeline analysis result"""
    metadata: CodeMetadata
    static_analysis: StaticAnalysisResult
    ai_documentation: str = ""
    quality_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)


class MetadataExtractor:
    """Stage 1: Extract metadata from code"""

    LANGUAGE_PATTERNS = {
        'python': r'\.py$',
        'javascript': r'\.(js|jsx)$',
        'typescript': r'\.(ts|tsx)$',
        'java': r'\.java$',
        'go': r'\.go$',
        'rust': r'\.rs$',
        'c++': r'\.(cpp|cc|cxx|hpp|h)$',
    }

    def detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        for lang, pattern in self.LANGUAGE_PATTERNS.items():
            if re.search(pattern, file_path):
                return lang
        return "unknown"

    def extract(self, code: str, file_path: str) -> CodeMetadata:
        """Extract metadata from source code"""
        metadata = CodeMetadata()
        metadata.language = self.detect_language(file_path)

        lines = code.split('\n')
        metadata.total_lines = len(lines)

        for line in lines:
            stripped = line.strip()
            if not stripped:
                metadata.blank_lines += 1
            elif self._is_comment(stripped, metadata.language):
                metadata.comment_lines += 1
            else:
                metadata.code_lines += 1

        # Extract functions and classes based on language
        if metadata.language == 'python':
            metadata.functions = self._extract_python_functions(code)
            metadata.classes = self._extract_python_classes(code)
            metadata.imports = self._extract_python_imports(code)
        elif metadata.language in ['javascript', 'typescript']:
            metadata.functions = self._extract_js_functions(code)
            metadata.classes = self._extract_js_classes(code)
            metadata.imports = self._extract_js_imports(code)

        return metadata

    def _is_comment(self, line: str, language: str) -> bool:
        """Check if line is a comment"""
        if language == 'python':
            return line.startswith('#')
        elif language in ['javascript', 'typescript', 'java', 'c++', 'go', 'rust']:
            return line.startswith('//') or line.startswith('/*') or line.startswith('*')
        return False

    def _extract_python_functions(self, code: str) -> List[str]:
        """Extract function names from Python code"""
        pattern = r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
        return re.findall(pattern, code, re.MULTILINE)

    def _extract_python_classes(self, code: str) -> List[str]:
        """Extract class names from Python code"""
        pattern = r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]'
        return re.findall(pattern, code, re.MULTILINE)

    def _extract_python_imports(self, code: str) -> List[str]:
        """Extract imports from Python code"""
        pattern = r'^\s*(?:from\s+([a-zA-Z0-9_.]+)\s+)?import\s+([a-zA-Z0-9_., ]+)'
        matches = re.findall(pattern, code, re.MULTILINE)
        imports = []
        for from_module, import_items in matches:
            if from_module:
                imports.append(f"from {from_module} import {import_items}")
            else:
                imports.append(f"import {import_items}")
        return imports

    def _extract_js_functions(self, code: str) -> List[str]:
        """Extract function names from JavaScript/TypeScript code"""
        patterns = [
            r'function\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*\(',
            r'const\s+([a-zA-Z_$][a-zA-Z0-9_$]*)\s*=\s*\([^)]*\)\s*=>',
            r'([a-zA-Z_$][a-zA-Z0-9_$]*)\s*:\s*\([^)]*\)\s*=>',
        ]
        functions = []
        for pattern in patterns:
            functions.extend(re.findall(pattern, code))
        return list(set(functions))

    def _extract_js_classes(self, code: str) -> List[str]:
        """Extract class names from JavaScript/TypeScript code"""
        pattern = r'class\s+([a-zA-Z_$][a-zA-Z0-9_$]*)'
        return re.findall(pattern, code)

    def _extract_js_imports(self, code: str) -> List[str]:
        """Extract imports from JavaScript/TypeScript code"""
        pattern = r'import\s+.+?\s+from\s+[\'"]([^\'"]+)[\'"]'
        return re.findall(pattern, code)


class StaticAnalyzer:
    """Stage 2: Perform static code analysis"""

    def analyze(self, code: str, metadata: CodeMetadata) -> StaticAnalysisResult:
        """Analyze code for issues and code smells"""
        result = StaticAnalysisResult()

        # Calculate cyclomatic complexity
        result.complexity_score = self._calculate_complexity(code, metadata.language)

        # Detect code smells
        result.code_smells = self._detect_code_smells(code, metadata)

        # Find common issues
        result.issues = self._find_issues(code, metadata)

        return result

    def _calculate_complexity(self, code: str, language: str) -> int:
        """Calculate approximate average cyclomatic complexity per function"""
        # Count decision points
        decision_keywords = ['if', 'elif', 'else', 'for', 'while', 'case', 'catch', 'and', 'or']

        total_decision_points = 0

        for keyword in decision_keywords:
            if language == 'python':
                pattern = r'\b' + keyword + r'\b'
            else:
                pattern = r'\b' + keyword + r'\b' if keyword.isalpha() else re.escape(keyword)

            total_decision_points += len(re.findall(pattern, code))

        # Calculate base complexity (1 per function + decision points)
        # If we have function count from metadata, use it; otherwise estimate
        function_count = 0

        if language == 'python':
            function_count = len(re.findall(r'^\s*def\s+', code, re.MULTILINE))
        elif language in ['javascript', 'typescript']:
            function_count = len(re.findall(r'function\s+\w+|const\s+\w+\s*=.*=>|\w+\s*:\s*\(.*\)\s*=>', code))

        # Avoid division by zero
        if function_count == 0:
            function_count = 1

        # Average complexity per function
        avg_complexity = (function_count + total_decision_points) // function_count

        return max(1, avg_complexity)  # Minimum complexity is 1

    def _detect_code_smells(self, code: str, metadata: CodeMetadata) -> List[str]:
        """Detect common code smells"""
        smells = []

        # Long functions
        if metadata.language == 'python':
            functions = self._get_function_lengths_python(code)
            for func, length in functions.items():
                if length > 50:
                    smells.append(f"Long function '{func}' ({length} lines)")

        # Too many functions
        if len(metadata.functions) > 20:
            smells.append(f"Too many functions ({len(metadata.functions)}) - consider splitting module")

        # Low comment ratio
        if metadata.code_lines > 0:
            comment_ratio = metadata.comment_lines / metadata.code_lines
            if comment_ratio < 0.05:
                smells.append(f"Low comment ratio ({comment_ratio:.1%}) - consider adding more documentation")

        # Magic numbers
        magic_numbers = re.findall(r'\b\d{2,}\b', code)
        if len(magic_numbers) > 5:
            smells.append("Multiple magic numbers detected - consider using named constants")

        return smells

    def _get_function_lengths_python(self, code: str) -> Dict[str, int]:
        """Get length of each Python function"""
        lines = code.split('\n')
        functions = {}
        current_function = None
        function_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith('def '):
                if current_function:
                    functions[current_function] = i - function_start
                match = re.match(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)', stripped)
                if match:
                    current_function = match.group(1)
                    function_start = i
            elif current_function and line and not line[0].isspace():
                # Function ended
                functions[current_function] = i - function_start
                current_function = None

        if current_function:
            functions[current_function] = len(lines) - function_start

        return functions

    def _find_issues(self, code: str, metadata: CodeMetadata) -> List[Dict[str, Any]]:
        """Find common coding issues"""
        issues = []

        lines = code.split('\n')

        for i, line in enumerate(lines, 1):
            # Line too long
            if len(line) > 120:
                issues.append({
                    'line': i,
                    'type': 'style',
                    'severity': 'low',
                    'message': f'Line too long ({len(line)} characters)'
                })

            # TODO/FIXME comments
            if 'TODO' in line or 'FIXME' in line:
                issues.append({
                    'line': i,
                    'type': 'maintenance',
                    'severity': 'info',
                    'message': 'TODO/FIXME comment found'
                })

            # Potential security issues (basic check)
            if metadata.language == 'python':
                if 'eval(' in line or 'exec(' in line:
                    issues.append({
                        'line': i,
                        'type': 'security',
                        'severity': 'high',
                        'message': 'Use of eval/exec is potentially dangerous'
                    })

        return issues


class QualityAssessor:
    """Stage 4: Assess overall code quality"""

    def assess(self, metadata: CodeMetadata, static_analysis: StaticAnalysisResult) -> tuple[float, List[str]]:
        """Calculate quality score and generate recommendations"""
        score = 100.0
        recommendations = []

        # Penalize based on complexity
        if static_analysis.complexity_score > 20:
            score -= 15
            recommendations.append("High complexity detected - consider refactoring to simplify logic")
        elif static_analysis.complexity_score > 10:
            score -= 5
            recommendations.append("Moderate complexity - review complex functions")

        # Penalize based on code smells
        score -= len(static_analysis.code_smells) * 3
        if static_analysis.code_smells:
            recommendations.append(f"Address {len(static_analysis.code_smells)} code smell(s)")

        # Penalize based on issues
        high_severity = sum(1 for issue in static_analysis.issues if issue['severity'] == 'high')
        medium_severity = sum(1 for issue in static_analysis.issues if issue['severity'] == 'medium')

        score -= high_severity * 10
        score -= medium_severity * 5

        if high_severity > 0:
            recommendations.append(f"Fix {high_severity} high-severity issue(s) immediately")

        # Reward good practices
        if metadata.code_lines > 0:
            comment_ratio = metadata.comment_lines / metadata.code_lines
            if comment_ratio > 0.2:
                score += 5
            elif comment_ratio < 0.05:
                recommendations.append("Add more comments and documentation")

        # Check function count
        if metadata.functions and metadata.code_lines > 0:
            lines_per_function = metadata.code_lines / len(metadata.functions)
            if lines_per_function < 30:
                score += 5  # Good modularization
            elif lines_per_function > 100:
                recommendations.append("Functions are too large on average - increase modularization")

        score = max(0, min(100, score))  # Clamp between 0 and 100

        return score, recommendations
