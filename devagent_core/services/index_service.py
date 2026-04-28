from pathlib import Path


class IndexService:
    SUPPORTED_EXTENSIONS = {
        ".py",
        ".js",
        ".ts",
        ".tsx",
        ".jsx",
        ".json",
        ".md",
        ".yaml",
        ".yml",
        ".toml",
        ".sql",
    }

    def __init__(self, storage):
        self.storage = storage

    def index_file(self, filepath: str):
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(filepath)

        if not path.is_file():
            raise ValueError(filepath)

        if path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            return False

        content = path.read_text(
            encoding="utf-8",
            errors="ignore"
        )

        self.storage.execute(
            """
            INSERT OR REPLACE INTO files_index
            (path, content)
            VALUES (?, ?)
            """,
            (str(path), content),
        )

        return True

    def index_directory(self, directory: str):
        root = Path(directory)

        if not root.exists():
            raise FileNotFoundError(directory)

        EXCLUDED_DIRS = {
            ".git",
            "__pycache__",
            "venv",
            ".venv",
            "node_modules",
            ".mypy_cache",
            ".pytest_cache",
            "dist",
            "build",
            ".idea",
            ".vscode",
            "_archive",
        }

        indexed = 0

        for file in root.rglob("*"):
            if not file.is_file():
                continue

            if any(part in EXCLUDED_DIRS for part in file.parts):
                continue

            try:
                if self.index_file(str(file)):
                    indexed += 1
            except Exception:
                continue

        return indexed
        
    def search(self, query: str, limit: int = 10):
        STOPWORDS = {
            "como",
            "funciona",
            "classe",
            "method",
            "método",
            "function",
            "função",
            "arquivo",
            "sobre",
            "para",
            "com",
            "uma",
            "das",
            "dos",
            "que",
            "the",
            "and",
            "what",
            "where",
            "when",
        }

        keywords = [
            word.strip(".,!?()[]{}\"'").lower()
            for word in query.split()
            if len(word.strip()) >= 3
        ]

        keywords = [
            word
            for word in keywords
            if word not in STOPWORDS
        ]

        if not keywords:
            keywords = [
                query.strip().lower()
            ]

        conditions = []
        params = []

        for word in keywords:
            conditions.append("LOWER(path) LIKE ?")
            conditions.append("LOWER(content) LIKE ?")

            like = f"%{word}%"
            params.extend([like, like])

        where_clause = " OR ".join(conditions)

        sql = f"""
            SELECT path
            FROM files_index
            WHERE {where_clause}
            ORDER BY
                CASE
                    WHEN LOWER(path) LIKE ? THEN 0
                    ELSE 1
                END,
                path
            LIMIT ?
        """

        params.append(f"%{keywords[0]}%")
        params.append(limit)

        return self.storage.fetchall(
            sql,
            tuple(params)
        )

    def count(self):
        row = self.storage.fetchone(
            "SELECT COUNT(*) FROM files_index"
        )
        return row[0] if row else 0