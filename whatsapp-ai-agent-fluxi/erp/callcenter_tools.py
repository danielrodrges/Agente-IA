"""
Ferramentas do call center para o agente IA.
Registra automaticamente as ferramentas de agendamento,
consulta, cancelamento e escalação no sistema Fluxi.
"""
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ferramenta.ferramenta_model import Ferramenta, ToolType, ToolScope, OutputDestination
from ferramenta.ferramenta_service import FerramentaService
import json


# Definições das ferramentas do call center
CALLCENTER_TOOLS: List[Dict[str, Any]] = [
    # ============================================================
    # BUSCA E CADASTRO DE PACIENTES
    # ============================================================
    {
        "nome": "buscar_paciente",
        "descricao": "Busca informações de um paciente cadastrado pelo CPF ou telefone. Use sempre que o paciente informar seus dados para identificá-lo no sistema.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "cpf": {
                "type": "string",
                "description": "CPF do paciente (apenas números)",
                "required": False
            },
            "telefone": {
                "type": "string",
                "description": "Telefone do paciente (apenas números com DDD)",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

if argumentos.get("cpf"):
    resultado = asyncio.get_event_loop().run_until_complete(
        erp_mock.buscar_paciente(cpf=argumentos["cpf"])
    )
elif argumentos.get("telefone"):
    resultado = asyncio.get_event_loop().run_until_complete(
        erp_mock.buscar_paciente(telefone=argumentos["telefone"])
    )
else:
    resultado = {"erro": "Informe CPF ou telefone do paciente"}
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "cadastrar_paciente",
        "descricao": "Cadastra um novo paciente no sistema. Use quando o paciente não for encontrado e desejar agendar uma consulta ou exame.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "nome": {
                "type": "string",
                "description": "Nome completo do paciente",
                "required": True
            },
            "cpf": {
                "type": "string",
                "description": "CPF do paciente (apenas números)",
                "required": True
            },
            "telefone": {
                "type": "string",
                "description": "Telefone com DDD (apenas números)",
                "required": True
            },
            "data_nascimento": {
                "type": "string",
                "description": "Data de nascimento no formato YYYY-MM-DD",
                "required": False
            },
            "email": {
                "type": "string",
                "description": "E-mail do paciente",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

dados = {
    "nome": argumentos["nome"],
    "cpf": argumentos["cpf"],
    "telefone": argumentos["telefone"],
}
if argumentos.get("data_nascimento"):
    dados["data_nascimento"] = argumentos["data_nascimento"]
if argumentos.get("email"):
    dados["email"] = argumentos["email"]

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.cadastrar_paciente(dados)
)
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # ESPECIALIDADES E MÉDICOS
    # ============================================================
    {
        "nome": "listar_especialidades",
        "descricao": "Lista todas as especialidades médicas disponíveis na clínica com seus preços. Use quando o paciente perguntar quais especialidades estão disponíveis ou quanto custa uma consulta.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({}),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.listar_especialidades()
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "listar_medicos",
        "descricao": "Lista os médicos disponíveis, opcionalmente filtrados por especialidade. Use quando o paciente quiser saber quais médicos atendem uma especialidade.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "especialidade_id": {
                "type": "string",
                "description": "ID da especialidade para filtrar os médicos (opcional)",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.listar_medicos(especialidade_id=argumentos.get("especialidade_id"))
)
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # HORÁRIOS E AGENDAMENTO DE CONSULTAS
    # ============================================================
    {
        "nome": "listar_horarios_disponiveis",
        "descricao": "Lista os horários disponíveis para agendamento de consulta com um médico específico em uma data. Use quando o paciente quiser escolher um horário para agendar.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "medico_id": {
                "type": "string",
                "description": "ID do médico",
                "required": True
            },
            "data": {
                "type": "string",
                "description": "Data desejada no formato YYYY-MM-DD",
                "required": True
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.listar_horarios_disponiveis(
        medico_id=argumentos["medico_id"],
        data=argumentos["data"]
    )
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "agendar_consulta",
        "descricao": "Agenda uma consulta para um paciente com um médico em uma data e horário específicos. Use SOMENTE após confirmar todos os dados com o paciente (médico, data, horário).",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "paciente_id": {
                "type": "string",
                "description": "ID do paciente no sistema",
                "required": True
            },
            "medico_id": {
                "type": "string",
                "description": "ID do médico",
                "required": True
            },
            "data_hora": {
                "type": "string",
                "description": "Data e hora da consulta no formato YYYY-MM-DD HH:MM",
                "required": True
            },
            "especialidade_id": {
                "type": "string",
                "description": "ID da especialidade da consulta",
                "required": True
            },
            "observacoes": {
                "type": "string",
                "description": "Observações adicionais sobre a consulta",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

dados = {
    "paciente_id": argumentos["paciente_id"],
    "medico_id": argumentos["medico_id"],
    "data_hora": argumentos["data_hora"],
    "especialidade_id": argumentos["especialidade_id"],
}
if argumentos.get("observacoes"):
    dados["observacoes"] = argumentos["observacoes"]

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.agendar_consulta(dados)
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "remarcar_consulta",
        "descricao": "Remarca uma consulta existente para uma nova data e horário. Use quando o paciente precisar mudar o dia ou horário de uma consulta já agendada.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "agendamento_id": {
                "type": "string",
                "description": "ID do agendamento a ser remarcado",
                "required": True
            },
            "nova_data_hora": {
                "type": "string",
                "description": "Nova data e hora no formato YYYY-MM-DD HH:MM",
                "required": True
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.remarcar_consulta(
        agendamento_id=argumentos["agendamento_id"],
        nova_data_hora=argumentos["nova_data_hora"]
    )
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "cancelar_consulta",
        "descricao": "Cancela uma consulta agendada. Use quando o paciente solicitar o cancelamento. IMPORTANTE: Sempre confirme com o paciente antes de cancelar.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "agendamento_id": {
                "type": "string",
                "description": "ID do agendamento a ser cancelado",
                "required": True
            },
            "motivo": {
                "type": "string",
                "description": "Motivo do cancelamento",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.cancelar_consulta(
        agendamento_id=argumentos["agendamento_id"],
        motivo=argumentos.get("motivo", "Solicitado pelo paciente")
    )
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "confirmar_consulta",
        "descricao": "Confirma a presença do paciente em uma consulta agendada. Use quando o paciente confirmar que irá comparecer.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "agendamento_id": {
                "type": "string",
                "description": "ID do agendamento a ser confirmado",
                "required": True
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.confirmar_consulta(agendamento_id=argumentos["agendamento_id"])
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "buscar_agendamentos",
        "descricao": "Busca os agendamentos (consultas e exames) de um paciente. Use para verificar consultas futuras ou passadas do paciente.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "paciente_id": {
                "type": "string",
                "description": "ID do paciente",
                "required": True
            },
            "status": {
                "type": "string",
                "description": "Filtrar por status: agendado, confirmado, cancelado, realizado (opcional)",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.buscar_agendamentos(
        paciente_id=argumentos["paciente_id"],
        status=argumentos.get("status")
    )
)
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # EXAMES
    # ============================================================
    {
        "nome": "listar_exames_disponiveis",
        "descricao": "Lista os exames disponíveis na clínica com seus preços e preparos necessários. Use quando o paciente perguntar sobre exames.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({}),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.listar_exames_disponiveis()
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "agendar_exame",
        "descricao": "Agenda um exame para um paciente. Informe ao paciente sobre o preparo necessário após agendar.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "paciente_id": {
                "type": "string",
                "description": "ID do paciente",
                "required": True
            },
            "exame_id": {
                "type": "string",
                "description": "ID do exame desejado",
                "required": True
            },
            "data_hora": {
                "type": "string",
                "description": "Data e hora para o exame no formato YYYY-MM-DD HH:MM",
                "required": True
            },
            "observacoes": {
                "type": "string",
                "description": "Observações adicionais",
                "required": False
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

dados = {
    "paciente_id": argumentos["paciente_id"],
    "exame_id": argumentos["exame_id"],
    "data_hora": argumentos["data_hora"],
}
if argumentos.get("observacoes"):
    dados["observacoes"] = argumentos["observacoes"]

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.agendar_exame(dados)
)
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # ORÇAMENTO E INFORMAÇÕES
    # ============================================================
    {
        "nome": "buscar_orcamento",
        "descricao": "Busca o orçamento/valor de procedimentos, consultas ou exames. Use quando o paciente perguntar valores ou pedir um orçamento.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "tipo": {
                "type": "string",
                "description": "Tipo do procedimento: consulta ou exame",
                "required": True,
                "enum": ["consulta", "exame"]
            },
            "item_id": {
                "type": "string",
                "description": "ID da especialidade (para consulta) ou ID do exame",
                "required": True
            }
        }),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.buscar_orcamento(
        tipo=argumentos["tipo"],
        item_id=argumentos["item_id"]
    )
)
""",
        "output": OutputDestination.LLM,
    },
    {
        "nome": "obter_info_clinica",
        "descricao": "Obtém informações gerais sobre a clínica: endereço, horário de funcionamento, formas de pagamento, convênios aceitos. Use quando o paciente perguntar sobre a clínica.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({}),
        "codigo_python": """
import asyncio
from erp.erp_mock import erp_mock

resultado = asyncio.get_event_loop().run_until_complete(
    erp_mock.obter_info_clinica()
)
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # ESCALAÇÃO PARA ATENDENTE HUMANO
    # ============================================================
    {
        "nome": "solicitar_ajuda_atendente",
        "descricao": (
            "Solicita ajuda de um atendente humano quando você NÃO conseguir resolver a "
            "situação sozinho. Use nos seguintes casos:\n"
            "- Paciente insatisfeito ou reclamando\n"
            "- Dúvida sobre política que você não sabe responder\n"
            "- Paciente solicitando exceção a uma regra\n"
            "- Erro persistente no sistema\n"
            "- Qualquer situação que vá além das suas capacidades\n"
            "IMPORTANTE: Informe o paciente que está encaminhando para um atendente."
        ),
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({
            "tipo": {
                "type": "string",
                "description": "Tipo da solicitação: duvida_agendamento, autorizacao_cancelamento, informacao_erp, excecao_politica, reclamacao, cadastro_paciente, informacao_clinica, outro",
                "required": True
            },
            "prioridade": {
                "type": "string",
                "description": "Prioridade: baixa, media, alta, urgente",
                "required": True
            },
            "contexto": {
                "type": "string",
                "description": "Resumo detalhado da situação e o que o paciente precisa. Inclua todos os dados relevantes já coletados.",
                "required": True
            },
            "telefone_cliente": {
                "type": "string",
                "description": "Telefone do cliente que está sendo atendido",
                "required": True
            }
        }),
        "codigo_python": """
import asyncio
from database import get_db

# Importar serviço de escalação
from escalacao.escalacao_service import EscalacaoService
from escalacao.escalacao_schema import EscalacaoCriar

# Criar escalação
dados = EscalacaoCriar(
    sessao_id=argumentos.get("sessao_id", 1),
    telefone_cliente=argumentos["telefone_cliente"],
    tipo=argumentos["tipo"],
    prioridade=argumentos["prioridade"],
    pergunta_ia=argumentos["contexto"],
)

# Obter sessão do banco
db_gen = get_db()
db_session = next(db_gen)
try:
    escalacao = asyncio.get_event_loop().run_until_complete(
        EscalacaoService.criar_escalacao(db_session, dados)
    )
    resultado = {
        "sucesso": True,
        "escalacao_id": escalacao.id,
        "status": escalacao.status.value,
        "mensagem": "Solicitação enviada ao atendente. Ele será notificado em tempo real."
    }
finally:
    try:
        next(db_gen)
    except StopIteration:
        pass
""",
        "output": OutputDestination.LLM,
    },

    # ============================================================
    # UTILITÁRIOS
    # ============================================================
    {
        "nome": "obter_data_hora_atual",
        "descricao": "Obtém a data e hora atuais no fuso horário de Brasília. Use quando precisar saber que dia é hoje ou que horas são para contexto de agendamento.",
        "tool_type": ToolType.CODE,
        "tool_scope": ToolScope.PRINCIPAL,
        "params": json.dumps({}),
        "codigo_python": """
from datetime import datetime
import pytz

tz = pytz.timezone("America/Sao_Paulo")
agora = datetime.now(tz)

resultado = {
    "data": agora.strftime("%Y-%m-%d"),
    "hora": agora.strftime("%H:%M"),
    "dia_semana": agora.strftime("%A"),
    "data_formatada": agora.strftime("%d/%m/%Y"),
    "dia_semana_pt": {
        "Monday": "Segunda-feira",
        "Tuesday": "Terça-feira",
        "Wednesday": "Quarta-feira",
        "Thursday": "Quinta-feira",
        "Friday": "Sexta-feira",
        "Saturday": "Sábado",
        "Sunday": "Domingo"
    }.get(agora.strftime("%A"), agora.strftime("%A"))
}
""",
        "output": OutputDestination.LLM,
    },
]


def registrar_ferramentas_callcenter(db: Session) -> List[Ferramenta]:
    """
    Registra todas as ferramentas do call center no banco de dados.
    Se uma ferramenta já existir (pelo nome), ela será atualizada.
    
    Returns:
        Lista de ferramentas registradas/atualizadas
    """
    ferramentas_registradas = []
    
    for tool_def in CALLCENTER_TOOLS:
        nome = tool_def["nome"]
        existente = FerramentaService.obter_por_nome(db, nome)
        
        if existente:
            # Atualizar ferramenta existente
            for campo, valor in tool_def.items():
                setattr(existente, campo, valor)
            existente.ativa = True
            db.commit()
            db.refresh(existente)
            ferramentas_registradas.append(existente)
            print(f"🔄 Ferramenta atualizada: {nome}")
        else:
            # Criar nova ferramenta
            ferramenta = Ferramenta(
                nome=tool_def["nome"],
                descricao=tool_def["descricao"],
                tool_type=tool_def["tool_type"],
                tool_scope=tool_def["tool_scope"],
                params=tool_def.get("params"),
                codigo_python=tool_def.get("codigo_python"),
                output=tool_def.get("output", OutputDestination.LLM),
                ativa=True,
                substituir=False,
            )
            db.add(ferramenta)
            db.commit()
            db.refresh(ferramenta)
            ferramentas_registradas.append(ferramenta)
            print(f"✅ Ferramenta criada: {nome}")
    
    print(f"\n📋 Total de ferramentas do call center: {len(ferramentas_registradas)}")
    return ferramentas_registradas


def associar_ferramentas_ao_agente(db: Session, agente_id: int) -> int:
    """
    Associa todas as ferramentas do call center a um agente específico.
    
    Args:
        db: Sessão do banco
        agente_id: ID do agente
        
    Returns:
        Número de ferramentas associadas
    """
    from agente.agente_service import AgenteService
    
    # Buscar todas as ferramentas do call center
    ferramentas_ids = []
    for tool_def in CALLCENTER_TOOLS:
        ferramenta = FerramentaService.obter_por_nome(db, tool_def["nome"])
        if ferramenta:
            ferramentas_ids.append(ferramenta.id)
    
    # Buscar ferramentas já associadas ao agente
    ferramentas_atuais = AgenteService.listar_ferramentas(db, agente_id)
    ids_atuais = [f.id for f in ferramentas_atuais]
    
    # Adicionar as novas sem remover as existentes
    todos_ids = list(set(ids_atuais + ferramentas_ids))
    
    AgenteService.atualizar_ferramentas(db, agente_id, todos_ids)
    
    print(f"🔗 {len(ferramentas_ids)} ferramentas do call center associadas ao agente {agente_id}")
    return len(ferramentas_ids)
