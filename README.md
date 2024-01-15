# doodba-escodoo-extra

# Adicionando Tarefas Escodoo
```
wget -O escodoo.py 'https://raw.githubusercontent.com/Escodoo/doodba-escodoo-extra/main/escodoo.py?token=GHSAT0AAAAAACF2PHAN4732ULZOQQQ3EEVYZNFLH5A'
```

# Preparando Ambiente

```
INVOKE_VENV_PATH=$(pipx environment --value PIPX_LOCAL_VENVS)
source "$INVOKE_VENV_PATH"/invoke/bin/activate
python -m pip install requests
deactivate
```

# Tarefas Escodoo e Preparação da Base

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
