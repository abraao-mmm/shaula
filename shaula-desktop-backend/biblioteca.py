import os
from typing import List
from rich.console import Console
import PyPDF2 # Importa a nova biblioteca

console = Console()

class Biblioteca:
    """
    Carrega e pesquisa documentos (PDFs, TXTs) da pasta da biblioteca.
    """
    def __init__(self, caminho_pasta="data/biblioteca"):
        self.base_conhecimento = {} # Armazena o texto dos arquivos
        self._carregar_arquivos(caminho_pasta)

    def _ler_pdf(self, caminho_completo: str) -> str:
        """Função específica para extrair texto de um PDF."""
        try:
            texto = ""
            with open(caminho_completo, 'rb') as f:
                leitor_pdf = PyPDF2.PdfReader(f)
                for pagina in leitor_pdf.pages:
                    texto += pagina.extract_text()
            return texto
        except Exception as e:
            console.print(f"[red]Erro ao ler PDF {caminho_completo}: {e}[/red]")
            return ""

    def _carregar_arquivos(self, caminho_pasta):
        """Carrega todos os arquivos .txt e .pdf da pasta da biblioteca."""
        console.log(f"📚 [Biblioteca] Carregando documentos de '{caminho_pasta}'...")
        try:
            for nome_arquivo in os.listdir(caminho_pasta):
                caminho_completo = os.path.join(caminho_pasta, nome_arquivo)
                if nome_arquivo.endswith(".pdf"):
                    self.base_conhecimento[nome_arquivo] = self._ler_pdf(caminho_completo)
                elif nome_arquivo.endswith(".txt"):
                    with open(caminho_completo, 'r', encoding='utf-8') as f:
                        self.base_conhecimento[nome_arquivo] = f.read()
            
            console.log(f"✅ [Biblioteca] {len(self.base_conhecimento)} documentos carregados.")
        except FileNotFoundError:
            console.print(f"[red]Pasta da biblioteca '{caminho_pasta}' não encontrada.[/red]")

    def buscar_contexto_documento(self, nome_arquivo_parcial: str) -> str:
        """
        Encontra um documento pelo nome e retorna seu conteúdo.
        """
        nome_arquivo_lower = nome_arquivo_parcial.lower()
        
        for nome_arquivo, conteudo in self.base_conhecimento.items():
            if nome_arquivo_lower in nome_arquivo.lower():
                console.log(f"📚 [Biblioteca] Documento '{nome_arquivo}' encontrado.")
                # Retorna apenas os primeiros 4000 caracteres para não estourar o prompt
                return conteudo[:4000] 
        
        return "Desculpe, não encontrei nenhum documento com esse nome na minha biblioteca."