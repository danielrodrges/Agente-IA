"""
Ponto de entrada para Vercel Serverless Functions.
Exporta a aplicação FastAPI como handler serverless.
"""
import os
import sys

# Garantir que o diretório do projeto está no path
project_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Importar a app FastAPI
from main import app

# Vercel espera o handler como 'app' ou 'handler'
handler = app
