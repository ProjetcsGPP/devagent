from __future__ import annotations


class IndexAPI:
    """
    Camada de abstração do ProjectIndex.

    Impede que CORE/MEMORY dependam de `.index` diretamente.
    """

    def __init__(self, project_index):
        self._project_index = project_index

    @property
    def index(self):
        return self._project_index.index

    def count_files(self) -> int:
        return len(self._project_index.index)

    def list_files(self):
        return list(self._project_index.index.keys())

    def get_raw(self):
        return self._project_index.index