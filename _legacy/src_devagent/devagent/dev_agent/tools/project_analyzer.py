"""
dev_agent/tools/project_analyzer.py

Analisador automático de projetos.
"""

from __future__ import annotations

from pathlib import Path
from typing import List

from dev_agent.tools.base import Tool


class ProjectAnalyzerTool(Tool):
    """
    Detecta tecnologias e características de um projeto.
    """

    name = "analyze"
    description = "Analisa estrutura e stack de projetos"

    def execute(self, directory: str = ".") -> str:
        path = Path(directory).expanduser()

        if not path.exists():
            return f"Diretório não encontrado: {path}"

        if not path.is_dir():
            return f"Não é um diretório: {path}"

        findings: List[str] = []

        findings.append(f"Projeto: {path.resolve()}")
        findings.append("")

        # Linguagens
        languages = self._detect_languages(path)
        findings.append("Linguagens detectadas:")
        findings.extend(
            f"- {language}" for language in languages
        )
        findings.append("")

        # Frameworks
        frameworks = self._detect_frameworks(path)
        findings.append("Frameworks detectados:")

        if frameworks:
            findings.extend(
                f"- {framework}"
                for framework in frameworks
            )
        else:
            findings.append("- Nenhum identificado")

        findings.append("")

        # Gerenciadores
        managers = self._detect_package_managers(path)
        findings.append(
            "Gerenciadores de dependências:"
        )

        if managers:
            findings.extend(
                f"- {manager}"
                for manager in managers
            )
        else:
            findings.append("- Nenhum identificado")

        return "\n".join(findings)

    # ------------------------------------------------------------------
    # Detecção
    # ------------------------------------------------------------------

    def _detect_languages(
        self,
        path: Path,
    ) -> List[str]:
        detected = set()

        extensions = {
            ".py": "Python",
            ".js": "JavaScript",
            ".ts": "TypeScript",
            ".tsx": "React/TypeScript",
            ".jsx": "React/JavaScript",
            ".cs": "C#",
            ".java": "Java",
            ".go": "Go",
            ".rs": "Rust",
            ".sql": "SQL",
        }

        for file in path.rglob("*"):
            if file.is_file():
                language = extensions.get(
                    file.suffix.lower()
                )
                if language:
                    detected.add(language)

        return sorted(detected) or ["Desconhecida"]

    def _detect_frameworks(
        self,
        path: Path,
    ) -> List[str]:
        frameworks = []

        if (path / "manage.py").exists():
            frameworks.append("Django")

        if (path / "requirements.txt").exists():
            content = (
                path / "requirements.txt"
            ).read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            if "fastapi" in content:
                frameworks.append("FastAPI")

            if "flask" in content:
                frameworks.append("Flask")

        if (path / "package.json").exists():
            content = (
                path / "package.json"
            ).read_text(
                encoding="utf-8",
                errors="ignore",
            ).lower()

            if "next" in content:
                frameworks.append("Next.js")

            if "react" in content:
                frameworks.append("React")

            if "vue" in content:
                frameworks.append("Vue")

            if "angular" in content:
                frameworks.append("Angular")

        return frameworks

    def _detect_package_managers(
        self,
        path: Path,
    ) -> List[str]:
        managers = []

        files = {
            "requirements.txt": "pip",
            "pyproject.toml": "Poetry/UV",
            "package.json": "npm",
            "yarn.lock": "Yarn",
            "pnpm-lock.yaml": "pnpm",
            "pom.xml": "Maven",
            "build.gradle": "Gradle",
            "*.csproj": ".NET",
            "Cargo.toml": "Cargo",
            "go.mod": "Go Modules",
        }

        for pattern, manager in files.items():
            if "*" in pattern:
                if list(path.glob(pattern)):
                    managers.append(manager)
            else:
                if (path / pattern).exists():
                    managers.append(manager)

        return managers