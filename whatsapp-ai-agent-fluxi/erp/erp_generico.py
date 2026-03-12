"""
Implementação genérica do ERP via HTTP/REST.
Faz requisições a endpoints configuráveis do ERP.
"""
import httpx
import json
import logging
from typing import Optional, Dict, Any, List

from erp.erp_interface import ERPInterface
from config.config_service import ConfiguracaoService

logger = logging.getLogger(__name__)


class ERPGenerico(ERPInterface):
    """
    Implementação genérica do ERP usando chamadas HTTP/REST.
    Os endpoints são configurados via painel de configurações.
    
    Configurações esperadas:
    - erp_base_url: URL base do ERP (ex: https://meu-erp.com/api)
    - erp_api_key: Chave de autenticação do ERP
    - erp_auth_type: Tipo de autenticação (bearer, basic, api_key)
    - erp_timeout: Timeout para requisições em segundos
    
    Cada endpoint específico pode ser configurado:
    - erp_endpoint_buscar_paciente: /pacientes/buscar
    - erp_endpoint_listar_horarios: /agendamentos/horarios
    - etc.
    """

    def __init__(self, db=None):
        self.db = db
        self._base_url = ""
        self._api_key = ""
        self._auth_type = "bearer"
        self._timeout = 30
        self._headers = {}

    def _carregar_config(self):
        """Carrega configurações do ERP do banco."""
        if self.db:
            self._base_url = ConfiguracaoService.obter_valor(self.db, "erp_base_url", "")
            self._api_key = ConfiguracaoService.obter_valor(self.db, "erp_api_key", "")
            self._auth_type = ConfiguracaoService.obter_valor(self.db, "erp_auth_type", "bearer")
            self._timeout = int(ConfiguracaoService.obter_valor(self.db, "erp_timeout", 30))

        # Montar headers de autenticação
        if self._auth_type == "bearer":
            self._headers = {"Authorization": f"Bearer {self._api_key}"}
        elif self._auth_type == "api_key":
            self._headers = {"X-API-Key": self._api_key}
        else:
            self._headers = {}

        self._headers["Content-Type"] = "application/json"

    async def _request(
        self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Faz requisição ao ERP."""
        self._carregar_config()
        
        if not self._base_url:
            return {"sucesso": False, "erro": "ERP não configurado. Configure erp_base_url em Configurações."}

        url = f"{self._base_url.rstrip('/')}/{endpoint.lstrip('/')}"

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                if method.upper() == "GET":
                    response = await client.get(url, headers=self._headers, params=params)
                elif method.upper() == "POST":
                    response = await client.post(url, headers=self._headers, json=data)
                elif method.upper() == "PUT":
                    response = await client.put(url, headers=self._headers, json=data)
                elif method.upper() == "DELETE":
                    response = await client.delete(url, headers=self._headers, params=params)
                else:
                    return {"sucesso": False, "erro": f"Método HTTP não suportado: {method}"}

                if response.status_code in (200, 201):
                    return response.json()
                else:
                    return {
                        "sucesso": False,
                        "erro": f"Erro do ERP: {response.status_code}",
                        "detalhes": response.text,
                    }
        except httpx.TimeoutException:
            return {"sucesso": False, "erro": "Timeout na comunicação com o ERP"}
        except Exception as e:
            logger.error(f"Erro ao comunicar com ERP: {e}")
            return {"sucesso": False, "erro": str(e)}

    def _get_endpoint(self, chave: str, padrao: str) -> str:
        """Obtém endpoint configurado ou usa o padrão."""
        if self.db:
            return ConfiguracaoService.obter_valor(self.db, f"erp_endpoint_{chave}", padrao)
        return padrao

    # --- Implementações da interface ---

    async def buscar_paciente(self, cpf=None, telefone=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("buscar_paciente", "/pacientes/buscar")
        params = {}
        if cpf:
            params["cpf"] = cpf
        if telefone:
            params["telefone"] = telefone
        return await self._request("GET", endpoint, params=params)

    async def cadastrar_paciente(self, dados: Dict[str, Any]) -> Dict[str, Any]:
        endpoint = self._get_endpoint("cadastrar_paciente", "/pacientes")
        return await self._request("POST", endpoint, data=dados)

    async def listar_especialidades(self) -> Dict[str, Any]:
        endpoint = self._get_endpoint("listar_especialidades", "/especialidades")
        return await self._request("GET", endpoint)

    async def listar_medicos(self, especialidade=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("listar_medicos", "/medicos")
        params = {}
        if especialidade:
            params["especialidade"] = especialidade
        return await self._request("GET", endpoint, params=params)

    async def listar_horarios_disponiveis(
        self, especialidade=None, medico_id=None, data=None, periodo_dias=7
    ) -> Dict[str, Any]:
        endpoint = self._get_endpoint("listar_horarios", "/agendamentos/horarios")
        params = {"periodo_dias": periodo_dias}
        if especialidade:
            params["especialidade"] = especialidade
        if medico_id:
            params["medico_id"] = medico_id
        if data:
            params["data"] = data
        return await self._request("GET", endpoint, params=params)

    async def agendar_consulta(
        self, paciente_id, medico_id, data_hora, especialidade, observacoes=None
    ) -> Dict[str, Any]:
        endpoint = self._get_endpoint("agendar_consulta", "/agendamentos/consultas")
        data = {
            "paciente_id": paciente_id,
            "medico_id": medico_id,
            "data_hora": data_hora,
            "especialidade": especialidade,
        }
        if observacoes:
            data["observacoes"] = observacoes
        return await self._request("POST", endpoint, data=data)

    async def remarcar_consulta(self, agendamento_id, nova_data_hora) -> Dict[str, Any]:
        endpoint = self._get_endpoint("remarcar_consulta", f"/agendamentos/{agendamento_id}/remarcar")
        return await self._request("PUT", endpoint, data={"nova_data_hora": nova_data_hora})

    async def cancelar_consulta(self, agendamento_id, motivo=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("cancelar_consulta", f"/agendamentos/{agendamento_id}/cancelar")
        data = {}
        if motivo:
            data["motivo"] = motivo
        return await self._request("PUT", endpoint, data=data)

    async def confirmar_consulta(self, agendamento_id) -> Dict[str, Any]:
        endpoint = self._get_endpoint("confirmar_consulta", f"/agendamentos/{agendamento_id}/confirmar")
        return await self._request("PUT", endpoint)

    async def buscar_agendamentos(self, paciente_id=None, telefone=None, status=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("buscar_agendamentos", "/agendamentos")
        params = {}
        if paciente_id:
            params["paciente_id"] = paciente_id
        if telefone:
            params["telefone"] = telefone
        if status:
            params["status"] = status
        return await self._request("GET", endpoint, params=params)

    async def listar_exames_disponiveis(self) -> Dict[str, Any]:
        endpoint = self._get_endpoint("listar_exames", "/exames")
        return await self._request("GET", endpoint)

    async def agendar_exame(self, paciente_id, exame_id, data_hora, observacoes=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("agendar_exame", "/agendamentos/exames")
        data = {
            "paciente_id": paciente_id,
            "exame_id": exame_id,
            "data_hora": data_hora,
        }
        if observacoes:
            data["observacoes"] = observacoes
        return await self._request("POST", endpoint, data=data)

    async def buscar_orcamento(self, procedimentos, convenio=None) -> Dict[str, Any]:
        endpoint = self._get_endpoint("buscar_orcamento", "/orcamentos")
        data = {"procedimentos": procedimentos}
        if convenio:
            data["convenio"] = convenio
        return await self._request("POST", endpoint, data=data)

    async def obter_info_clinica(self) -> Dict[str, Any]:
        endpoint = self._get_endpoint("info_clinica", "/clinica/info")
        return await self._request("GET", endpoint)
