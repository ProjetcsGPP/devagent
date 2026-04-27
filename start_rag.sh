#!/bin/bash

cd ~/workspace || exit 1

echo "Ativando ambiente virtual..."
source rag/venv/bin/activate

if [ $? -ne 0 ]; then
    echo "Erro ao ativar o ambiente virtual."
    exit 1
fi

echo "Verificando Ollama..."

if ! pgrep -x "ollama" >/dev/null; then
    echo "Iniciando Ollama..."
    nohup ollama serve >/tmp/ollama.log 2>&1 &
    sleep 5
else
    echo "Ollama já está em execução."
fi

echo
echo "Iniciando DevAgent..."
echo

python dev_agent.py