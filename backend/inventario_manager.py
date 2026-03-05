import json
from rich.console import Console
import difflib # <-- 1. IMPORTA A BIBLIOTECA DE COMPARAÇÃO

console = Console()

class InventarioManager:
    def __init__(self, caminho_arquivo="data/inventario.json"):
        self.caminho_arquivo = caminho_arquivo
        self.dados = self._carregar_dados()
        self.nomes_itens = list(self.dados.keys()) # Lista de nomes para o fuzzy matching

    def _carregar_dados(self):
        try:
            with open(self.caminho_arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            console.print(f"[bold red]Arquivo de inventário não encontrado em {self.caminho_arquivo}[/bold red]")
            return {}

    def _salvar_dados(self):
        with open(self.caminho_arquivo, 'w', encoding='utf-8') as f:
            json.dump(self.dados, f, indent=2, ensure_ascii=False)

    def consultar_estoque(self, nome_item):
        # Usa a mesma lógica de fuzzy matching para consultas
        match = difflib.get_close_matches(nome_item.lower(), [k.lower() for k in self.nomes_itens], n=1, cutoff=0.6)
        
        if match:
            # Encontra a chave original (com maiúsculas/minúsculas)
            chave_correta = [k for k in self.nomes_itens if k.lower() == match[0]][0]
            return f"Temos {self.dados[chave_correta]['quantidade']} unidades de '{chave_correta}'."
        
        return f"Desculpe, não encontrei o item '{nome_item}' no inventário."

    def atualizar_estoque(self, nome_item_transcrito, quantidade, acao):
        """
        Atualiza o estoque. Se não tiver certeza, pede confirmação.
        Retorna um dicionário com o status da operação.
        """
        
        # 1. Tenta encontrar a correspondência mais próxima
        match = difflib.get_close_matches(nome_item_transcrito.lower(), [k.lower() for k in self.nomes_itens], n=1, cutoff=0.6)
        
        if not match:
            return {"status": "nao_encontrado", "mensagem": f"Erro: Item '{nome_item_transcrito}' não foi encontrado no inventário."}

        # 2. Encontra a chave original (com maiúsculas/minúsculas)
        chave_correta = [k for k in self.nomes_itens if k.lower() == match[0]][0]

        # 3. Verifica se a correspondência é exata o suficiente ou precisa de confirmação
        # Se "led vermelha" (transcrito) for diferente de "led vermelho" (chave correta), pede confirmação
        if nome_item_transcrito.lower() != chave_correta.lower():
            return {
                "status": "confirmacao_necessaria", 
                "item_sugerido": chave_correta, 
                "item_original": nome_item_transcrito
            }

        # 4. Se chegou aqui, a correspondência é exata. Prossiga com a lógica de estoque.
        if acao == 'remover':
            estoque_atual = self.dados[chave_correta]['quantidade']
            if estoque_atual >= quantidade:
                self.dados[chave_correta]['quantidade'] -= quantidade
                self._salvar_dados()
                nova_qtd = self.dados[chave_correta]['quantidade']
                return {"status": "sucesso", "mensagem": f"Ok! Estoque de '{chave_correta}' atualizado para {nova_qtd} unidades."}
            else:
                return {"status": "erro_estoque", "mensagem": f"Erro: Estoque insuficiente de '{chave_correta}'. Você tentou remover {quantidade}, mas só temos {estoque_atual}."}
        
        elif acao == 'adicionar':
            self.dados[chave_correta]['quantidade'] += quantidade
            self._salvar_dados()
            nova_qtd = self.dados[chave_correta]['quantidade']
            return {"status": "sucesso", "mensagem": f"Ok! Estoque de '{chave_correta}' atualizado para {nova_qtd} unidades."}
        
    def cadastrar_novo_item(self, nome_item, quantidade_inicial):
        """Cadastra um item que não existe no inventário."""
        nome_item_formatado = nome_item.strip().title() # Garante formatação (ex: Led Verde)
        
        if nome_item_formatado.lower() in [k.lower() for k in self.nomes_itens]:
            return {"status": "erro_estoque", "mensagem": f"Erro: O item '{nome_item_formatado}' já existe no inventário."}

        # Adiciona o novo item
        self.dados[nome_item_formatado] = {"quantidade": quantidade_inicial}
        self.nomes_itens.append(nome_item_formatado) # Atualiza a lista de nomes
        self._salvar_dados()
        
        return {"status": "sucesso", "mensagem": f"Item '{nome_item_formatado}' cadastrado com sucesso com {quantidade_inicial} unidades."}

    def gerar_relatorio_uso(self):
        """Gera um relatório simples de contagem de estoque."""
        if not self.dados:
            return "O inventário está vazio."
            
        relatorio = "Relatório de Estoque Atual:\n"
        for item, data in self.dados.items():
            relatorio += f"- {item}: {data['quantidade']} unidades\n"
            
        return relatorio