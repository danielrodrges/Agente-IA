"""
Parser de CURL para extrair componentes de um comando curl.
Converte CURL → Dict e Dict → CURL
"""
import re
import json
from typing import Dict, Any, Optional


class CurlParser:
    """Parser e builder de comandos CURL."""
    
    @staticmethod
    def parse_curl(curl_command: str) -> Dict[str, Any]:
        """
        Converte comando CURL em dicionário.
        Suporta: JSON, form-data, urlencoded, basic auth, bearer, múltiplos headers.
        """
        result = {
            "method": "GET",
            "url": "",
            "headers": {},
            "query_params": {},
            "body": None,
            "body_type": "json",
            "auth": None
        }
        
        # Limpar comando
        curl_command = curl_command.strip()
        if curl_command.startswith('curl'):
            curl_command = curl_command[4:].strip()
        
        # Remover quebras de linha e \ extras (preserva JSON)
        curl_command = re.sub(r'\\\s*\n\s*(?![\{\[])', ' ', curl_command)
        
        # Extrair método (-X ou --request)
        method_match = re.search(r'(?:-X|--request)\s+([A-Z]+)', curl_command, re.IGNORECASE)
        if method_match:
            result["method"] = method_match.group(1).upper()
        else:
            # Se não tem método explícito mas tem body, assume POST
            has_body = re.search(r'(?:-d|--data|--data-raw|--data-binary|-F|--form)\s+', curl_command)
            if has_body:
                result["method"] = "POST"
        
        # Extrair autenticação básica (-u ou --user)
        auth_match = re.search(r'(?:-u|--user)\s+["\']?([^"\'\\s]+)["\']?', curl_command)
        if auth_match:
            auth_str = auth_match.group(1)
            result["auth"] = {"type": "basic", "credentials": auth_str}
            # Adicionar header Authorization
            import base64
            encoded = base64.b64encode(auth_str.encode()).decode()
            result["headers"]["Authorization"] = f"Basic {encoded}"
        
        # Extrair URL (primeira string https?://)
        url_match = re.search(r'(https?://[^\s"\']+)', curl_command)
        if url_match:
            full_url = url_match.group(1).strip("'\"")
            # Separar URL de query params
            if '?' in full_url:
                base_url, query_string = full_url.split('?', 1)
                result["url"] = base_url
                # Parse query params (decode URL)
                from urllib.parse import unquote
                for param in query_string.split('&'):
                    if '=' in param:
                        key, value = param.split('=', 1)
                        result["query_params"][key] = unquote(value)
            else:
                result["url"] = full_url
        
        # Extrair headers (-H ou --header) - suporta múltiplos
        header_pattern = r'(?:-H|--header)\s+["\']([^"\']+)["\']'
        for match in re.finditer(header_pattern, curl_command):
            header = match.group(1)
            if ':' in header:
                key, value = header.split(':', 1)
                result["headers"][key.strip()] = value.strip()
        
        # Extrair body (-d, --data, --data-raw, --data-binary)
        # Suporta JSON multilinha
        body_pattern = r'(?:-d|--data|--data-raw|--data-binary)\s+(["\'])(.+?)\1'
        body_match = re.search(body_pattern, curl_command, re.DOTALL)
        if body_match:
            body = body_match.group(2)
            # Limpar espaços extras mas preservar estrutura JSON
            body = body.strip()
            result["body"] = body
            
            # Detectar tipo do body
            try:
                json.loads(body)
                result["body_type"] = "json"
            except:
                if '&' in body and '=' in body and '{' not in body:
                    result["body_type"] = "x-www-form-urlencoded"
                else:
                    result["body_type"] = "raw"
        
        # Extrair múltiplos -d (urlencoded)
        if not body_match:
            urlencoded_pattern = r'-d\s+"?([^"\s]+)"?'
            urlencoded_matches = re.findall(urlencoded_pattern, curl_command)
            if urlencoded_matches:
                result["body"] = '&'.join(urlencoded_matches)
                result["body_type"] = "x-www-form-urlencoded"
        
        # Extrair form data (-F ou --form) - suporta upload
        form_pattern = r'(?:-F|--form)\s+["\']([^"\']+)["\']'
        form_matches = re.findall(form_pattern, curl_command)
        if form_matches:
            result["body_type"] = "form-data"
            form_data = {}
            for form_field in form_matches:
                if '=' in form_field:
                    key, value = form_field.split('=', 1)
                    # Detectar upload de arquivo (@)
                    if value.startswith('@'):
                        form_data[key] = {"type": "file", "path": value[1:]}
                    else:
                        form_data[key] = value
            result["body"] = json.dumps(form_data)
        
        return result
    
    @staticmethod
    def dict_to_curl(data: Dict[str, Any]) -> str:
        """
        Converte dicionário em comando CURL.
        
        Exemplo:
        {
            "method": "POST",
            "url": "https://api.com/users",
            "headers": {"Authorization": "Bearer token"},
            "body": '{"name": "João"}'
        }
        
        Retorna:
        curl -X POST https://api.com/users \
          -H "Authorization: Bearer token" \
          -d '{"name": "João"}'
        """
        parts = ["curl"]
        
        # Método
        method = data.get("method", "GET")
        if method != "GET":
            parts.append(f"-X {method}")
        
        # URL com query params
        url = data.get("url", "")
        query_params = data.get("query_params", {})
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            url = f"{url}?{query_string}"
        parts.append(f'"{url}"')
        
        # Headers
        headers = data.get("headers", {})
        for key, value in headers.items():
            parts.append(f'-H "{key}: {value}"')
        
        # Body
        body = data.get("body")
        if body:
            body_type = data.get("body_type", "json")
            if body_type == "form-data":
                # Parse JSON body para form fields
                try:
                    body_dict = json.loads(body) if isinstance(body, str) else body
                    for key, value in body_dict.items():
                        parts.append(f'-F "{key}={value}"')
                except:
                    parts.append(f'-d \'{body}\'')
            else:
                # JSON ou raw
                parts.append(f'-d \'{body}\'')
        
        return " \\\n  ".join(parts)
    
    @staticmethod
    def extract_variables(text: str) -> list:
        """
        Extrai todas as variáveis {variavel} de um texto.
        
        Retorna lista de variáveis encontradas.
        """
        pattern = r'\{([^}]+)\}'
        return list(set(re.findall(pattern, text)))
    
    @staticmethod
    def validate_curl(curl_command: str) -> tuple[bool, str]:
        """
        Valida se um comando CURL é válido.
        
        Retorna (is_valid, error_message)
        """
        if not curl_command.strip():
            return False, "Comando CURL vazio"
        
        # Deve começar com curl
        if not curl_command.strip().startswith('curl'):
            return False, "Comando deve começar com 'curl'"
        
        # Deve ter uma URL
        if not re.search(r'https?://', curl_command):
            return False, "URL não encontrada"
        
        return True, ""


# Exemplo de uso
if __name__ == "__main__":
    # Teste parse
    curl = """
    curl -X POST https://api.example.com/users?page=1 \
      -H "Authorization: Bearer {var.API_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"name": "{nome}", "email": "{email}"}'
    """
    
    parsed = CurlParser.parse_curl(curl)
    print("Parsed:", json.dumps(parsed, indent=2))
    
    # Teste dict to curl
    rebuilt = CurlParser.dict_to_curl(parsed)
    print("\nRebuilt CURL:")
    print(rebuilt)
    
    # Teste extract variables
    variables = CurlParser.extract_variables(curl)
    print("\nVariables found:", variables)
