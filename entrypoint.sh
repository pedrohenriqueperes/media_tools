#!/bin/bash

# Sair imediatamente se um comando falhar
set -e

# Aguardar o banco de dados estar pronto
if [ "$DB_HOST" = "db" ]; then
    echo "Aguardando o banco de dados ($DB_HOST:$DB_PORT)..."
    while ! nc -z $DB_HOST $DB_PORT; do
      sleep 0.1
    done
    echo "Banco de dados pronto!"
fi

# Executar o comando passado para o script
exec "$@"
