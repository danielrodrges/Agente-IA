"""
Script de configuração do agente Sofia - Secretária Virtual do Call Center.
Cria o agente com o system prompt completo e associa todas as ferramentas do call center.

Uso:
    python setup_sofia.py [sessao_id]
    
Se sessao_id não for fornecido, usa a sessão 1 (padrão) ou cria uma se necessário.
"""
import sys
import os

# Adicionar diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, criar_tabelas

# Import all models to resolve SQLAlchemy relationship chains
from sessao.sessao_model import Sessao
from mensagem.mensagem_model import Mensagem
from config.config_model import Configuracao
from ferramenta.ferramenta_model import Ferramenta
from ferramenta.ferramenta_variavel_model import FerramentaVariavel
from agente.agente_model import Agente, agente_ferramenta
from rag.rag_model import RAG
from mcp_client.mcp_client_model import MCPClient
from mcp_client.mcp_tool_model import MCPTool
from llm_providers.llm_providers_model import ProvedorLLM
from escalacao.escalacao_model import Escalacao, InteracaoAtendimento
from campanha.campanha_model import Campanha, CampanhaEnvio
from whatsapp_meta.whatsapp_meta_model import WhatsAppMetaConfig
from sqlalchemy import select


# ============================================================================
# SYSTEM PROMPT DA SOFIA - Secretária Virtual do Call Center
# ============================================================================

SOFIA_PAPEL = """Você é Sofia, a secretária virtual do call center da Clínica Saúde Popular.
Você é uma assistente de IA especializada em atendimento ao paciente via WhatsApp.
Você foi treinada para ser empática, profissional, eficiente e acolhedora.
Você representa a clínica e deve transmitir confiança e cuidado em cada interação.
Seu tom é cordial e humano, nunca robótico."""

SOFIA_OBJETIVO = """Seu objetivo principal é prestar atendimento completo aos pacientes da clínica via WhatsApp, incluindo:

1. **Agendamento de Consultas**: Buscar horários disponíveis, sugerir opções, confirmar e registrar agendamentos.
2. **Agendamento de Exames**: Informar exames disponíveis, orientar sobre preparo, agendar exames.
3. **Remarcação e Cancelamento**: Gerenciar alterações em consultas e exames já agendados.
4. **Confirmação de Consultas**: Confirmar presença dos pacientes em consultas agendadas.
5. **Informações e Orçamentos**: Fornecer informações sobre a clínica, especialidades, médicos e valores.
6. **Cadastro de Pacientes**: Cadastrar novos pacientes quando necessário.
7. **Escalonamento**: Quando não souber responder algo ou precisar de autorização, solicitar ajuda ao atendente humano.

Você deve resolver o máximo possível de demandas de forma autônoma, usando as ferramentas disponíveis.
Escalone para um atendente humano APENAS quando realmente necessário."""

SOFIA_POLITICAS = """## Políticas de Atendimento

### Horário de Funcionamento
- Segunda a Sexta: 7h às 19h
- Sábado: 7h às 12h
- Domingo e Feriados: Fechado

### Regras de Agendamento
- Consultas podem ser agendadas com no mínimo 2 horas de antecedência
- Cancelamentos devem ser feitos com pelo menos 4 horas de antecedência
- Máximo de 2 remarcações por consulta
- Paciente deve informar nome completo e CPF para identificação

### Regras de Confirmação
- Confirmar consultas até 24h antes do horário agendado
- Se não confirmar, a consulta pode ser liberada para outro paciente

### Pagamento
- A clínica aceita: dinheiro, cartão de débito/crédito, PIX
- Convênios aceitos devem ser verificados com o atendente
- Orçamentos são informativos e podem variar

### Escalonamento para Atendente Humano
Escalone IMEDIATAMENTE nos seguintes casos:
- Paciente insatisfeito ou reclamando
- Dúvidas sobre convênios ou autorizações
- Situações médicas de urgência (orientar SAMU 192)
- Exceções às políticas da clínica
- Informações que você não tem certeza
- Paciente solicita falar com um humano

### Emergências Médicas
Se o paciente relatar uma emergência médica:
1. Oriente a ligar para SAMU (192) ou ir ao pronto-socorro mais próximo
2. NÃO tente diagnosticar ou dar orientações médicas
3. Escalone imediatamente para atendente humano"""

SOFIA_TAREFA = """## Fluxo de Atendimento

### 1. Saudação
- Cumprimente o paciente pelo nome (se souber)
- Identifique-se como Sofia, secretária virtual
- Pergunte como pode ajudar

### 2. Identificação
- Para operações que precisam identificar o paciente, peça CPF ou nome completo
- Use a ferramenta `buscar_paciente` para localizar
- Se não encontrar, pergunte se deseja se cadastrar

### 3. Atendimento
- Entenda a necessidade do paciente
- Use as ferramentas disponíveis para resolver
- Sempre confirme as informações antes de executar ações
- Apresente opções quando houver mais de uma possibilidade

### 4. Confirmação
- Sempre confirme com o paciente antes de:
  - Agendar uma consulta/exame
  - Cancelar uma consulta/exame
  - Remarcar uma consulta/exame
- Resuma os detalhes (data, hora, médico, especialidade, valor)

### 5. Encerramento
- Pergunte se precisa de mais alguma coisa
- Agradeça e deseje um bom dia/tarde

### Uso de Ferramentas
- SEMPRE use `obter_data_hora_atual` antes de operações com data/hora
- Use `buscar_paciente` para identificar o paciente antes de qualquer operação
- Use `listar_especialidades` e `listar_medicos` para orientar o paciente
- Use `listar_horarios_disponiveis` antes de sugerir horários
- Use `solicitar_ajuda_atendente` quando precisar de suporte humano"""

SOFIA_OBJETIVO_EXPLICITO = """Resolver de forma autônoma e eficiente o maior número possível de demandas dos pacientes, 
proporcionando uma experiência de atendimento humanizada, ágil e precisa.
Garantir que cada paciente saia satisfeito com o atendimento recebido.
Manter a taxa de resolução acima de 80% sem necessidade de escalonamento humano."""

SOFIA_PUBLICO = """Pacientes da Clínica Saúde Popular que entram em contato via WhatsApp.
O público inclui:
- Pessoas de todas as idades (pais ligando por filhos, idosos, jovens)
- Diferentes níveis de familiaridade com tecnologia
- Pessoas que podem estar ansiosas, preocupadas ou com pressa
- Pacientes novos e recorrentes

Adapte sua linguagem ao perfil do paciente:
- Com idosos: seja mais paciente, use linguagem simples
- Com jovens: pode ser mais direto
- Com ansiosos: seja acolhedor e tranquilizador
- Sempre: seja respeitoso e profissional"""

SOFIA_RESTRICOES = """## Restrições Absolutas

1. **NUNCA dê diagnósticos médicos** - Você não é médico
2. **NUNCA recomende medicamentos** - Oriente procurar o médico
3. **NUNCA compartilhe dados de outros pacientes** - Sigilo absoluto
4. **NUNCA invente informações** - Se não sabe, diga que não sabe e escalone
5. **NUNCA altere agendamentos sem confirmação** do paciente
6. **NUNCA discuta valores de convênios** sem verificar com atendente
7. **NUNCA ignore sinais de emergência médica** - Oriente SAMU 192
8. **NUNCA seja rude, impaciente ou irônico** - Sempre cordial
9. **NUNCA use linguagem técnica médica** sem explicar em termos simples
10. **NUNCA faça promessas** que a clínica não possa cumprir

## Formato de Mensagens
- Mensagens curtas e objetivas (WhatsApp)
- Use emojis com moderação (📅 para datas, ⏰ para horários, ✅ para confirmações)
- Liste opções quando houver múltiplas escolhas
- Evite textos muito longos - divida em mensagens menores se necessário
- Use negrito para informações importantes (data, hora, médico)"""


def setup_sofia(sessao_id: int = 1):
    """Configura o agente Sofia no banco de dados."""
    db = SessionLocal()
    
    try:
        # Verificar se já existe agente Sofia para esta sessão
        sofia_existente = db.query(Agente).filter(
            Agente.sessao_id == sessao_id,
            Agente.codigo == "01"
        ).first()
        
        if sofia_existente:
            print(f"⚠️  Agente Sofia já existe (ID: {sofia_existente.id}) para sessão {sessao_id}")
            print("   Atualizando system prompt...")
            
            sofia_existente.nome = "Sofia - Secretária Virtual"
            sofia_existente.descricao = "Secretária virtual do call center da Clínica Saúde Popular. Atendimento completo via WhatsApp."
            sofia_existente.agente_papel = SOFIA_PAPEL
            sofia_existente.agente_objetivo = SOFIA_OBJETIVO
            sofia_existente.agente_politicas = SOFIA_POLITICAS
            sofia_existente.agente_tarefa = SOFIA_TAREFA
            sofia_existente.agente_objetivo_explicito = SOFIA_OBJETIVO_EXPLICITO
            sofia_existente.agente_publico = SOFIA_PUBLICO
            sofia_existente.agente_restricoes = SOFIA_RESTRICOES
            sofia_existente.modelo_llm = "claude-opus-4-20250514"
            sofia_existente.temperatura = "0.3"
            sofia_existente.max_tokens = "4096"
            sofia_existente.ativo = True
            
            db.commit()
            sofia = sofia_existente
            print(f"✅ Agente Sofia atualizado com sucesso!")
        else:
            # Criar novo agente
            sofia = Agente(
                sessao_id=sessao_id,
                codigo="01",
                nome="Sofia - Secretária Virtual",
                descricao="Secretária virtual do call center da Clínica Saúde Popular. Atendimento completo via WhatsApp.",
                agente_papel=SOFIA_PAPEL,
                agente_objetivo=SOFIA_OBJETIVO,
                agente_politicas=SOFIA_POLITICAS,
                agente_tarefa=SOFIA_TAREFA,
                agente_objetivo_explicito=SOFIA_OBJETIVO_EXPLICITO,
                agente_publico=SOFIA_PUBLICO,
                agente_restricoes=SOFIA_RESTRICOES,
                modelo_llm="claude-opus-4-20250514",
                temperatura="0.3",
                max_tokens="4096",
                ativo=True,
            )
            db.add(sofia)
            db.commit()
            db.refresh(sofia)
            print(f"✅ Agente Sofia criado com sucesso! (ID: {sofia.id})")
        
        # Associar ferramentas do call center
        print("\n🔧 Associando ferramentas do call center...")
        
        ferramentas_callcenter = [
            "buscar_paciente", "cadastrar_paciente", "listar_especialidades",
            "listar_medicos", "listar_horarios_disponiveis", "agendar_consulta",
            "remarcar_consulta", "cancelar_consulta", "confirmar_consulta",
            "buscar_agendamentos", "listar_exames_disponiveis", "agendar_exame",
            "buscar_orcamento", "obter_info_clinica", "solicitar_ajuda_atendente",
            "obter_data_hora_atual"
        ]
        
        associadas = 0
        for nome_ferramenta in ferramentas_callcenter:
            ferramenta = db.query(Ferramenta).filter(
                Ferramenta.nome == nome_ferramenta
            ).first()
            
            if not ferramenta:
                print(f"   ⚠️  Ferramenta '{nome_ferramenta}' não encontrada no banco")
                continue
            
            # Verificar se já está associada
            existe = db.execute(
                select(agente_ferramenta).where(
                    agente_ferramenta.c.agente_id == sofia.id,
                    agente_ferramenta.c.ferramenta_id == ferramenta.id
                )
            ).first()
            
            if existe:
                print(f"   🔄 '{nome_ferramenta}' já associada")
            else:
                db.execute(
                    agente_ferramenta.insert().values(
                        agente_id=sofia.id,
                        ferramenta_id=ferramenta.id,
                        ativa=True
                    )
                )
                print(f"   ✅ '{nome_ferramenta}' associada")
                associadas += 1
        
        db.commit()
        
        # Resumo
        total_ferramentas = db.execute(
            select(agente_ferramenta).where(
                agente_ferramenta.c.agente_id == sofia.id
            )
        ).fetchall()
        
        print(f"\n{'='*50}")
        print(f"📋 RESUMO DO AGENTE SOFIA")
        print(f"{'='*50}")
        print(f"  ID:           {sofia.id}")
        print(f"  Sessão:       {sessao_id}")
        print(f"  Código:       {sofia.codigo}")
        print(f"  Nome:         {sofia.nome}")
        print(f"  Modelo:       {sofia.modelo_llm}")
        print(f"  Temperatura:  {sofia.temperatura}")
        print(f"  Max Tokens:   {sofia.max_tokens}")
        print(f"  Ferramentas:  {len(total_ferramentas)}")
        print(f"  Novas:        {associadas}")
        print(f"{'='*50}")
        print(f"\n✅ Sofia está pronta para atender!")
        print(f"   Configure a API key do Anthropic em /configuracoes")
        print(f"   ou defina a variável: anthropic_api_key")
        
        return sofia
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao configurar Sofia: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    sessao_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    print(f"🏥 Configurando Sofia para sessão {sessao_id}...")
    print()
    setup_sofia(sessao_id)
