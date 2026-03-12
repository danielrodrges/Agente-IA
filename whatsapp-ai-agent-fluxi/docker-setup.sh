#!/bin/bash

# Script para configurar o ambiente Docker do Fluxi
echo "🚀 Configurando ambiente Docker do Fluxi..."

# Criar diretório data se não existir
mkdir -p data

# Se existe fluxi.db na raiz, mover para data/
if [ -f "fluxi.db" ]; then
    echo "📦 Movendo banco de dados existente para data/"
    mv fluxi.db data/fluxi.db
    echo "✅ Banco movido com sucesso"
fi

# Criar diretórios necessários
mkdir -p uploads sessoes rags

# Definir permissões corretas (777 para garantir acesso total)
chmod -R 777 data uploads sessoes rags

echo "✅ Ambiente configurado com sucesso!"
echo "📝 Para iniciar o Docker:"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
echo ""
echo "📝 Para ver logs:"
echo "   docker-compose logs -f"
