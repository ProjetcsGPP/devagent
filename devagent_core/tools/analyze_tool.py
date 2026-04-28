from pathlib import Path


class AnalyzeTool:
    def __init__(self, rag):
        self.rag = rag

    def execute(self, file_path: str) -> str:
        path = Path(file_path)

        if not path.exists():
            return f"Arquivo não encontrado: {file_path}"

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return f"Erro ao ler arquivo: {e}"

        prompt = f"""
Analise detalhadamente o seguinte código.

Arquivo: {file_path}

{content[:12000]}

Forneça:
1. Objetivo do arquivo
2. Principais classes e funções
3. Dependências
4. Pontos fortes
5. Melhorias recomendadas
6. Possíveis problemas

Resposta:
"""

        return self.rag.llm.generate(prompt)