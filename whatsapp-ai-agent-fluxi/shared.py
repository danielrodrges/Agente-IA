"""
Utilitários compartilhados para templates e paths.
"""
import os
from fastapi.templating import Jinja2Templates

# Diretório base do projeto (resolve corretamente em serverless)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Instância compartilhada de templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)
