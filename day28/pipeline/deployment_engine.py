"""
Deployment Engine
Stage 4 of deployment pipeline - handles actual deployment to platforms
"""

import os
import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class DeploymentResult:
    """Result of deployment"""
    success: bool
    platform: str
    url: Optional[str]
    logs: List[str]
    errors: List[str]


class DeploymentEngine:
    """Handles deployment to various platforms"""

    def __init__(self, project_root: str = '.'):
        """
        Initialize deployment engine

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)

    def deploy(self, platform: str = 'railway') -> DeploymentResult:
        """
        Deploy to specified platform (auto-detects redeploy)

        Args:
            platform: Target platform (railway, docker)

        Returns:
            DeploymentResult with deployment status and details
        """
        logs = []
        errors = []
        url = None
        success = False

        # Check if already deployed
        is_redeploying = self._check_existing_deployment(platform)
        action = "Redeploying" if is_redeploying else "Deploying"
        logs.append(f"{action} to {platform}...")

        try:
            if platform == 'railway':
                success, url, deploy_logs = self._deploy_railway()
            elif platform == 'docker':
                success, url, deploy_logs = self._deploy_docker()
            else:
                errors.append(f"Unknown platform: {platform}")
                success = False

            logs.extend(deploy_logs)

        except Exception as e:
            errors.append(f"Deployment failed: {str(e)}")
            logs.append(f"ERROR: {str(e)}")
            success = False

        return DeploymentResult(
            success=success,
            platform=platform,
            url=url,
            logs=logs,
            errors=errors
        )

    def _check_existing_deployment(self, platform: str) -> bool:
        """Check if there's an existing deployment"""
        deployment_markers = {
            'railway': ['.railway', 'railway.json'],
            'docker': ['Dockerfile', '.dockerignore']
        }

        markers = deployment_markers.get(platform, [])
        for marker in markers:
            marker_path = self.project_root / marker
            if marker_path.exists():
                return True
        return False

    def _deploy_railway(self) -> tuple:
        """Deploy to Railway"""
        logs = []

        # Check if Railway CLI is installed
        if not self._check_cli('railway'):
            logs.append("Railway CLI not found")
            logs.append("Install: npm i -g @railway/cli")
            return False, None, logs

        # Check authentication
        logs.append("Checking Railway authentication...")
        auth_result = self._run_command(['railway', 'whoami'])

        if auth_result['returncode'] != 0:
            logs.append("Not authenticated with Railway")
            logs.append("Run: railway login")
            return False, None, logs

        # Check if project is linked
        logs.append("Checking project link...")
        status_result = self._run_command(['railway', 'status'])

        if status_result['returncode'] != 0 or 'No service linked' in ''.join(status_result['output']):
            logs.append("No Railway project linked")
            logs.append("Attempting to link to existing project...")

            # Try to link
            link_result = self._run_command(['railway', 'link'])
            logs.extend(link_result['output'])

            if link_result['returncode'] != 0:
                logs.append("Failed to link project")
                logs.append("Please create a project in Railway Dashboard first:")
                logs.append("1. Go to railway.app/new")
                logs.append("2. Create 'Empty Service'")
                logs.append("3. Then run: railway link")
                return False, None, logs

        # Deploy
        logs.append("Deploying to Railway...")
        deploy_result = self._run_command(['railway', 'up'])
        logs.extend(deploy_result['output'])

        if deploy_result['returncode'] == 0:
            # Get deployment URL
            status_result = self._run_command(['railway', 'status'])
            url = self._extract_url(status_result['output'])
            return True, url, logs
        else:
            logs.append("Deployment failed - check logs above")
            return False, None, logs

    def _deploy_docker(self) -> tuple:
        """Deploy as Docker container"""
        logs = []

        # Check if Docker is installed
        if not self._check_cli('docker'):
            logs.append("Docker not found")
            logs.append("Install: https://docs.docker.com/get-docker/")
            return False, None, logs

        # Build Docker image
        logs.append("Building Docker image...")
        build_result = self._run_command([
            'docker', 'build',
            '-t', 'god-agent',
            str(self.project_root)
        ])
        logs.extend(build_result['output'])

        if build_result['returncode'] != 0:
            logs.append("Docker build failed")
            return False, None, logs

        # Check if container already exists
        check_result = self._run_command(['docker', 'ps', '-a', '-q', '-f', 'name=god-agent'])
        if check_result['output']:
            logs.append("Existing container found, removing...")
            self._run_command(['docker', 'rm', '-f', 'god-agent'])
            logs.append("Old container removed")

        # Run container
        logs.append("Starting Docker container...")
        run_result = self._run_command([
            'docker', 'run',
            '-d',
            '-p', '8080:8080',
            '-e', f"GEMINI_API_KEY={os.getenv('GEMINI_API_KEY', '')}",
            '-e', f"GROQ_API_KEY={os.getenv('GROQ_API_KEY', '')}",
            '-e', f"LLM_PROVIDER={os.getenv('LLM_PROVIDER', 'gemini')}",
            '--name', 'god-agent',
            'god-agent'
        ])
        logs.extend(run_result['output'])

        if run_result['returncode'] == 0:
            url = "http://localhost:8080"
            logs.append(f"Container running at {url}")
            return True, url, logs
        else:
            logs.append("Failed to start container")
            return False, None, logs

    def _check_cli(self, command: str) -> bool:
        """Check if a CLI tool is installed"""
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except Exception:
            return False

    def _run_command(self, command: List[str], timeout: int = 300) -> Dict:
        """Run a shell command and capture output"""
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.project_root)
            )

            output = []
            if result.stdout:
                output.extend(result.stdout.splitlines())
            if result.stderr:
                output.extend(result.stderr.splitlines())

            return {
                'returncode': result.returncode,
                'output': output
            }
        except subprocess.TimeoutExpired:
            return {
                'returncode': -1,
                'output': ['Command timed out']
            }
        except Exception as e:
            return {
                'returncode': -1,
                'output': [f'Command failed: {str(e)}']
            }

    def _extract_url(self, logs: List[str]) -> Optional[str]:
        """Extract deployment URL from logs"""
        for line in logs:
            if 'http' in line.lower() and 'railway' in line.lower():
                # Simple URL extraction
                parts = line.split()
                for part in parts:
                    if part.startswith('http'):
                        return part.rstrip('.,;')
        return None

    def format_result(self, result: DeploymentResult) -> str:
        """
        Format deployment result as human-readable text

        Args:
            result: DeploymentResult to format

        Returns:
            Formatted string
        """
        lines = []

        lines.append("=" * 70)
        lines.append("DEPLOYMENT REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Status
        status = "✓ SUCCESS" if result.success else "✗ FAILED"
        lines.append(f"Status: {status}")
        lines.append(f"Platform: {result.platform}")
        if result.url:
            lines.append(f"URL: {result.url}")
        lines.append("")

        # Deployment Logs
        if result.logs:
            lines.append("DEPLOYMENT LOGS:")
            lines.append("-" * 70)
            for log in result.logs:
                lines.append(f"  {log}")
            lines.append("")

        # Errors
        if result.errors:
            lines.append(f"ERRORS ({len(result.errors)}):")
            lines.append("-" * 70)
            for error in result.errors:
                lines.append(f"  ✗ {error}")
            lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)
