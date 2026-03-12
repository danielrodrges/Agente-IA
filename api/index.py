"""
Ponto de entrada para Vercel Serverless Functions.
Importa a aplicação FastAPI do subdirectório do projeto.
"""
import os
import sys

# Adicionar o diretório do projeto ao Python path
project_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "whatsapp-ai-agent-fluxi"
)
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Importar a app FastAPI
from main import app

# Vercel espera o handler como 'app' ou 'handler'
handler = app
