from devagent_core.storage.sqlite_storage import SQLiteStorage
from devagent_core.services.memory_service import MemoryService
from devagent_core.services.index_service_v2 import IndexServiceV2_1
from devagent_core.services.llm_service import LLMService
from devagent_core.services.rag_service import RAGService

from devagent_core.tools.analyze_tool import AnalyzeTool
from devagent_core.tools.edit_tool import EditTool
from devagent_core.tools.run_tool import RunTool
from devagent_core.tools.test_tool import TestTool
from devagent_core.tools.auto_fix_tool import AutoFixTool
from devagent_core.tools.auto_fix_v2 import AutoFixV2

from devagent_core.core.brain_v3 import DevAgentBrainV3

from devagent_core.memory.mil_final import MIL  
from devagent_core.repositories.file_tag_repository import FileTagRepository

import logging


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

        self.file_tags = None
        self.mil = None
        self.brain = None

    def start(self):
        try:
            # =========================
            # INFRA
            # =========================
            self.storage = SQLiteStorage()
            self.memory = MemoryService(self.storage)
            self.llm = LLMService()

            # =========================
            # TAG SYSTEM (ANTES DO INDEX)
            # =========================
            self.file_tags = FileTagRepository(self.storage)

            # =========================
            # INDEX + RAG
            # =========================
            self.index = IndexServiceV2_1(
                self.storage,
                self.llm,
                self.file_tags
            )

            self.rag = RAGService(
                self.index,
                self.llm,
                self.storage,
            )

            # =========================
            # TOOLS
            # =========================
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

            # =========================
            # MIL (MEMÓRIA INTELIGENTE)
            # =========================
            self.mil = MIL(
                self.storage,
                self.file_tags
            )

            # =========================
            # BRAIN (DEPENDE DE TUDO)
            # =========================
            self.brain = DevAgentBrainV3(self)

            logging.info("\n🧠 DEVAGENT CORE v3 iniciado\n")

        except Exception as e:
            logging.error(f"Erro ao iniciar o DEVAGENT CORE v3: {e}")