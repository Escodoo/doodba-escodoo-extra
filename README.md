# Doodba Escodoo Extra

## Baxiando a Invoke Collection
Partindo do princípio que seu projeto Doodba está disponível, abra o terminal shell e, dentro da pasta do projeto Doodba, execute o processo abaixo para baixar o script `escodoo.py`:

```
wget -O escodoo.py https://raw.githubusercontent.com/Escodoo/doodba-escodoo-extra/main/escodoo.py
```

## Tarefas da Collection

Para listar todas as tarefas disponíveis na coleção escodoo, utilize o comando:

```
invoke --collection=escodoo --list 
```

### Tarefa: get_template_files

Propósito: Baixa e atualiza arquivos de configuração locais para a configuração do Odoo com as versões do repositório GitHub especificado. É essencial para configurar o Odoo com as dependências necessárias e configurações personalizadas.

Uso:
```
invoke --collection=escodoo get_template_files
```

Opções:
- github_url: URL do repositório GitHub. Padrão: https://github.com/Escodoo/doodba-escodoo-setup-br.
- - force_branch: Permite forçar a branch de onde deve copiar os arquivos. Por padrão a tarefa assume a versão do Odoo

### Tarefa: prepare_db

Propósito: Prepara o banco de dados Escodoo em várias etapas. Configura um banco de dados Odoo instalando módulos especificados durante a inicialização do banco de dados. Opcionalmente, módulos adicionais são instalados em uma etapa subsequente se fornecidos. Utiliza docker-compose para gerenciar os contêineres Odoo e realizar operações no banco de dados como a exclusão e instalação de bancos de dados.

Observação: Antes de executar a preparação do banco, caso já tenha executado o comando `invoke --collection=escodoo` execute os comandos abaixo para baixar os repositórios que vão compor o projeto e fazer o build da imagem docker.

```
invoke git-aggregate
invoke img-build
```

Uso:
```
invoke --collection=escodoo prepare_db --dbname=devel_br --language=pt_BR
```

Opções:
- dbname: Nome do banco de dados a ser destruído e recriado. Padrão: 'devel'.
- init_modules: Módulos a serem instalados durante a inicialização do banco de dados (separados por vírgula). Padrão: 'escodoo_setup_base'.
- extra_modules: Módulos extras a serem instalados após a configuração inicial (separados por vírgula). Padrão: 'escodoo_setup_base_br'. Especifique --extra_modules='' para pular.
- language: Código de idioma para a inicialização do banco de dados. Padrão: idioma do sistema Odoo ou parâmetro 'load_language' em odoo.conf.
- demo: Use para instalar dados de demonstração, sobrescrevendo a definição do ambiente.
- no_demo: Use para excluir dados de demonstração, sobrescrevendo a definição do ambiente.

## Tarefa: update

Propósito: Atualiza a coleção invoke especificada para a última versão do ramo fornecido do repositório GitHub.

Esta tarefa busca a última versão dos scripts da coleção invoke, garantindo que a configuração local permaneça alinhada com os últimos desenvolvimentos e melhores práticas. Também cria um backup dos scripts atuais com um carimbo de data/hora, antes de realizar a atualização, para proteger contra quaisquer problemas potenciais que possam surgir da atualização.

Uso:
```
invoke --collection=escodoo update
```

Opções:
- branch: Ramo do repositório GitHub. Padrão: 'main'.
- repo_url: URL do repositório GitHub. Padrão: 'https://github.com/Escodoo/doodba-escodoo-extra'.
- collection_name: Nome da coleção invoke. Padrão: 'escodoo'.

Lembre-se de que você pode combinar várias opções de linha de comando para personalizar o comportamento das tarefas conforme necessário para o seu fluxo de trabalho.

## Iniciando o Ambiente
```
invoke start
```

Abra o navegador e acesse `http://localhost:14069` (se for Odoo 16.0 acesse pela por 16069) e selecione a base de dados que foi criada anteriormente caso tenha passado o parametro --dbname na tarefa preparedb-escodoo.
