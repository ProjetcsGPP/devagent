from devagent_core.storage.sqlite_storage import SQLiteStorage
from devagent_core.services.memory_service import MemoryService
from devagent_core.services.index_service import IndexService
from devagent_core.services.llm_service import LLMService
from devagent_core.services.rag_service import RAGService
from devagent_core.tools.analyze_tool import AnalyzeTool
from devagent_core.tools.edit_tool import EditTool
from devagent_core.tools.run_tool import RunTool
from devagent_core.tools.test_tool import TestTool
from devagent_core.tools.auto_fix_tool import AutoFixTool
from devagent_core.tools.auto_fix_v2 import AutoFixV2
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Bootstrap:
    def __init__(self):
        self.storage = None
        self.memory = None
        self.index = None
        self.llm = None
        self.rag = None
        self.analyze_tool = None
        self.edit_tool = None
        self.run_tool = None
        self.test_tool = None
        self.auto_fix_tool = None
        self.auto_fix_v2 = None

    def start(self):
        try:
            self.storage = SQLiteStorage()
            self.memory = MemoryService(self.storage)
            self.index = IndexService(self.storage)
            self.llm = LLMService()
            self.rag = RAGService(
                self.index,
                self.llm,
                self.storage,
            )

            self.analyze_tool = AnalyzeTool(self.rag)
            self.edit_tool = EditTool(self.llm)
            self.run_tool = RunTool()
            self.test_tool = TestTool()
            self.auto_fix_tool = AutoFixTool(self.llm)
            self.auto_fix_v2 = AutoFixV2(
                                    llm_service=self.llm,
                                    edit_tool=self.edit_tool,
                                    test_tool=self.test_tool
                                )

            logging.info("\n🧠 DEVAGENT CORE v2 iniciado\n")
            logging.info("Memory: active")
            logging.info(f"Index count: {self.index.count()}")
            logging.info("RAG: active")
            logging.info("Edit Tool: active")
            logging.info("Run Tool: active")
            logging.info("Test Tool: active")
            logging.info("Auto Fix Tool: active")
            logging.info("Auto Fix v2 Tool: active")
        except Exception as e:
            logging.error(f"Erro ao iniciar o DEVAGENT CORE v2: {e}")