"""
DevAgent v6 - Project Indexer

Responsável por mapear estrutura do projeto.
"""

from __future__ import annotations

import os
from typing import Dict, List


class ProjectIndex:
    def __init__(self, root_path: str):
        self.root_path = root_path
        self.index: Dict[str, Dict] = {}

    # --------------------------------------------------------
    # SCAN DO PROJETO
    # --------------------------------------------------------

    def build(self) -> Dict[str, Dict]:
        """
        Varre o projeto e cria índice base.
        """

        for root, dirs, files in os.walk(self.root_path):

            for file in files:

                if not file.endswith(".py"):
                    continue

                full_path = os.path.join(root, file)

                self.index[full_path] = {
                    "file": file,
                    "path": full_path,
                    "imports": self._extract_imports(full_path),
                }

        return self.index

    # --------------------------------------------------------
    # EXTRAÇÃO SIMPLES DE IMPORTS
    # --------------------------------------------------------

    def _extract_imports(self, file_path: str) -> List[str]:
        """
        Parser simples inicial (pode evoluir depois para AST).
        """

        imports = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:

                    line = line.strip()

                    if line.startswith("import ") or line.startswith("from "):
                        imports.append(line)

        except Exception:
            pass

        return imports

    # --------------------------------------------------------
    # CONSULTA
    # --------------------------------------------------------

    def find_file(self, name: str) -> List[str]:
        """
        Busca arquivos por nome.
        """

        return [
            path for path in self.index.keys()
            if name in path
        ]

    # --------------------------------------------------------
    # DEBUG
    # --------------------------------------------------------

    def summary(self) -> Dict[str, int]:
        return {
            "files": len(self.index)
        }