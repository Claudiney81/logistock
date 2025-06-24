#!/bin/bash

echo "Inicializando LogiStock..."

flask db upgrade
flask init-db
flask seed-dados
flask criar-usuario

echo "Tudo pronto!"
