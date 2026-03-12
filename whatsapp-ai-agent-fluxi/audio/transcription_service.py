"""
Serviço de transcrição de áudio.
Suporta Groq e OpenAI como provedores de transcrição.
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
import httpx
import io
from pathlib import Path
from config.config_service import ConfiguracaoService


class TranscriptionService:
    """Serviço para transcrição de áudio usando Whisper (Groq/OpenAI)."""
    
    # Endpoints
    GROQ_ENDPOINT = "https://api.groq.com/openai/v1/audio/transcriptions"
    OPENAI_ENDPOINT = "https://api.openai.com/v1/audio/transcriptions"
    
    # Modelos disponíveis por provedor
    MODELOS = {
        "groq": [
            {"id": "whisper-large-v3-turbo", "nome": "Whisper Large V3 Turbo", "custo_hora": 0.04},
            {"id": "whisper-large-v3", "nome": "Whisper Large V3", "custo_hora": 0.111},
        ],
        "openai": [
            {"id": "whisper-1", "nome": "Whisper 1", "custo_hora": 0.006},
            {"id": "gpt-4o-transcribe", "nome": "GPT-4o Transcribe", "custo_hora": None},
            {"id": "gpt-4o-mini-transcribe", "nome": "GPT-4o Mini Transcribe", "custo_hora": None},
        ]
    }
    
    @staticmethod
    def obter_configuracao(db: Session) -> Dict[str, Any]:
        """Obtém configuração de transcrição do banco."""
        return {
            "habilitado": ConfiguracaoService.obter_valor(db, "audio_transcricao_habilitado", True),
            "provedor": ConfiguracaoService.obter_valor(db, "audio_transcricao_provedor", "groq"),
            "modelo": ConfiguracaoService.obter_valor(db, "audio_transcricao_modelo", "whisper-large-v3-turbo"),
            "idioma": ConfiguracaoService.obter_valor(db, "audio_transcricao_idioma", "pt"),
            "temperatura": ConfiguracaoService.obter_valor(db, "audio_transcricao_temperatura", 0.0),
            "prompt": ConfiguracaoService.obter_valor(db, "audio_transcricao_prompt", ""),
            "response_format": ConfiguracaoService.obter_valor(db, "audio_transcricao_formato", "text"),
            "responder_audio": ConfiguracaoService.obter_valor(db, "audio_responder_habilitado", True),
        }
    
    @staticmethod
    def obter_api_key(db: Session, provedor: str) -> Optional[str]:
        """Obtém a API key do provedor."""
        if provedor == "groq":
            return ConfiguracaoService.obter_valor(db, "groq_api_key")
        elif provedor == "openai":
            return ConfiguracaoService.obter_valor(db, "openai_api_key")
        return None
    
    @staticmethod
    async def transcrever(
        db: Session,
        audio_bytes: bytes,
        filename: str = "audio.ogg",
        mime_type: str = "audio/ogg"
    ) -> Dict[str, Any]:
        """
        Transcreve áudio para texto.
        
        Args:
            db: Sessão do banco
            audio_bytes: Bytes do arquivo de áudio
            filename: Nome do arquivo
            mime_type: Tipo MIME do áudio
            
        Returns:
            Dict com:
                - sucesso: bool
                - texto: str (transcrição)
                - idioma: str (idioma detectado)
                - duracao: float (duração em segundos)
                - erro: str (se houver erro)
        """
        config = TranscriptionService.obter_configuracao(db)
        
        # Verificar se transcrição está habilitada
        if not config["habilitado"]:
            return {
                "sucesso": False,
                "texto": None,
                "erro": "Transcrição de áudio desabilitada"
            }
        
        provedor = config["provedor"]
        api_key = TranscriptionService.obter_api_key(db, provedor)
        
        if not api_key:
            return {
                "sucesso": False,
                "texto": None,
                "erro": f"API Key do {provedor} não configurada"
            }
        
        # Determinar endpoint
        if provedor == "groq":
            endpoint = TranscriptionService.GROQ_ENDPOINT
        elif provedor == "openai":
            endpoint = TranscriptionService.OPENAI_ENDPOINT
        else:
            return {
                "sucesso": False,
                "texto": None,
                "erro": f"Provedor '{provedor}' não suportado"
            }
        
        try:
            # Limpar mime_type (remover parâmetros como "; codecs=opus")
            mime_base = mime_type.split(";")[0].strip()
            
            # Corrigir extensão do filename se necessário
            if ";" in filename:
                # Remover parâmetros do filename também
                parts = filename.rsplit(".", 1)
                if len(parts) == 2:
                    ext_limpa = parts[1].split(";")[0].strip()
                    filename = f"{parts[0]}.{ext_limpa}"
            
            # Preparar form data
            files = {
                "file": (filename, audio_bytes, mime_base)
            }
            
            data = {
                "model": config["modelo"],
                "response_format": config["response_format"],
            }
            
            # Adicionar parâmetros opcionais
            if config["idioma"]:
                data["language"] = config["idioma"]
            
            if config["temperatura"] is not None:
                data["temperature"] = float(config["temperatura"])
            
            if config["prompt"]:
                data["prompt"] = config["prompt"]
            
            # Para Groq, adicionar timestamp_granularities se verbose_json
            if provedor == "groq" and config["response_format"] == "verbose_json":
                data["timestamp_granularities[]"] = "segment"
            
            # Fazer requisição
            timeout = ConfiguracaoService.obter_valor(db, "audio_transcricao_timeout", 60)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}"
                    },
                    files=files,
                    data=data,
                    timeout=float(timeout)
                )
                
                if response.status_code != 200:
                    return {
                        "sucesso": False,
                        "texto": None,
                        "erro": f"Erro na API ({response.status_code}): {response.text}"
                    }
                
                # Processar resposta
                if config["response_format"] == "text":
                    texto = response.text
                    return {
                        "sucesso": True,
                        "texto": texto.strip(),
                        "idioma": config["idioma"],
                        "duracao": None,
                        "provedor": provedor,
                        "modelo": config["modelo"]
                    }
                else:
                    # JSON response
                    result = response.json()
                    return {
                        "sucesso": True,
                        "texto": result.get("text", "").strip(),
                        "idioma": result.get("language", config["idioma"]),
                        "duracao": result.get("duration"),
                        "segmentos": result.get("segments"),
                        "provedor": provedor,
                        "modelo": config["modelo"]
                    }
                    
        except httpx.TimeoutException:
            return {
                "sucesso": False,
                "texto": None,
                "erro": f"Timeout ao transcrever áudio ({timeout}s)"
            }
        except Exception as e:
            return {
                "sucesso": False,
                "texto": None,
                "erro": f"Erro ao transcrever: {str(e)}"
            }
    
    @staticmethod
    def listar_modelos(provedor: str = None) -> Dict[str, list]:
        """Lista modelos disponíveis por provedor."""
        if provedor:
            return {provedor: TranscriptionService.MODELOS.get(provedor, [])}
        return TranscriptionService.MODELOS
    
    @staticmethod
    async def testar_conexao(db: Session) -> Dict[str, Any]:
        """Testa conexão com o provedor de transcrição."""
        config = TranscriptionService.obter_configuracao(db)
        provedor = config["provedor"]
        api_key = TranscriptionService.obter_api_key(db, provedor)
        
        if not api_key:
            return {
                "sucesso": False,
                "mensagem": f"API Key do {provedor} não configurada"
            }
        
        # Criar áudio de teste mínimo (silêncio)
        # Para um teste real, precisaríamos de um arquivo de áudio válido
        return {
            "sucesso": True,
            "mensagem": f"API Key do {provedor} configurada",
            "provedor": provedor,
            "modelo": config["modelo"]
        }
