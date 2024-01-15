# Doodba Escodoo Extra

Abra o terminal shell e dentro da pasta do projeto Doodba execute o processo abaixo

## Iniciando ambiente de desenvolvimento
```
invoke develop
```

## Adicionando Tarefas Escodoo
```
wget -O escodoo.py https://github.com/Escodoo/doodba-escodoo-extra/blob/e799334c71be1fbd6fe4e406fea0fe98150aada5/escodoo.py
```

## Preparando Ambiente

```
INVOKE_VENV_PATH=$(pipx environment --value PIPX_LOCAL_VENVS)
source "$INVOKE_VENV_PATH"/invoke/bin/activate
python -m pip install requests
deactivate
```

## Tarefas Escodoo e Preparação da Base

### Listando as ações disponíveis:
```
invoke --collection=escodoo --list 
```

### Atualizando arquivos do projeto (addons.yaml, repos.yaml, pip.txt and others)
```
invoke --collection=escodoo overwrite-project-files --github-url=https://github.com/escodoo/doodba-escodoo-setup-br
```

### Criando e preparando a base de dados Escodoo
```
invoke --collection=escodoo preparedb-escodoo --dbname=devel_br --createdb
```

## Iniciando Ambiente e Acessando o Odoo
```
invoke git-aggregate
invoke img-build
invoke start
```

Abra o navegador e acesse `http://localhost:14069` (se for Odoo 16.0 acesse pela por 16069) e selecione a base de dados que foi criada anteriormente caso tenha passado o parametro --dbname na tarefa preparedb-escodoo.
