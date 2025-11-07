"""
Project Validator
Stage 1 of deployment pipeline - validates project structure and requirements
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ValidationResult:
    """Result of project validation"""
    valid: bool
    issues: List[str]
    warnings: List[str]
    project_info: Dict


class ProjectValidator:
    """Validates project structure and dependencies before deployment"""

    REQUIRED_FILES = [
        'webapp/app.py',
        'requirements.txt',
        'core/gemini_client.py'
    ]

    REQUIRED_DIRS = [
        'webapp',
        'core',
        'pipeline'
    ]

    def __init__(self, project_root: str = '.'):
        """
        Initialize validator

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)

    def validate(self) -> ValidationResult:
        """
        Validate the project

        Returns:
            ValidationResult with validation status and details
        """
        issues = []
        warnings = []
        project_info = {}

        # Check if project root exists
        if not self.project_root.exists():
            issues.append(f"Project root not found: {self.project_root}")
            return ValidationResult(
                valid=False,
                issues=issues,
                warnings=warnings,
                project_info=project_info
            )

        # Validate directory structure
        dir_issues = self._validate_directories()
        issues.extend(dir_issues)

        # Validate required files
        file_issues = self._validate_files()
        issues.extend(file_issues)

        # Check requirements.txt
        req_warnings = self._check_requirements()
        warnings.extend(req_warnings)

        # Check environment variables
        env_warnings = self._check_environment()
        warnings.extend(env_warnings)

        # Gather project info
        project_info = self._gather_project_info()

        # Determine if valid
        valid = len(issues) == 0

        return ValidationResult(
            valid=valid,
            issues=issues,
            warnings=warnings,
            project_info=project_info
        )

    def _validate_directories(self) -> List[str]:
        """Validate required directories exist"""
        issues = []

        for dir_name in self.REQUIRED_DIRS:
            dir_path = self.project_root / dir_name
            if not dir_path.exists():
                issues.append(f"Required directory missing: {dir_name}")
            elif not dir_path.is_dir():
                issues.append(f"Path is not a directory: {dir_name}")

        return issues

    def _validate_files(self) -> List[str]:
        """Validate required files exist"""
        issues = []

        for file_name in self.REQUIRED_FILES:
            file_path = self.project_root / file_name
            if not file_path.exists():
                issues.append(f"Required file missing: {file_name}")
            elif not file_path.is_file():
                issues.append(f"Path is not a file: {file_name}")

        return issues

    def _check_requirements(self) -> List[str]:
        """Check requirements.txt for potential issues"""
        warnings = []

        req_file = self.project_root / 'requirements.txt'
        if req_file.exists():
            try:
                with open(req_file, 'r') as f:
                    requirements = f.read().splitlines()

                # Check for essential packages
                essential_packages = ['flask', 'requests', 'rich']
                missing_packages = []

                for package in essential_packages:
                    if not any(package.lower() in req.lower() for req in requirements):
                        missing_packages.append(package)

                if missing_packages:
                    warnings.append(
                        f"Potentially missing packages: {', '.join(missing_packages)}"
                    )

                # Check for version pinning
                unpinned = [req for req in requirements if '==' not in req and req.strip() and not req.startswith('#')]
                if unpinned:
                    warnings.append(
                        f"{len(unpinned)} packages without pinned versions (recommended for deployment)"
                    )

            except Exception as e:
                warnings.append(f"Could not parse requirements.txt: {str(e)}")

        return warnings

    def _check_environment(self) -> List[str]:
        """Check for required environment variables"""
        warnings = []

        # Check for API key
        if not os.getenv('GEMINI_API_KEY'):
            warnings.append(
                "GEMINI_API_KEY not set - application will not function without it"
            )

        # Check for PORT (useful for deployment platforms)
        if not os.getenv('PORT'):
            warnings.append(
                "PORT environment variable not set - will use default 8080"
            )

        return warnings

    def _gather_project_info(self) -> Dict:
        """Gather information about the project"""
        info = {
            'root': str(self.project_root.absolute()),
            'files': {},
            'directories': {},
            'python_version': None
        }

        # Count Python files
        py_files = list(self.project_root.rglob('*.py'))
        info['files']['python'] = len(py_files)
        info['files']['total_lines'] = self._count_lines(py_files)

        # Count directories
        dirs = [d for d in self.project_root.rglob('*') if d.is_dir()]
        info['directories']['total'] = len(dirs)

        # Get Python version from runtime.txt if exists
        runtime_file = self.project_root / 'runtime.txt'
        if runtime_file.exists():
            try:
                with open(runtime_file, 'r') as f:
                    info['python_version'] = f.read().strip()
            except Exception:
                pass

        return info

    def _count_lines(self, files: List[Path]) -> int:
        """Count total lines in Python files"""
        total = 0
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    total += len(f.readlines())
            except Exception:
                pass
        return total

    def format_result(self, result: ValidationResult) -> str:
        """
        Format validation result as human-readable text

        Args:
            result: ValidationResult to format

        Returns:
            Formatted string
        """
        lines = []

        lines.append("=" * 70)
        lines.append("PROJECT VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append("")

        # Status
        status = "✓ VALID" if result.valid else "✗ INVALID"
        lines.append(f"Status: {status}")
        lines.append("")

        # Issues
        if result.issues:
            lines.append(f"ISSUES ({len(result.issues)}):")
            lines.append("-" * 70)
            for issue in result.issues:
                lines.append(f"  ✗ {issue}")
            lines.append("")

        # Warnings
        if result.warnings:
            lines.append(f"WARNINGS ({len(result.warnings)}):")
            lines.append("-" * 70)
            for warning in result.warnings:
                lines.append(f"  ⚠ {warning}")
            lines.append("")

        # Project Info
        if result.project_info:
            lines.append("PROJECT INFO:")
            lines.append("-" * 70)
            lines.append(f"  Root: {result.project_info.get('root', 'N/A')}")
            if 'files' in result.project_info:
                lines.append(f"  Python files: {result.project_info['files'].get('python', 0)}")
                lines.append(f"  Total lines: {result.project_info['files'].get('total_lines', 0)}")
            if 'directories' in result.project_info:
                lines.append(f"  Directories: {result.project_info['directories'].get('total', 0)}")
            if result.project_info.get('python_version'):
                lines.append(f"  Python version: {result.project_info['python_version']}")
            lines.append("")

        lines.append("=" * 70)

        return '\n'.join(lines)
