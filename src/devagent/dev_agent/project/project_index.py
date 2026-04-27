def build_multi(self, roots: List[str]):
    """
    Indexa múltiplos projetos.
    """

    for root in roots:
        self._scan(root)
        
def _scan(self, root_path: str):
    for root, dirs, files in os.walk(root_path):

        for file in files:
            if not file.endswith(".py") and not file.endswith(".ts"):
                continue

            full_path = os.path.join(root, file)

            self.index[full_path] = {
                "file": file,
                "path": full_path,
                "imports": self._extract_imports(full_path),
                "source_root": root_path
            }        