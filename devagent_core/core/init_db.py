# devagent_core/core/init_db.py

def init_db(cursor):
    """
    Schema centralizado do DevAgent.
    NÃO contém lógica, apenas criação de tabelas.
    """

    # =========================================================
    # FILES INDEX
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            content TEXT
        )
    """)

    # =========================================================
    # MEMORY STORE (KV + EVENT RAW)
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT,
            type TEXT,
            timestamp REAL,
            data TEXT
        )
    """)

    # =========================================================
    # MEMORY EVENTS (FUTURO ANALYTICS)
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT,
            intent TEXT,
            strategy TEXT,
            plan TEXT,
            success INTEGER,
            error_type TEXT,
            timestamp REAL
        )
    """)

    # =========================================================
    # FILE TAGS
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            tag TEXT NOT NULL,
            tag_type TEXT DEFAULT 'generic',
            weight REAL DEFAULT 1.0,
            confidence REAL DEFAULT 0.5,
            source TEXT DEFAULT 'indexer',
            created_at TEXT,
            updated_at TEXT,
            UNIQUE(file_path, tag)
        )
    """)

    # =========================================================
    # ENTITY TAGS
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS entity_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT NOT NULL,
            tag TEXT NOT NULL,
            weight REAL DEFAULT 1.0
        )
    """)

    # =========================================================
    # STRATEGY MEMORY
    # =========================================================
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS strategy_memory (
            strategy_name TEXT PRIMARY KEY,
            score REAL DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            failure_count INTEGER DEFAULT 0,
            last_used REAL,
            updated_at REAL
        )
    """)