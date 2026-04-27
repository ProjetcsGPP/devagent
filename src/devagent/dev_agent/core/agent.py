"""
dev_agent/core/agent.py

Núcleo principal do DevAgent.
"""

from __future__ import annotations

from typing import Optional

from devagent.core.llm import OllamaClient
from dev_agent.core.prompts import (
    SYSTEM_PROMPT,
    RAG_PROMPT_TEMPLATE,
    TOOL_ROUTER_PROMPT,
    CHAT_PROMPT_TEMPLATE,
)

from dev_agent.core.session import SessionManager
from dev_agent.rag.retriever import RAGRetriever
from dev_agent.tools.registry import ToolRegistry
from dev_agent.core.router import Router
from dev_agent.tools.validator import ToolValidator
from dev_agent.tools import TOOLS

import json
from pathlib import Path

from dev_agent.memory.memory_store import MemoryStore
from dev_agent.core.context_builder import ContextBuilder
from dev_agent.core.context_router import ContextRouter

from dev_agent.sources.project_sources import ProjectSources


class DevAgent:
    """
    Agente principal.
    """

    def __init__(self) -> None:
        self.llm = OllamaClient()
        self.session = SessionManager()
        
        self.session_file = Path("storage/session.json")
        self.session.load(self.session_file)
        
        self.memory = MemoryStore()
        self.rag = RAGRetriever()
        self.tools = ToolRegistry()

        self.project_sources = ProjectSources()
                        
        self._register_tools()
        
        self.router = Router(
            registry=self.tools,
            validator=ToolValidator()
        )

        self.context_builder = ContextBuilder(
            session=self.session,
            rag=self.rag,
            memory=self.memory,
            project_index=getattr(self, "project_index", None),
        )
        
        self.context_router = ContextRouter(max_tokens=2500)

        self.project_index.build_multi([
            "external_projects/backend",
            "external_projects/frontend",
        ])

        # Prompt de sistema
        if self.session.is_empty():
            self.session.add_system_message(SYSTEM_PROMPT)

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------


    def _register_tools(self) -> None:
        """
        Registra todas as ferramentas disponíveis.
        """
        for tool in TOOLS:
            self.tools.register(tool)


    # ------------------------------------------------------------------
    # Processamento principal
    # ------------------------------------------------------------------

    def process(self, user_input: str) -> str:
        user_input = user_input.strip()

        if not user_input:
            return "Digite uma solicitação válida."

        session_cmd = self._handle_session_commands(user_input)
        if session_cmd is not None:
            return session_cmd

        # Comandos internos
        command_response = self._handle_builtin_commands(user_input)
        if command_response is not None:
            if not user_input.startswith("/history") and user_input.lower() not in {
                "history", "hist", "/hist"
            }:
                self.session.add_user_message(user_input)
                self.session.add_assistant_message(command_response)

            return command_response

        # Ferramentas explícitas
        tool_response = self._handle_tool_execution(user_input)
        if tool_response is not None:
            self.session.add_user_message(user_input)
            self.session.add_assistant_message(tool_response)
            return tool_response

        # Ferramentas autônomas
        autonomous_response = self._try_autonomous_tool(
            user_input
        )
        if autonomous_response is not None:
            self.session.add_user_message(user_input)
            self.session.add_assistant_message(autonomous_response)
            return autonomous_response

        # Histórico
        self.session.add_user_message(user_input)

        # Context Layer (único ponto de verdade)
        response = self._process_with_context(user_input)

        self.session.add_assistant_message(response)
        return response

    # ------------------------------------------------------------------
    # Ferramentas
    # ------------------------------------------------------------------

    def _try_autonomous_tool(
        self,
        user_input: str,
    ) -> Optional[str]:
        """
        Permite ao LLM decidir automaticamente
        quando usar uma ferramenta.
        """

        prompt = (
            f"{TOOL_ROUTER_PROMPT}\n\n"
            f"Solicitação do usuário:\n"
            f"{user_input}"
        )

        try:
            response = self.llm.generate(
                prompt=prompt,
                system="Você responde apenas JSON."
            )

            decision = json.loads(response)

            if not decision.get("tool"):
                return None

            result = self.router.execute(
                json.dumps(decision)
            )

            return json.dumps(
                result,
                indent=2,
                ensure_ascii=False,
            )

        except Exception:
            return None


    def _handle_tool_execution(
        self,
        user_input: str,
    ) -> Optional[str]:
        """
        Executa ferramentas via prefixo @ ou !.
        """

        # Shell
        if user_input.startswith("!"):
            command = user_input[1:].strip()

            if not command:
                return "Uso: ! <comando>"

            return self.tools.execute(
                "shell",
                command,
            )

        # Ferramentas genéricas
        if user_input.startswith("@"):
            content = user_input[1:].strip()

            if not content:
                return "Uso: @<ferramenta> [argumentos]"

            parts = content.split(maxsplit=1)
            tool_name = parts[0]
            arguments = parts[1] if len(parts) > 1 else ""

            # Compatibilidade com filesystem
            if tool_name == "fs":
                tool_name = "filesystem"

                fs_parts = arguments.split(
                    maxsplit=2
                )

                if not fs_parts:
                    return (
                        "Uso:\n"
                        "@fs list [diretório]\n"
                        "@fs read <arquivo>\n"
                        "@fs write <arquivo> <conteúdo>"
                    )

                action = fs_parts[0]
                args = fs_parts[1:]

                payload = {
                    "tool": tool_name,
                    "args": {
                        "action": action
                    }
                }

                if len(args) >= 1:
                    payload["args"]["path"] = args[0]

                if len(args) >= 2:
                    payload["args"]["content"] = args[1]

                result = self.router.execute(
                    json.dumps(payload)
                )

                return json.dumps(
                    result,
                    indent=2,
                    ensure_ascii=False
                )

            # ----------------------------
            # Ferramenta: edit (CASO ESPECIAL)
            # ----------------------------
            if tool_name == "edit":
                edit_parts = arguments.split(maxsplit=1)

                if len(edit_parts) < 2:
                    return (
                        "Uso:\n"
                        "@edit append <arquivo> <texto>\n"
                        "@edit prepend <arquivo> <texto>\n"
                        "@edit replace <arquivo> <buscar> <substituir>"
                    )

                action = edit_parts[0]
                rest = edit_parts[1]

                if action in {"append", "prepend"}:
                    sub = rest.split(maxsplit=1)

                    if len(sub) < 2:
                        return "Uso incorreto para append/prepend."

                    return self.tools.execute(
                        "edit",
                        action,
                        sub[0],
                        sub[1],
                    )

                if action == "replace":
                    sub = rest.split(maxsplit=2)

                    if len(sub) < 3:
                        return "Uso: @edit replace <arquivo> <buscar> <substituir>"

                    return self.tools.execute(
                        "edit",
                        action,
                        sub[0],
                        sub[1],
                        sub[2],
                    )

            if tool_name == "memory":
                mem_parts = arguments.split(maxsplit=1)

                if not mem_parts:
                    return (
                        "Uso:\n"
                        "@memory save <texto> | #tags\n"
                        "@memory search <tag ou texto>\n"
                        "@memory tags"
                    )

                action = mem_parts[0]
                rest = mem_parts[1] if len(mem_parts) > 1 else ""

                # --------------------------
                # SAVE
                # --------------------------
                if action == "save":
                    if "|" in rest:
                        content, tags_raw = rest.split("|", 1)
                        tags = [t.strip().replace("#", "") for t in tags_raw.split()]
                    else:
                        content = rest
                        tags = ["general"]

                    result = self.memory.save(
                        content=content.strip(),
                        tags=tags,
                        source="manual"
                    )

                    return f"Memória salva: {result['id']}"

                # --------------------------
                # SEARCH
                # --------------------------
                if action == "search":
                    results = self.memory.search_text(rest)

                    if not results:
                        return "Nenhuma memória encontrada."

                    return json.dumps(results, indent=2, ensure_ascii=False)

                # --------------------------
                # TAGS
                # --------------------------
                if action == "tags":
                    return json.dumps(self.memory.list_tags(), indent=2)

                return "Ação inválida em @memory"


            return self.tools.execute(tool_name)

        return None
    
        
    def _handle_session_commands(self, user_input: str):
        cmd = user_input.strip().lower()

        if cmd == "/save":
            self.save_session()
            return "Sessão salva manualmente."

        if cmd == "/load":
            self.session.load(self.session_file)
            return "Sessão recarregada do disco."

        if cmd == "/clear":
            self.session.clear()
            self.session.add_system_message(SYSTEM_PROMPT)
            return "Sessão limpa."

        return None    
    
    def save_session(self) -> None:
        """
        Persiste a sessão em disco.
        """
        self.session.save(self.session_file)
        
    # ------------------------------------------------------------------
    # Processamento normal
    # ------------------------------------------------------------------

    def _get_last_user_message(self) -> Optional[str]:
        messages = self.session.get_messages()

        for msg in reversed(messages):
            if msg["role"] == "user":
                return msg["content"]

        return None

    def _process_standard(self) -> str:
        """
        Processamento padrão usando histórico formatado.
        """

        history = self.session.format_for_prompt()

        question = self._get_last_user_message()

        if not question:
            return "Nenhuma mensagem do usuário encontrada."

        prompt = CHAT_PROMPT_TEMPLATE.format(
            history=history,
            question=question,
        )

        return self.llm.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
        )


    # ------------------------------------------------------------------
    # Context Builder
    # ------------------------------------------------------------------
    def _process_with_context(self, user_input: str) -> str:
        context_packet = self.context_builder.build(user_input)

        context_text = self.context_router.build(context_packet)

        prompt = CHAT_PROMPT_TEMPLATE.format(
            history=self.session.format_for_prompt(),
            context=context_text,
            question=user_input,
        )

        return self.llm.generate(
            prompt=prompt,
            system=SYSTEM_PROMPT,
        )

    # ------------------------------------------------------------------
    # RAG
    # ------------------------------------------------------------------

    def _get_rag_context(
        self,
        question: str,
    ) -> Optional[str]:
        if not self.rag.enabled:
            return None

        if not self.rag.should_use_rag(question):
            return None

        return self.rag.retrieve(question)

    # ------------------------------------------------------------------
    # Comandos internos
    # ------------------------------------------------------------------

    def _handle_builtin_commands(
        self,
        command: str,
    ) -> Optional[str]:
        cmd = command.strip().lower()

        aliases = {
            "exit": "/exit",
            "quit": "/exit",
            "sair": "/exit",
            "clear": "/clear",
            "cls": "/clear",
            "help": "/help",
            "ajuda": "/help",
            "tools": "/tools",
            "ferramentas": "/tools",
            "history": "/history",
            "hist": "/history",
            "/hist": "/history",
            "/history": "/history",
        }

        cmd = aliases.get(cmd, cmd)

        if cmd in {"/exit", "/quit"}:
            raise KeyboardInterrupt

        if cmd == "/clear":
            self.session.clear()
            self.session.add_system_message(SYSTEM_PROMPT)
            return "Histórico limpo."

        if cmd == "/help":
            return self._help()

        if cmd == "/tools":
            return self._list_tools()
        
        if cmd == "/history":
            return self._show_history()

        return None


    def _help(self) -> str:
        return """
            Comandos disponíveis:

            /help               - Exibe esta ajuda
            /clear              - Limpa o histórico
            /tools              - Lista ferramentas
            /exit               - Encerra o agente

            Ferramentas:

            ! <comando>          - Executa comando Linux
            ! ls -la

            @fs list             - Lista diretório
            @fs read arquivo.py  - Lê arquivo
            @fs write arq.txt texto
            """.strip()

    def _list_tools(self) -> str:
        tools = self.tools.list()

        if not tools:
            return "Nenhuma ferramenta registrada."

        lines = ["Ferramentas disponíveis:"]

        for name, description in tools.items():
            lines.append(f"- {name}: {description}")

        return "\n".join(lines)

    def _show_history(self) -> str:
        """
        Exibe o histórico atual da sessão.
        """
        messages = [
            msg
            for msg in self.session.get_messages()
            if msg["role"] != "system"
        ]

        if not messages:
            return "Nenhuma interação registrada."

        lines = ["Histórico da sessão:"]

        for i, message in enumerate(messages, start=1):
            role = message["role"].upper()
            content = message["content"].strip()

            if len(content) > 200:
                content = content[:197] + "..."

            lines.append(
                f"{i:02d}. [{role}] {content}"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def startup_message(self) -> str:
        rag_status = "ativo" if self.rag.enabled else "inativo"

        return (
            f"DevAgent iniciado com sucesso.\n"
            f"Modelo: {self.llm.model}\n"
            f"RAG: {rag_status}\n"
            f"Ferramentas: {len(self.tools.list())}\n"
            f"Digite /help para ajuda."
        )