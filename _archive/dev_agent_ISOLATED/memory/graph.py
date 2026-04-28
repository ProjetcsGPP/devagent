"""
DevAgent v6 - Dependency Graph Layer

Constrói e mantém um grafo de dependências entre módulos Python.

Base para:
- análise de impacto
- navegação de código
- contexto inteligente no LLM
"""

from __future__ import annotations

from typing import Dict, List, Set
import re


class DependencyGraph:
    def __init__(self, project_index):
        """
        project_index: ProjectIndex
        """
        self.project_index = project_index

        # grafo:
        # { file: set(imported_files) }
        self.graph: Dict[str, Set[str]] = {}

    # --------------------------------------------------------
    # BUILD GRAPH
    # --------------------------------------------------------

    def build(self) -> Dict[str, Set[str]]:
        """
        Constrói grafo de dependências.
        """

        self.graph = {}

        index = self.project_index.get_index()

        for file_path, data in index.items():

            imports = data.get("imports", [])

            resolved = self._resolve_imports(imports, index)

            self.graph[file_path] = set(resolved)

        return self.graph

    # --------------------------------------------------------
    # RESOLVE IMPORTS → FILE PATHS
    # --------------------------------------------------------

    def _resolve_imports(self, imports: List[str], index: Dict[str, Dict]) -> List[str]:
        """
        Tenta mapear imports para arquivos reais do projeto.
        Versão inicial heurística.
        """

        resolved = []

        all_files = list(index.keys())

        for imp in imports:

            # tenta extrair nome do módulo
            module = self._extract_module_name(imp)

            if not module:
                continue

            for file_path in all_files:

                if module in file_path:
                    resolved.append(file_path)

        return resolved

    # --------------------------------------------------------
    # EXTRATOR SIMPLES DE MÓDULO
    # --------------------------------------------------------

    def _extract_module_name(self, import_line: str) -> str:
        """
        Extrai nome básico do import.
        """

        # from x import y
        match = re.match(r"from\s+([a-zA-Z0-9_\.]+)", import_line)
        if match:
            return match.group(1).split(".")[-1]

        # import x
        match = re.match(r"import\s+([a-zA-Z0-9_\.]+)", import_line)
        if match:
            return match.group(1).split(".")[0]

        return ""

    # --------------------------------------------------------
    # ANALYSIS API
    # --------------------------------------------------------

    def dependencies_of(self, file_path: str) -> List[str]:
        return list(self.graph.get(file_path, []))

    def dependents_of(self, file_path: str) -> List[str]:
        """
        Quem depende deste arquivo.
        """
        result = []

        for file, deps in self.graph.items():
            if file_path in deps:
                result.append(file)

        return result

    # --------------------------------------------------------
    # IMPACT ANALYSIS
    # --------------------------------------------------------

    def impact_analysis(self, file_path: str, depth: int = 3) -> Set[str]:
        """
        Retorna todos os arquivos afetados por mudança.
        """

        visited = set()
        queue = [(file_path, 0)]

        while queue:
            current, level = queue.pop(0)

            if level > depth:
                continue

            for dependent in self.dependents_of(current):

                if dependent not in visited:
                    visited.add(dependent)
                    queue.append((dependent, level + 1))

        return visited

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    def summary(self) -> Dict[str, int]:
        return {
            "nodes": len(self.graph),
            "edges": sum(len(v) for v in self.graph.values())
        }