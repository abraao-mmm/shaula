from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum
from datetime import datetime, timezone
import uuid

# --- ENUMS (Opções Fixas) ---
class TipoPensamento(str, Enum):
    IDEIA = "Ideia"
    TAREFA = "Tarefa"
    REFERENCIA = "Referencia"
    DUVIDA = "Duvida"

class OrigemInput(str, Enum):
    MOBILE = "mobile"
    TOTEM = "totem"
    WEB = "web"

class StatusPensamento(str, Enum):
    ATIVO = "ativo"
    RESOLVIDO = "resolvido"
    ARQUIVADO = "arquivado"

class NivelConfianca(str, Enum):
    BAIXA = "Baixa"
    MEDIA = "Media"
    ALTA = "Alta"

class Tendencia(str, Enum):
    ESTAVEL = "Estavel"
    MELHORANDO = "Melhorando"
    PIORANDO = "Piorando"

# NOVO: Tipos de Estado Humano
class TipoEstado(str, Enum):
    CRISE = "Crise"            # "Tô mal, não quero ir"
    OBSERVACAO = "Observacao"  # "Não posso mais faltar no curso"
    ROTINA = "Rotina"          # "Curso FPF Terça e Quinta"

# --- MODELOS DE DADOS ---

class Pensamento(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: TipoPensamento
    conteudo: str
    origem: OrigemInput
    projeto_associado: Optional[str] = None
    status: StatusPensamento = StatusPensamento.ATIVO
    confianca: NivelConfianca = NivelConfianca.MEDIA
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# NOVO: Entidade para Crises e Rotinas
class RegistroEstado(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipo: TipoEstado
    conteudo: str
    intensidade: int = 1 # 1 (Leve) a 5 (Crítico) - Relevante para Crises
    valido_ate: Optional[datetime] = None 
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class EstadoCognitivoGlobal(BaseModel):
    score_atual: int
    tendencia: Tendencia
    nivel_carga: str 
    projeto_foco: Optional[str]
    total_pendencias: int
    diagnostico_resumido: str 
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class BriefingExecutivo(BaseModel):
    estado_atual: EstadoCognitivoGlobal
    gargalos_identificados: List[str]
    estrategia_do_momento: str
    acao_tatica_sugerida: str
    mensagem_motivacional: Optional[str] = None