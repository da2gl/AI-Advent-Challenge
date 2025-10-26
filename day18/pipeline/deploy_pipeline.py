"""
Deployment Pipeline Executor
Orchestrates all stages of the deployment pipeline
"""

from dataclasses import dataclass
from typing import Optional, Dict

from .project_validator import ProjectValidator, ValidationResult
from .build_preparer import BuildPreparer, BuildResult
from .deployment_engine import DeploymentEngine


@dataclass
class PipelineStage:
    """Represents a single pipeline stage"""
    name: str
    status: str  # pending, running, success, error
    message: str
    details: Optional[Dict] = None


class DeploymentPipeline:
    """Main deployment pipeline orchestrator"""

    def __init__(self, gemini_client=None, project_root: str = '.'):
        """
        Initialize deployment pipeline

        Args:
            gemini_client: Optional Gemini client for AI-powered recommendations
            project_root: Root directory of the project
        """
        self.gemini_client = gemini_client
        self.project_root = project_root
        self.validator = ProjectValidator(project_root)
        self.build_preparer = BuildPreparer(project_root)
        self.deployment_engine = DeploymentEngine(project_root)

        self.stages = [
            PipelineStage('Validation', 'pending', 'Waiting...'),
            PipelineStage('Build Preparation', 'pending', 'Waiting...'),
            PipelineStage('AI Analysis', 'pending', 'Waiting...'),
            PipelineStage('Deployment', 'pending', 'Waiting...')
        ]

    def deploy(self, platform: str = 'railway') -> Dict:
        """
        Execute full deployment pipeline

        Args:
            platform: Target deployment platform

        Returns:
            Dictionary with deployment results and stage information
        """
        # Stage 1: Validation
        self._update_stage(0, 'running', 'Validating project structure...')
        validation_result = self.validator.validate()

        if not validation_result.valid:
            self._update_stage(0, 'error', f'Validation failed: {len(validation_result.issues)} issues')
            return self._build_response('error', validation_result=validation_result)

        self._update_stage(0, 'success', 'Project validated successfully')

        # Stage 2: Build Preparation
        self._update_stage(1, 'running', f'Preparing build for {platform}...')
        build_result = self.build_preparer.prepare(platform=platform)

        if not build_result.success:
            self._update_stage(1, 'error', f'Build preparation failed')
            return self._build_response('error', validation_result=validation_result, build_result=build_result)

        self._update_stage(1, 'success', f'Generated {len(build_result.artifacts)} artifacts')

        # Stage 3: AI Analysis
        self._update_stage(2, 'running', 'Analyzing deployment with AI...')
        ai_recommendations = self._get_ai_recommendations(validation_result, build_result, platform)
        self._update_stage(2, 'success', 'AI analysis complete')

        # Stage 4: Deployment
        self._update_stage(3, 'running', f'Deploying to {platform}...')
        deployment_result = self.deployment_engine.deploy(platform=platform)

        if not deployment_result.success:
            self._update_stage(3, 'error', 'Deployment failed')
            return self._build_response(
                'error',
                validation_result=validation_result,
                build_result=build_result,
                deployment_result=deployment_result,
                ai_recommendations=ai_recommendations
            )

        self._update_stage(3, 'success', f'Deployed to {deployment_result.url or platform}')

        return self._build_response(
            'success',
            validation_result=validation_result,
            build_result=build_result,
            deployment_result=deployment_result,
            ai_recommendations=ai_recommendations
        )

    def _update_stage(self, index: int, status: str, message: str):
        """Update a pipeline stage"""
        if 0 <= index < len(self.stages):
            self.stages[index].status = status
            self.stages[index].message = message

    def _get_ai_recommendations(self,
                                validation_result: ValidationResult,
                                build_result: BuildResult,
                                platform: str) -> str:
        """Get AI-powered deployment recommendations"""
        if not self.gemini_client:
            return "AI recommendations not available (no Gemini client provided)"

        # Prepare context for AI
        context = f"""Analyze this deployment setup and provide recommendations:

Project Information:
- Python files: {validation_result.project_info.get('files', {}).get('python', 0)}
- Total lines: {validation_result.project_info.get('files', {}).get('total_lines', 0)}
- Target platform: {platform}
- Build artifacts: {len(build_result.artifacts)}

Validation Issues: {len(validation_result.issues)}
Validation Warnings: {len(validation_result.warnings)}

Warnings:
{chr(10).join('- ' + w for w in validation_result.warnings[:5])}

Please provide:
1. Platform suitability assessment (is {platform} a good choice for this app?)
2. Configuration recommendations
3. Performance optimization tips
4. Security considerations

Keep response concise (3-4 sentences)."""

        try:
            response = self.gemini_client.generate_content(context)
            if hasattr(self.gemini_client, 'extract_text'):
                return self.gemini_client.extract_text(response)
            return str(response)
        except Exception as e:
            return f"AI analysis failed: {str(e)}"

    def _build_response(self, status: str, **results) -> Dict:
        """Build pipeline response dictionary"""
        return {
            'status': status,
            'stages': [
                {
                    'name': stage.name,
                    'status': stage.status,
                    'message': stage.message
                }
                for stage in self.stages
            ],
            'results': results
        }

    def format_report(self, response: Dict) -> str:
        """
        Format pipeline response as human-readable report

        Args:
            response: Pipeline response dictionary

        Returns:
            Formatted string report
        """
        lines = []

        lines.append("╔" + "═" * 68 + "╗")
        lines.append("║" + " " * 20 + "DEPLOYMENT PIPELINE REPORT" + " " * 22 + "║")
        lines.append("╚" + "═" * 68 + "╝")
        lines.append("")

        # Overall Status
        status = response.get('status', 'unknown').upper()
        status_symbol = "✓" if status == 'SUCCESS' else "✗"
        lines.append(f"Overall Status: {status_symbol} {status}")
        lines.append("")

        # Pipeline Stages
        lines.append("Pipeline Stages:")
        lines.append("─" * 70)
        for stage in response.get('stages', []):
            status_map = {
                'success': '✓',
                'error': '✗',
                'running': '▶',
                'pending': '○'
            }
            symbol = status_map.get(stage['status'], '?')
            lines.append(f"  {symbol} {stage['name']}: {stage['message']}")
        lines.append("")

        # Results
        results = response.get('results', {})

        # Validation
        if 'validation_result' in results:
            val = results['validation_result']
            lines.append("Validation:")
            if val.issues:
                lines.append(f"  Issues: {len(val.issues)}")
            if val.warnings:
                lines.append(f"  Warnings: {len(val.warnings)}")
            lines.append("")

        # Build
        if 'build_result' in results:
            build = results['build_result']
            lines.append("Build:")
            lines.append(f"  Artifacts: {len(build.artifacts)}")
            lines.append("")

        # AI Recommendations
        if 'ai_recommendations' in results:
            lines.append("AI Recommendations:")
            lines.append("─" * 70)
            for line_text in results['ai_recommendations'].split('\n'):
                lines.append(f"  {line_text}")
            lines.append("")

        # Deployment
        if 'deployment_result' in results:
            deploy = results['deployment_result']
            lines.append("Deployment:")
            lines.append(f"  Platform: {deploy.platform}")
            if deploy.url:
                lines.append(f"  URL: {deploy.url}")
            lines.append("")

        lines.append("═" * 70)

        return '\n'.join(lines)
