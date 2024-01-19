"""Escodoo child project tasks.

This file is to be executed with https://www.pyinvoke.org/ in Python 3.6+.

Contains common helpers to develop using this child project.
"""
import os
import subprocess
import sys
from logging import getLogger
from pathlib import Path
from datetime import datetime

from invoke import exceptions, task

try:
    import yaml
except ImportError:
    from invoke.util import yaml

_logger = getLogger(__name__)


def get_invoke_venv_path():
    """Obtém o caminho do ambiente virtual do invoke gerenciado pelo pipx."""
    try:
        result = subprocess.run(
            ["pipx", "environment", "--value", "PIPX_LOCAL_VENVS"],
            capture_output=True,
            text=True,
            check=True
        )
        pipx_venv_root = Path(result.stdout.strip())
        invoke_venv_path = pipx_venv_root / "invoke" / "bin"
        return invoke_venv_path
    except subprocess.CalledProcessError:
        print("Não foi possível obter o caminho do ambiente virtual do invoke.")
        return None


def install_package_in_venv(venv_path, package):
    """Instala um pacote no ambiente virtual especificado."""
    python_executable = venv_path / "python"  # Caminho para o Python no ambiente virtual do invoke
    try:
        subprocess.check_call([python_executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        print(f"Failed to install {package} in the virtual environment.")


try:
    import requests
except ImportError:
    print("Installing 'requests' module in the invoke virtual environment...")
    invoke_venv_path = get_invoke_venv_path()
    if invoke_venv_path and invoke_venv_path.exists():
        install_package_in_venv(invoke_venv_path, "requests")
        import requests  # Tenta importar novamente após a instalação
    else:
        print("Invoke virtual environment path not found.")
        sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_PATH = PROJECT_ROOT / "odoo" / "custom" / "src"
UID_ENV = {
    "GID": os.environ.get("DOODBA_GID", str(os.getgid())),
    "UID": os.environ.get("DOODBA_UID", str(os.getuid())),
    "DOODBA_UMASK": os.environ.get("DOODBA_UMASK", "27"),
}
UID_ENV.update(
    {
        "DOODBA_GITAGGREGATE_GID": os.environ.get(
            "DOODBA_GITAGGREGATE_GID", UID_ENV["GID"]
        ),
        "DOODBA_GITAGGREGATE_UID": os.environ.get(
            "DOODBA_GITAGGREGATE_UID", UID_ENV["UID"]
        ),
    }
)
SERVICES_WAIT_TIME = int(os.environ.get("SERVICES_WAIT_TIME", 4))
ODOO_VERSION = float(
    yaml.safe_load((PROJECT_ROOT / "common.yaml").read_text())["services"]["odoo"][
        "build"
    ]["args"]["ODOO_VERSION"]
)


# Função para transformar a URL do GitHub para a URL do conteúdo bruto
def transform_github_url_to_raw_url(github_url, branch, path):
    parts = github_url.split("/")
    user_or_org = parts[3]
    repo = parts[4]
    raw_url = f"https://raw.githubusercontent.com/{user_or_org}/{repo}/{branch}/{path}"
    return raw_url


# Função para baixar o conteúdo de uma URL
def download_file(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


@task(help={"github_url": "URL of the GitHub repository"})
def overwrite_project_files(c, github_url):
    """Overwrite local files by template remote files (spec.yaml, repos.yaml, apt.txt, gem.txt, npm.txt, pip.txt if exist in repo)
    """
    odoo_version = str(int(ODOO_VERSION))
    files_to_update = {
        "repos.yaml": "odoo/custom/src/repos.yaml",
        "addons.yaml": "odoo/custom/src/addons.yaml",
        "apt.txt": "odoo/custom/dependencies/apt.txt",
        "gem.txt": "odoo/custom/dependencies/gem.txt",
        "npm.txt": "odoo/custom/dependencies/npm.txt",
        "pip.txt": "odoo/custom/dependencies/pip.txt",
    }

    for file_name, file_path in files_to_update.items():
        url = transform_github_url_to_raw_url(github_url, f"{odoo_version}.0", file_path)
        content = download_file(url)
        if content is not None:
            local_path = PROJECT_ROOT / file_path
            with open(local_path, 'w') as file:
                file.write(content)
            print(f"File updated: {file_name}")

    print("Update Escodoo config files is done!")


@task(help={
    "dbname": "The DB if exits that will be DESTROYED and recreated. Default: 'devel'.",
    "demo": "Use --demo to force install demo data.",
    "no_demo": "Use --no-demo to force exclude demo data.",
    "extra_modules": "Comma-separated list of extra modules to be installed in the second step (e.g., 'module1,module2,module3'). Default: ''",
    "language": "Language code to force the language for the installation (e.g., 'pt_BR', 'en_US'). If not set, defaults to 'en_US' or the language configured in odoo.conf.",
})
def preparedb_escodoo(c, dbname="devel", demo=False, no_demo=False, extra_modules='', language=None):
    """
    Prepare the Escodoo database with a specific profile in two steps.

    First, this script sets up an Odoo database for Escodoo by installing
    escodoo_setup_base with an optional specific language. Then, it installs
    escodoo_setup_base_br and any extra modules provided. It uses docker-compose
    to manage Odoo containers and performs database operations such as dropping
    and installing databases.

    Note:
        Make sure to test the script in a safe environment before applying it to production.
    """
    # Checks for Odoo version compatibility
    if ODOO_VERSION < 11:
        raise exceptions.PlatformError(
            "The preparedb_escodoo script is not available for Doodba environments below v11."
        )

    # Stops the Odoo service to prevent conflicts
    c.run("docker-compose stop odoo", pty=True)
    _run = "docker-compose run --rm -l traefik.enable=false odoo"

    with c.cd(str(PROJECT_ROOT)):
        # Determines the demo data and language parameter based on 'demo' and 'language'
        demo_param = "--without-demo=False" if demo else ""
        demo_param = "--without-demo=ALL" if no_demo else ""
        language_param = f"--load-language={language}" if language else "--load-language=en_US"

        # Drops existing database if requested
        c.run(
            f"{_run} click-odoo-dropdb {dbname}",
            env=UID_ENV,
            warn=True,
            pty=True,
        )

        # First step: Create a new database and install the escodoo_setup_base module with the specified language
        c.run(
            f"{_run} -d {dbname} -i escodoo_setup_base {demo_param} {language_param} --stop-after-init",
            env=UID_ENV,
            pty=True,
        )

        # Formats the extra modules to be included in the second installation command
        extra_modules_param = ',' + extra_modules if extra_modules else ''

        # Second step: Install escodoo_setup_base_br and any extra modules
        c.run(
            f"{_run} -d {dbname} -i escodoo_setup_base_br{extra_modules_param} --stop-after-init",
            env=UID_ENV,
            pty=True,
        )

    # TODO:
    # - Implementar forma de atualizar o arquivo escodoo.py
    # - Avaliar se o melhor é criar as bases com o click-odoo-createdb passando como parametro o odoo.conf para garantir a seleção da linguagem

    # Observações:
    # A justificativa de ter o modulo escodoo_setup_base é para que seja um padrão independente de que pais vamos implantar
    # o Odoo. Então teremos uma versão base para qq pais e um modulo como o escodoo_setup_base_br para o Brasil e podemos ter outros
    # modulos como escodoo_setup_base_ar para a Argentina, escodoo_setup_base_mx para o México, etc.


@task(help={"branch": "Branch of the GitHub repository to download the script from. Default: 'main'."})
def update_script(c, branch="main"):
    """
    Update the escodoo.py script with the latest version from the GitHub repository.
    Saves a backup copy of the current script with a timestamp before updating.
    """
    script_url = transform_github_url_to_raw_url(
        "https://github.com/Escodoo/doodba-escodoo-extra",
        branch,
        "escodoo.py"
    )
    new_script_content = download_file(script_url)
    if new_script_content is not None:
        script_path = PROJECT_ROOT / "escodoo.py"

        # Save a backup of the current script with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_script_path = PROJECT_ROOT / f"escodoo.py.{timestamp}"
        os.rename(script_path, backup_script_path)
        print(f"Backup of the current script saved as: {backup_script_path}")

        # Update the script with the new content
        with open(script_path, 'w') as file:
            file.write(new_script_content)
        print("The escodoo.py script has been updated to the latest version.")

        # Instructions to delete the backup file
        print("\nTo delete the backup file, use one of the following commands:")
        print(f"Linux/Mac: rm {backup_script_path}")
        print(f"Windows: del {backup_script_path}")
    else:
        print("Failed to update the escodoo.py script. Please check the URL or your internet connection.")

