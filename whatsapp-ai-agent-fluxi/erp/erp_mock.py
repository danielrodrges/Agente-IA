"""
Implementação Mock do ERP para testes e desenvolvimento.
Simula todas as operações do ERP com dados fictícios.
"""
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from erp.erp_interface import ERPInterface


class ERPMock(ERPInterface):
    """
    Implementação mock do ERP para testes.
    Usa dados em memória para simular operações.
    """

    def __init__(self):
        # Dados mock
        self._pacientes = {
            "12345678900": {
                "paciente_id": "PAC001",
                "nome": "Maria da Silva",
                "cpf": "123.456.789-00",
                "telefone": "5511999999999",
                "email": "maria@email.com",
                "data_nascimento": "1985-03-15",
                "convenio": "SUS",
                "observacoes": "",
            },
            "98765432100": {
                "paciente_id": "PAC002",
                "nome": "João Santos",
                "cpf": "987.654.321-00",
                "telefone": "5511988888888",
                "email": "joao@email.com",
                "data_nascimento": "1990-07-22",
                "convenio": "Particular",
                "observacoes": "Alérgico a dipirona",
            },
        }

        self._especialidades = [
            {"id": "ESP001", "nome": "Clínico Geral", "descricao": "Consulta clínica geral"},
            {"id": "ESP002", "nome": "Cardiologia", "descricao": "Consulta cardiológica"},
            {"id": "ESP003", "nome": "Dermatologia", "descricao": "Consulta dermatológica"},
            {"id": "ESP004", "nome": "Ginecologia", "descricao": "Consulta ginecológica"},
            {"id": "ESP005", "nome": "Oftalmologia", "descricao": "Consulta oftalmológica"},
            {"id": "ESP006", "nome": "Ortopedia", "descricao": "Consulta ortopédica"},
            {"id": "ESP007", "nome": "Pediatria", "descricao": "Consulta pediátrica"},
            {"id": "ESP008", "nome": "Urologia", "descricao": "Consulta urológica"},
        ]

        self._medicos = [
            {"id": "MED001", "nome": "Dr. Carlos Oliveira", "crm": "CRM/SP 12345", "especialidade": "Clínico Geral"},
            {"id": "MED002", "nome": "Dra. Ana Lima", "crm": "CRM/SP 23456", "especialidade": "Cardiologia"},
            {"id": "MED003", "nome": "Dr. Pedro Santos", "crm": "CRM/SP 34567", "especialidade": "Cardiologia"},
            {"id": "MED004", "nome": "Dra. Julia Costa", "crm": "CRM/SP 45678", "especialidade": "Dermatologia"},
            {"id": "MED005", "nome": "Dr. Ricardo Souza", "crm": "CRM/SP 56789", "especialidade": "Ortopedia"},
            {"id": "MED006", "nome": "Dra. Fernanda Rocha", "crm": "CRM/SP 67890", "especialidade": "Ginecologia"},
            {"id": "MED007", "nome": "Dr. Marcos Silva", "crm": "CRM/SP 78901", "especialidade": "Oftalmologia"},
            {"id": "MED008", "nome": "Dra. Patricia Alves", "crm": "CRM/SP 89012", "especialidade": "Pediatria"},
        ]

        self._exames = [
            {"id": "EXA001", "nome": "Hemograma Completo", "preparo": "Jejum de 8 horas", "valor": 35.00},
            {"id": "EXA002", "nome": "Glicemia", "preparo": "Jejum de 8 horas", "valor": 15.00},
            {"id": "EXA003", "nome": "Colesterol Total", "preparo": "Jejum de 12 horas", "valor": 25.00},
            {"id": "EXA004", "nome": "Eletrocardiograma", "preparo": "Sem preparo necessário", "valor": 80.00},
            {"id": "EXA005", "nome": "Raio-X Tórax", "preparo": "Sem preparo necessário", "valor": 60.00},
            {"id": "EXA006", "nome": "Ultrassom Abdominal", "preparo": "Jejum de 6 horas, bexiga cheia", "valor": 120.00},
            {"id": "EXA007", "nome": "TSH / T4 Livre", "preparo": "Sem preparo necessário", "valor": 45.00},
            {"id": "EXA008", "nome": "Urina Tipo I", "preparo": "Coletar primeira urina da manhã", "valor": 20.00},
        ]

        self._agendamentos: Dict[str, Dict] = {}
        self._next_agendamento_id = 1

    async def buscar_paciente(
        self, cpf: Optional[str] = None, telefone: Optional[str] = None
    ) -> Dict[str, Any]:
        # Limpar CPF
        if cpf:
            cpf_limpo = cpf.replace(".", "").replace("-", "").replace(" ", "")
            if cpf_limpo in self._pacientes:
                return {"encontrado": True, **self._pacientes[cpf_limpo]}
        
        if telefone:
            tel_limpo = telefone.replace("+", "").replace(" ", "").replace("-", "")
            for pac in self._pacientes.values():
                if pac["telefone"] == tel_limpo:
                    return {"encontrado": True, **pac}
        
        return {"encontrado": False, "mensagem": "Paciente não encontrado no sistema"}

    async def cadastrar_paciente(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        cpf_limpo = dados.get("cpf", "").replace(".", "").replace("-", "").replace(" ", "")
        pac_id = f"PAC{len(self._pacientes) + 1:03d}"
        
        paciente = {
            "paciente_id": pac_id,
            "nome": dados.get("nome", ""),
            "cpf": dados.get("cpf", ""),
            "telefone": dados.get("telefone", ""),
            "email": dados.get("email", ""),
            "data_nascimento": dados.get("data_nascimento", ""),
            "convenio": dados.get("convenio", "Particular"),
            "observacoes": dados.get("observacoes", ""),
        }
        
        self._pacientes[cpf_limpo] = paciente
        return {"sucesso": True, "paciente_id": pac_id, "mensagem": "Paciente cadastrado com sucesso"}

    async def listar_especialidades(self) -> Dict[str, Any]:
        return {"especialidades": self._especialidades}

    async def listar_medicos(self, especialidade: Optional[str] = None) -> Dict[str, Any]:
        if especialidade:
            medicos = [m for m in self._medicos if m["especialidade"].lower() == especialidade.lower()]
        else:
            medicos = self._medicos
        return {"medicos": medicos}

    async def listar_horarios_disponiveis(
        self,
        especialidade: Optional[str] = None,
        medico_id: Optional[str] = None,
        data: Optional[str] = None,
        periodo_dias: int = 7,
    ) -> Dict[str, Any]:
        horarios = []
        
        # Filtrar médicos
        medicos = self._medicos
        if especialidade:
            medicos = [m for m in medicos if m["especialidade"].lower() == especialidade.lower()]
        if medico_id:
            medicos = [m for m in medicos if m["id"] == medico_id]

        # Gerar horários disponíveis
        if data:
            try:
                data_inicio = datetime.strptime(data, "%Y-%m-%d")
            except ValueError:
                data_inicio = datetime.now() + timedelta(days=1)
        else:
            data_inicio = datetime.now() + timedelta(days=1)

        slots_hora = ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", 
                       "11:00", "13:00", "13:30", "14:00", "14:30", "15:00",
                       "15:30", "16:00", "16:30", "17:00"]

        for dia in range(periodo_dias):
            dt = data_inicio + timedelta(days=dia)
            if dt.weekday() >= 6:  # Pular domingo
                continue
            if dt.weekday() == 5:  # Sábado só até 12h
                slots_dia = [s for s in slots_hora if int(s.split(":")[0]) < 12]
            else:
                slots_dia = slots_hora

            for medico in medicos:
                # Simular alguns slots ocupados
                disponíveis = random.sample(slots_dia, min(len(slots_dia), random.randint(3, 8)))
                for slot in sorted(disponíveis):
                    horarios.append({
                        "data": dt.strftime("%Y-%m-%d"),
                        "horario": slot,
                        "medico_id": medico["id"],
                        "medico_nome": medico["nome"],
                        "especialidade": medico["especialidade"],
                        "duracao_minutos": 30,
                    })

        return {"horarios": horarios[:20]}  # Limitar a 20 resultados

    async def agendar_consulta(
        self,
        paciente_id: str,
        medico_id: str,
        data_hora: str,
        especialidade: str,
        observacoes: Optional[str] = None,
    ) -> Dict[str, Any]:
        ag_id = f"AG{self._next_agendamento_id:05d}"
        self._next_agendamento_id += 1

        medico = next((m for m in self._medicos if m["id"] == medico_id), None)
        medico_nome = medico["nome"] if medico else "Médico"

        agendamento = {
            "id": ag_id,
            "paciente_id": paciente_id,
            "medico_id": medico_id,
            "medico": medico_nome,
            "data_hora": data_hora,
            "especialidade": especialidade,
            "status": "agendado",
            "tipo": "consulta",
            "observacoes": observacoes or "",
        }
        self._agendamentos[ag_id] = agendamento

        return {
            "sucesso": True,
            "agendamento_id": ag_id,
            "data_hora": data_hora,
            "medico": medico_nome,
            "especialidade": especialidade,
            "mensagem": f"Consulta agendada com sucesso! Código: {ag_id}",
        }

    async def remarcar_consulta(
        self, agendamento_id: str, nova_data_hora: str
    ) -> Dict[str, Any]:
        if agendamento_id not in self._agendamentos:
            return {"sucesso": False, "mensagem": "Agendamento não encontrado"}

        ag = self._agendamentos[agendamento_id]
        ag["data_hora"] = nova_data_hora
        ag["status"] = "remarcado"

        return {
            "sucesso": True,
            "agendamento_id": agendamento_id,
            "nova_data_hora": nova_data_hora,
            "mensagem": f"Consulta remarcada para {nova_data_hora}",
        }

    async def cancelar_consulta(
        self, agendamento_id: str, motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        if agendamento_id not in self._agendamentos:
            return {"sucesso": False, "mensagem": "Agendamento não encontrado"}

        ag = self._agendamentos[agendamento_id]
        ag["status"] = "cancelado"

        return {
            "sucesso": True,
            "agendamento_id": agendamento_id,
            "taxa_cancelamento": 0.0,
            "mensagem": "Consulta cancelada com sucesso. Sem taxa de cancelamento.",
        }

    async def confirmar_consulta(self, agendamento_id: str) -> Dict[str, Any]:
        if agendamento_id not in self._agendamentos:
            return {"sucesso": False, "mensagem": "Agendamento não encontrado"}

        ag = self._agendamentos[agendamento_id]
        ag["status"] = "confirmado"

        return {
            "sucesso": True,
            "agendamento_id": agendamento_id,
            "status": "confirmado",
            "mensagem": "Presença confirmada!",
        }

    async def buscar_agendamentos(
        self,
        paciente_id: Optional[str] = None,
        telefone: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        agendamentos = list(self._agendamentos.values())

        if paciente_id:
            agendamentos = [a for a in agendamentos if a.get("paciente_id") == paciente_id]
        if status:
            agendamentos = [a for a in agendamentos if a.get("status") == status]

        return {"agendamentos": agendamentos}

    async def listar_exames_disponiveis(self) -> Dict[str, Any]:
        return {"exames": self._exames}

    async def agendar_exame(
        self,
        paciente_id: str,
        exame_id: str,
        data_hora: str,
        observacoes: Optional[str] = None,
    ) -> Dict[str, Any]:
        ag_id = f"EX{self._next_agendamento_id:05d}"
        self._next_agendamento_id += 1

        exame = next((e for e in self._exames if e["id"] == exame_id), None)
        
        if not exame:
            return {"sucesso": False, "mensagem": "Exame não encontrado"}

        agendamento = {
            "id": ag_id,
            "paciente_id": paciente_id,
            "exame_id": exame_id,
            "exame": exame["nome"],
            "data_hora": data_hora,
            "preparo": exame["preparo"],
            "status": "agendado",
            "tipo": "exame",
        }
        self._agendamentos[ag_id] = agendamento

        return {
            "sucesso": True,
            "agendamento_id": ag_id,
            "exame": exame["nome"],
            "data_hora": data_hora,
            "preparo": exame["preparo"],
            "mensagem": f"Exame agendado! Preparo: {exame['preparo']}",
        }

    async def buscar_orcamento(
        self, procedimentos: List[str], convenio: Optional[str] = None
    ) -> Dict[str, Any]:
        itens = []
        total = 0.0

        # Buscar em especialidades + exames
        todos_procedimentos = {e["nome"].lower(): e["valor"] for e in self._exames}
        todos_procedimentos.update({
            "consulta clínico geral": 80.00,
            "consulta cardiologia": 150.00,
            "consulta dermatologia": 120.00,
            "consulta ginecologia": 130.00,
            "consulta oftalmologia": 110.00,
            "consulta ortopedia": 140.00,
            "consulta pediatria": 100.00,
            "consulta urologia": 130.00,
        })

        for proc in procedimentos:
            proc_lower = proc.lower()
            # Busca aproximada
            valor = None
            nome_encontrado = proc
            for nome, val in todos_procedimentos.items():
                if proc_lower in nome or nome in proc_lower:
                    valor = val
                    nome_encontrado = nome.title()
                    break
            
            if valor is None:
                valor = 100.00  # Valor padrão para desconhecidos
            
            convenio_cobre = convenio and convenio.lower() != "particular"
            itens.append({
                "procedimento": nome_encontrado,
                "valor": valor,
                "convenio_cobre": convenio_cobre,
            })
            if not convenio_cobre:
                total += valor

        return {
            "itens": itens,
            "valor_total": total,
            "forma_pagamento": "Dinheiro, PIX, Cartão (débito/crédito)",
            "observacao": "Valores para particular. Consulte cobertura do convênio.",
        }

    async def obter_info_clinica(self) -> Dict[str, Any]:
        return {
            "nome": "Clínica Popular Saúde & Vida",
            "endereco": "Rua da Saúde, 123 - Centro",
            "telefone": "(11) 3333-4444",
            "horario_funcionamento": "Segunda a Sexta: 7h às 19h | Sábado: 7h às 12h",
            "convenios_aceitos": ["SUS", "Unimed", "Amil", "Bradesco Saúde", "SulAmérica"],
            "formas_pagamento": ["Dinheiro", "PIX", "Cartão de Débito", "Cartão de Crédito (até 3x)"],
        }


# Singleton para uso
erp_mock = ERPMock()
