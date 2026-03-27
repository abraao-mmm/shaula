import os
from typing import List
from rich.console import Console

console = Console()

class BancoDeIdentidade:
    """
    Carrega e pesquisa a "memória de identidade" da Shaula 
    (seus diários de bordo e seu próprio código-fonte).
    """
    def __init__(self, caminho_pasta="data/identidade"):
        self.base_conhecimento = {}
        self._carregar_arquivos(caminho_pasta)

    def _carregar_arquivos(self, caminho_pasta):
        """Carrega todos os arquivos .txt e .py da pasta de identidade."""
        console.log(f"🧠 [Banco de Identidade] Carregando arquivos de '{caminho_pasta}'...")
        try:
            for nome_arquivo in os.listdir(caminho_pasta):
                if nome_arquivo.endswith((".txt", ".py")):
                    caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
                    try:
                        with open(caminho_completo, 'r', encoding='utf-8') as f:
                            self.base_conhecimento[nome_arquivo] = f.read()
                    except Exception as e:
                        console.print(f"[red]Erro ao ler {nome_arquivo}: {e}[/red]")
            console.log(f"✅ [Banco de Identidade] {len(self.base_conhecimento)} arquivos carregados.")
        except FileNotFoundError:
            console.print(f"[red]Pasta de identidade '{caminho_pasta}' não encontrada.[/red]")

    def buscar_contexto_relevante(self, pergunta_usuario: str, max_trechos: int = 5) -> str:
        """
        Pesquisa na base de conhecimento por trechos relevantes para a pergunta.
        Esta é uma busca de palavra-chave simples (não é um vetor).
        """
        palavras_chave = set(pergunta_usuario.lower().split())
        palavras_chave_filtradas = {p for p in palavras_chave if len(p) > 3} # Ignora palavras pequenas

        if not palavras_chave_filtradas:
            return "Nenhum contexto específico encontrado."

        trechos_encontrados = []
        for nome_arquivo, conteudo in self.base_conhecimento.items():
            for linha in conteudo.splitlines():
                linha_lower = linha.lower()
                for palavra in palavras_chave_filtradas:
                    if palavra in linha_lower:
                        trechos_encontrados.append(f"[Trecho de {nome_arquivo}]: ...{linha.strip()}...")
                        if len(trechos_encontrados) >= max_trechos:
                            break
                if len(trechos_encontrados) >= max_trechos:
                    break
            if len(trechos_encontrados) >= max_trechos:
                break
        
        if not trechos_encontrados:
            return "Nenhum documento de identidade parece relevante para esta pergunta."
            
        return "\n".join(trechos_encontrados)