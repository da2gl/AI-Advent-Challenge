"""
Pipeline Executor
Orchestrates the code analysis pipeline through all stages
"""

import json
from .code_analyzer import (
    MetadataExtractor,
    StaticAnalyzer,
    QualityAssessor,
    PipelineResult,
    CodeMetadata,
    StaticAnalysisResult,
)


class CodeAnalysisPipeline:
    """Main pipeline executor that coordinates all stages"""

    def __init__(self, gemini_client=None):
        """
        Initialize pipeline with all stages

        Args:
            gemini_client: Optional Gemini client for AI documentation generation
        """
        self.metadata_extractor = MetadataExtractor()
        self.static_analyzer = StaticAnalyzer()
        self.quality_assessor = QualityAssessor()
        self.gemini_client = gemini_client

    def analyze_file(self, file_path: str) -> PipelineResult:
        """
        Analyze a source code file through the complete pipeline

        Args:
            file_path: Path to the source code file

        Returns:
            PipelineResult with all analysis stages
        """
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        return self.analyze_code(code, file_path)

    def analyze_code(self, code: str, file_path: str = "unknown") -> PipelineResult:
        """
        Analyze source code through the complete pipeline

        Args:
            code: Source code content
            file_path: Optional file path for language detection

        Returns:
            PipelineResult with all analysis stages
        """
        # Stage 1: Extract metadata
        print("Stage 1/4: Extracting metadata...")
        metadata = self.metadata_extractor.extract(code, file_path)

        # Stage 2: Static analysis
        print("Stage 2/4: Performing static analysis...")
        static_analysis = self.static_analyzer.analyze(code, metadata)

        # Stage 3: Generate AI documentation
        print("Stage 3/4: Generating AI documentation...")
        ai_documentation = self._generate_documentation(code, metadata, static_analysis)

        # Stage 4: Quality assessment
        print("Stage 4/4: Assessing code quality...")
        quality_score, recommendations = self.quality_assessor.assess(metadata, static_analysis)

        # Build result
        result = PipelineResult(
            metadata=metadata,
            static_analysis=static_analysis,
            ai_documentation=ai_documentation,
            quality_score=quality_score,
            recommendations=recommendations
        )

        return result

    def _generate_documentation(
        self,
        code: str,
        metadata: CodeMetadata,
        static_analysis: StaticAnalysisResult
    ) -> str:
        """Generate documentation using Gemini AI"""
        if not self.gemini_client:
            return "AI documentation not available (no Gemini client provided)"

        # Truncate code preview to first 30 lines
        code_lines = code.split('\n')[:30]
        code_preview = '\n'.join(code_lines)
        if len(code.split('\n')) > 30:
            code_preview += "\n... (truncated)"

        # Generate documentation
        prompt = f"""Analyze this {metadata.language} code snippet:

```{metadata.language}
{code_preview}
```

Statistics:
- Lines: {metadata.code_lines}
- Functions: {len(metadata.functions)}
- Classes: {len(metadata.classes)}
- Complexity: {static_analysis.complexity_score}

Provide a brief analysis (3-4 sentences):
1. What does this code do?
2. Key components
3. Main concerns or improvements needed
"""

        try:
            response = self.gemini_client.generate_content(prompt)
            return response
        except Exception as e:
            return f"Error generating AI documentation: {str(e)}"

    def _prepare_ai_context(
        self,
        code: str,
        metadata: CodeMetadata,
        static_analysis: StaticAnalysisResult
    ) -> str:
        """Prepare context information for AI"""
        context_parts = []

        if metadata.functions:
            context_parts.append(f"Functions: {', '.join(metadata.functions[:10])}")
            if len(metadata.functions) > 10:
                context_parts.append(f"... and {len(metadata.functions) - 10} more")

        if metadata.classes:
            context_parts.append(f"Classes: {', '.join(metadata.classes)}")

        if metadata.imports:
            context_parts.append(f"Imports: {', '.join(metadata.imports[:5])}")
            if len(metadata.imports) > 5:
                context_parts.append(f"... and {len(metadata.imports) - 5} more")

        if static_analysis.code_smells:
            context_parts.append(f"\nCode smells detected: {len(static_analysis.code_smells)}")

        # Include a preview of the code (first 50 lines max)
        code_preview = '\n'.join(code.split('\n')[:50])
        context_parts.append(f"\nCode preview:\n```{metadata.language}\n{code_preview}\n```")

        return '\n'.join(context_parts)

    def format_result(self, result: PipelineResult, detailed: bool = True) -> str:
        """
        Format analysis result as human-readable text

        Args:
            result: Pipeline analysis result
            detailed: Whether to include detailed information

        Returns:
            Formatted string representation
        """
        lines = []

        lines.append("=" * 70)
        lines.append("CODE ANALYSIS REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Metadata
        lines.append("METADATA")
        lines.append("-" * 70)
        lines.append(f"Language:      {result.metadata.language}")
        lines.append(f"Total lines:   {result.metadata.total_lines}")
        lines.append(f"Code lines:    {result.metadata.code_lines}")
        lines.append(f"Comment lines: {result.metadata.comment_lines}")
        lines.append(f"Blank lines:   {result.metadata.blank_lines}")
        lines.append(f"Functions:     {len(result.metadata.functions)}")
        lines.append(f"Classes:       {len(result.metadata.classes)}")
        lines.append(f"Imports:       {len(result.metadata.imports)}")
        lines.append("")

        if detailed and result.metadata.functions:
            lines.append(f"Function list: {', '.join(result.metadata.functions[:10])}")
            if len(result.metadata.functions) > 10:
                lines.append(f"               ... and {len(result.metadata.functions) - 10} more")
            lines.append("")

        # Static Analysis
        lines.append("STATIC ANALYSIS")
        lines.append("-" * 70)
        lines.append(f"Complexity score: {result.static_analysis.complexity_score}")
        lines.append(f"Issues found:     {len(result.static_analysis.issues)}")
        lines.append(f"Code smells:      {len(result.static_analysis.code_smells)}")
        lines.append("")

        if result.static_analysis.code_smells:
            lines.append("Code Smells:")
            for smell in result.static_analysis.code_smells:
                lines.append(f"  - {smell}")
            lines.append("")

        if detailed and result.static_analysis.issues:
            lines.append("Issues (first 10):")
            for issue in result.static_analysis.issues[:10]:
                severity_marker = "⚠️" if issue['severity'] == 'high' else "ℹ️"
                lines.append(f"  {severity_marker} Line {issue['line']}: {issue['message']}")
            if len(result.static_analysis.issues) > 10:
                lines.append(f"  ... and {len(result.static_analysis.issues) - 10} more issues")
            lines.append("")

        # Quality Assessment
        lines.append("QUALITY ASSESSMENT")
        lines.append("-" * 70)
        lines.append(f"Quality Score: {result.quality_score:.1f}/100")

        # Add quality rating
        if result.quality_score >= 90:
            rating = "Excellent"
        elif result.quality_score >= 75:
            rating = "Good"
        elif result.quality_score >= 60:
            rating = "Fair"
        else:
            rating = "Needs Improvement"
        lines.append(f"Rating: {rating}")
        lines.append("")

        if result.recommendations:
            lines.append("Recommendations:")
            for rec in result.recommendations:
                lines.append(f"  - {rec}")
            lines.append("")

        # AI Documentation
        if result.ai_documentation:
            lines.append("AI-GENERATED DOCUMENTATION")
            lines.append("-" * 70)
            lines.append(result.ai_documentation)
            lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)

    def save_result(self, result: PipelineResult, output_path: str, format: str = 'txt'):
        """
        Save analysis result to file

        Args:
            result: Pipeline analysis result
            output_path: Path to save the result
            format: Output format ('txt' or 'json')
        """
        if format == 'json':
            # Convert to dict
            result_dict = {
                'metadata': {
                    'language': result.metadata.language,
                    'total_lines': result.metadata.total_lines,
                    'code_lines': result.metadata.code_lines,
                    'comment_lines': result.metadata.comment_lines,
                    'blank_lines': result.metadata.blank_lines,
                    'functions': result.metadata.functions,
                    'classes': result.metadata.classes,
                    'imports': result.metadata.imports,
                },
                'static_analysis': {
                    'complexity_score': result.static_analysis.complexity_score,
                    'issues': result.static_analysis.issues,
                    'code_smells': result.static_analysis.code_smells,
                },
                'ai_documentation': result.ai_documentation,
                'quality_score': result.quality_score,
                'recommendations': result.recommendations,
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_dict, f, indent=2, ensure_ascii=False)
        else:
            # Save as text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(self.format_result(result, detailed=True))

        print(f"Results saved to: {output_path}")
