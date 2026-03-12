"""
Interface abstrata para integração com ERP.
Define o contrato que qualquer ERP deve implementar.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from datetime import datetime


class ERPInterface(ABC):
    """
    Interface abstrata para integração com ERP da clínica.
    Implemente esta classe para integrar com seu ERP específico.
    """

    # --- Pacientes ---

    @abstractmethod
    async def buscar_paciente(
        self, cpf: Optional[str] = None, telefone: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Busca paciente por CPF ou telefone.
        
        Returns:
            {
                "encontrado": bool,
                "paciente_id": str,
                "nome": str,
                "cpf": str,
                "telefone": str,
                "email": str,
                "data_nascimento": str,
                "convenio": str,
                "observacoes": str
            }
        """
        pass

    @abstractmethod
    async def cadastrar_paciente(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cadastra novo paciente no ERP.
        
        Args:
            dados: {"nome", "cpf", "telefone", "email", "data_nascimento", "convenio"}
            
        Returns:
            {"sucesso": bool, "paciente_id": str, "mensagem": str}
        """
        pass

    # --- Agendamento de Consultas ---

    @abstractmethod
    async def listar_especialidades(self) -> Dict[str, Any]:
        """
        Lista especialidades disponíveis na clínica.
        
        Returns:
            {
                "especialidades": [
                    {"id": str, "nome": str, "descricao": str}
                ]
            }
        """
        pass

    @abstractmethod
    async def listar_medicos(
        self, especialidade: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Lista médicos, opcionalmente filtrados por especialidade.
        
        Returns:
            {
                "medicos": [
                    {"id": str, "nome": str, "crm": str, "especialidade": str}
                ]
            }
        """
        pass

    @abstractmethod
    async def listar_horarios_disponiveis(
        self,
        especialidade: Optional[str] = None,
        medico_id: Optional[str] = None,
        data: Optional[str] = None,
        periodo_dias: int = 7,
    ) -> Dict[str, Any]:
        """
        Lista horários disponíveis para agendamento.
        
        Returns:
            {
                "horarios": [
                    {
                        "data": str,
                        "horario": str,
                        "medico_id": str,
                        "medico_nome": str,
                        "especialidade": str,
                        "duracao_minutos": int
                    }
                ]
            }
        """
        pass

    @abstractmethod
    async def agendar_consulta(
        self,
        paciente_id: str,
        medico_id: str,
        data_hora: str,
        especialidade: str,
        observacoes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Realiza agendamento de consulta.
        
        Returns:
            {
                "sucesso": bool,
                "agendamento_id": str,
                "data_hora": str,
                "medico": str,
                "especialidade": str,
                "mensagem": str
            }
        """
        pass

    @abstractmethod
    async def remarcar_consulta(
        self, agendamento_id: str, nova_data_hora: str
    ) -> Dict[str, Any]:
        """
        Remarca uma consulta existente.
        
        Returns:
            {"sucesso": bool, "agendamento_id": str, "nova_data_hora": str, "mensagem": str}
        """
        pass

    @abstractmethod
    async def cancelar_consulta(
        self, agendamento_id: str, motivo: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cancela uma consulta agendada.
        
        Returns:
            {"sucesso": bool, "agendamento_id": str, "taxa_cancelamento": float, "mensagem": str}
        """
        pass

    @abstractmethod
    async def confirmar_consulta(self, agendamento_id: str) -> Dict[str, Any]:
        """
        Confirma presença do paciente na consulta.
        
        Returns:
            {"sucesso": bool, "agendamento_id": str, "status": str, "mensagem": str}
        """
        pass

    @abstractmethod
    async def buscar_agendamentos(
        self,
        paciente_id: Optional[str] = None,
        telefone: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Busca agendamentos de um paciente.
        
        Returns:
            {
                "agendamentos": [
                    {
                        "id": str,
                        "data_hora": str,
                        "medico": str,
                        "especialidade": str,
                        "status": str,
                        "tipo": str  # consulta ou exame
                    }
                ]
            }
        """
        pass

    # --- Exames ---

    @abstractmethod
    async def listar_exames_disponiveis(self) -> Dict[str, Any]:
        """
        Lista exames disponíveis na clínica.
        
        Returns:
            {
                "exames": [
                    {"id": str, "nome": str, "preparo": str, "valor": float}
                ]
            }
        """
        pass

    @abstractmethod
    async def agendar_exame(
        self,
        paciente_id: str,
        exame_id: str,
        data_hora: str,
        observacoes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Agenda um exame.
        
        Returns:
            {"sucesso": bool, "agendamento_id": str, "exame": str, "data_hora": str, "preparo": str}
        """
        pass

    # --- Orçamento ---

    @abstractmethod
    async def buscar_orcamento(
        self, procedimentos: List[str], convenio: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Consulta valores de procedimentos.
        
        Returns:
            {
                "itens": [
                    {"procedimento": str, "valor": float, "convenio_cobre": bool}
                ],
                "valor_total": float,
                "forma_pagamento": str
            }
        """
        pass

    # --- Informações ---

    @abstractmethod
    async def obter_info_clinica(self) -> Dict[str, Any]:
        """
        Obtém informações gerais da clínica.
        
        Returns:
            {
                "nome": str,
                "endereco": str,
                "telefone": str,
                "horario_funcionamento": str,
                "convenios_aceitos": List[str],
                "formas_pagamento": List[str]
            }
        """
        pass
