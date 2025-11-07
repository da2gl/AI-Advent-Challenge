"""
Build Preparer
Stage 2 of deployment pipeline - prepares project for deployment
"""

from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class BuildResult:
    """Result of build preparation"""
    success: bool
    artifacts: List[str]
    errors: List[str]
    build_info: Dict


class BuildPreparer:
    """Prepares project for deployment by generating necessary files"""

    def __init__(self, project_root: str = '.'):
        """
        Initialize build preparer

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self.build_dir = self.project_root / 'build'

    def prepare(self, platform: str = 'railway') -> BuildResult:
        """
        Prepare project for deployment

        Args:
            platform: Target deployment platform (railway, docker)

        Returns:
            BuildResult with preparation status and artifacts
        """
        errors = []
        artifacts = []
        build_info = {
            'platform': platform,
            'timestamp': self._get_timestamp()
        }

        try:
            # Create build directory
            self.build_dir.mkdir(exist_ok=True)
            artifacts.append(str(self.build_dir))

            # Generate platform-specific files
            if platform == 'railway':
                railway_artifacts = self._prepare_railway()
                artifacts.extend(railway_artifacts)
            elif platform == 'docker':
                docker_artifacts = self._prepare_docker()
                artifacts.extend(docker_artifacts)
            else:
                errors.append(f"Unknown platform: {platform}")

            # Generate Procfile
            procfile = self._generate_procfile()
            if procfile:
                artifacts.append(procfile)

            # Generate .env.example
            env_example = self._generate_env_example()
            if env_example:
                artifacts.append(env_example)

            # Verify requirements.txt
            if not self._verify_requirements():
                errors.append("requirements.txt verification failed")

            success = len(errors) == 0

        except Exception as e:
            errors.append(f"Build preparation failed: {str(e)}")
            success = False

        return BuildResult(
            success=success,
            artifacts=artifacts,
            errors=errors,
            build_info=build_info
        )

    def _prepare_railway(self) -> List[str]:
        """Prepare Railway-specific files"""
        artifacts = []

        # Generate railway.json
        railway_config = {
            "$schema": "https://railway.app/railway.schema.json",
            "build": {
                "builder": "NIXPACKS"
            },
            "deploy": {
                "startCommand": "uvicorn webapp.app:app --host 0.0.0.0 --port $PORT",
                "restartPolicyType": "ON_FAILURE",
                "restartPolicyMaxRetries": 10
            }
        }

        railway_file = self.project_root / 'railway.json'
        try:
            import json
            with open(railway_file, 'w') as f:
                json.dump(railway_config, f, indent=2)
            artifacts.append(str(railway_file))
        except Exception as e:
            print(f"Warning: Could not create railway.json: {e}")

        return artifacts

    def _prepare_docker(self) -> List[str]:
        """Prepare Docker-specific files"""
        artifacts = []

        # Dockerfile already exists, just verify it
        dockerfile = self.project_root / 'Dockerfile'
        if dockerfile.exists():
            artifacts.append(str(dockerfile))

        # Generate .dockerignore
        dockerignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Build
build/
dist/
*.egg-info/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Data
data/
*.db
*.sqlite

# Logs
*.log

# Git
.git/
.gitignore
"""

        dockerignore_file = self.project_root / '.dockerignore'
        try:
            with open(dockerignore_file, 'w') as f:
                f.write(dockerignore_content)
            artifacts.append(str(dockerignore_file))
        except Exception as e:
            print(f"Warning: Could not create .dockerignore: {e}")

        return artifacts

    def _generate_procfile(self) -> Optional[str]:
        """Generate Procfile for deployment"""
        procfile_content = "web: uvicorn webapp.app:app --host 0.0.0.0 --port $PORT\n"

        procfile = self.project_root / 'Procfile'
        try:
            with open(procfile, 'w') as f:
                f.write(procfile_content)
            return str(procfile)
        except Exception as e:
            print(f"Warning: Could not create Procfile: {e}")
            return None

    def _generate_env_example(self) -> Optional[str]:
        """Generate .env.example file"""
        env_example_content = """# Environment Variables Example
# Copy this file to .env and fill in your values

# Gemini API Key (required)
GEMINI_API_KEY=your_api_key_here

# Groq API Key (optional, for voice input)
GROQ_API_KEY=your_groq_api_key_here

# LLM Provider (gemini or ollama)
LLM_PROVIDER=gemini

# Port (optional, defaults to 8080)
PORT=8080
"""

        env_example = self.project_root / '.env.example'
        try:
            with open(env_example, 'w') as f:
                f.write(env_example_content)
            return str(env_example)
        except Exception as e:
            print(f"Warning: Could not create .env.example: {e}")
            return None

    def _verify_requirements(self) -> bool:
        """Verify requirements.txt includes deployment dependencies"""
        req_file = self.project_root / 'requirements.txt'

        if not req_file.exists():
            return False

        try:
            with open(req_file, 'r') as f:
                content = f.read().lower()

            # Check for uvicorn (needed for FastAPI production)
            if 'uvicorn' not in content:
                print("Warning: uvicorn not found in requirements.txt")
                return False

            # Check for fastapi
            if 'fastapi' not in content:
                print("Warning: fastapi not found in requirements.txt")
                return False

            return True

        except Exception as e:
            print(f"Error verifying requirements: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'

    def format_result(self, result: BuildResult) -> str:
        """
        Format build result as human-readable text

        Args:
            result: BuildResult to format

        Returns:
            Formatted string
        """
        lines = []

        lines.append("=" * 70)
        lines.append("BUILD PREPARATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Status
        status = "✓ SUCCESS" if result.success else "✗ FAILED"
        lines.append(f"Status: {status}")
        lines.append("")

        # Build Info
        lines.append("BUILD INFO:")
        lines.append("-" * 70)
        lines.append(f"  Platform: {result.build_info.get('platform', 'N/A')}")
        lines.append(f"  Timestamp: {result.build_info.get('timestamp', 'N/A')}")
        lines.append("")

        # Artifacts
        if result.artifacts:
            lines.append(f"ARTIFACTS GENERATED ({len(result.artifacts)}):")
            lines.append("-" * 70)
            for artifact in result.artifacts:
                lines.append(f"  ✓ {artifact}")
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
