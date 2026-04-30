from devagent_core.storage.sqlite_storage import SQLiteStorage
from devagent_core.services.index_service_v2 import IndexServiceV2_1
from devagent_core.services.llm_service import LLMService
from devagent_core.services.rag_service import RAGService

from devagent_core.tools.analyze_tool import AnalyzeTool
from devagent_core.tools.edit_tool import EditTool
from devagent_core.tools.run_tool import RunTool
from devagent_core.tools.test_tool import TestTool
from devagent_core.tools.auto_fix_tool import AutoFixTool
from devagent_core.tools.auto_fix_v2 import AutoFixV2
from devagent_core.tools.code_tool import CodeTool

from devagent_core.core.brain_v3 import DevAgentBrainV3
from devagent_core.memory.mil_final import MIL

from devagent_core.repositories.strategy_memory_repository import StrategyMemoryRepository
from devagent_core.services.file_tag_service import FileTagService
from devagent_core.services.query_service import QueryService

import logging


class Bootstrap:
    def __init__(self):

        # INFRA
        self.storage = None
        self.llm = None

        # SERVICES
        self.query_service = None
        self.file_tag_service = None
        self.strategy_memory = None

        # INDEX / RAG
        self.index = None
        self.rag = None

        # TOOLS
        self.analyze_tool = None
        self.edit_tool = None
        self.run_tool = None
        self.test_tool = None
        self.auto_fix_tool = None
        self.auto_fix_v2 = None
        self.code_tool = None

        # INTELIGÊNCIA
        self.mil = None
        self.brain = None

    def start(self):
        try:
            logging.info("Inicializando DevAgent Core...")

            # =====================================================
            # INFRA
            # =====================================================
            self.storage = SQLiteStorage()
            self.llm = LLMService()

            # =====================================================
            # SERVICES (SINGLE SOURCE OF TRUTH)
            # =====================================================
            self.query_service = QueryService(self.storage)
            self.file_tag_service = FileTagService(self.storage)
            self.strategy_memory = StrategyMemoryRepository(self.storage)

            # =====================================================
            # INDEX
            # =====================================================
            self.index = IndexServiceV2_1(
                storage=self.storage,
                llm_service=self.llm,
                file_tag_service=self.file_tag_service
            )
            
            # =====================================================
            # RAG (corrigido: usa QueryService indiretamente via storage/index)
            # =====================================================
            self.rag = RAGService(
                index_service=self.index,
                llm_service=self.llm,
                storage=self.storage,
                query_service=self.query_service
            )

            # =====================================================
            # TOOLS
            # =====================================================
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

            self.code_tool = CodeTool(self.llm)

            # =====================================================
            # MIL
            # =====================================================
            self.mil = MIL(
                storage=self.storage,
                strategy_repository=self.strategy_memory,
                query_service=self.query_service,
                file_tag_service=self.file_tag_service,
            )

            self.memory_intelligence = self.mil

            # =====================================================
            # BRAIN
            # =====================================================
            self.brain = DevAgentBrainV3(
                bootstrap=self,
                mil=self.mil
            )

            # =====================================================
            # BOOTSTRAP INDEXAÇÃO (CRÍTICO PARA RAG)
            # =====================================================

            try:
                logging.info("Iniciando indexação do projeto...")

                PROJECT_ROOT = "."  # ou ajuste se tiver path fixo

                indexed = self.index.run(PROJECT_ROOT)

                logging.info(f"Indexação concluída: {indexed} arquivos processados")

            except Exception as e:
                logging.exception("Falha na indexação inicial do DevAgent")
                raise
            

            logging.info("🧠 DevAgent Core v3 iniciado com sucesso.")
            return self

        except Exception:
            logging.exception("Erro ao iniciar o DevAgent Core v3.")
            raise