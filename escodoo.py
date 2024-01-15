"""Escodoo child project tasks.

This file is to be executed with https://www.pyinvoke.org/ in Python 3.6+.

Contains common helpers to develop using this child project.
"""
import os
from logging import getLogger
from pathlib import Path

from invoke import exceptions, task

try:
    import yaml
except ImportError:
    from invoke.util import yaml

_logger = getLogger(__name__)

try:
    import requests
except (ImportError, IOError) as err:
    _logger.debug(err)

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
    """Overwrite local files by template remote files (spec.yaml, repos.yaml, requirements.yaml and others if exist in repo)
    """
    odoo_version = str(int(ODOO_VERSION))
    files_to_update = {
        "repos.yaml": "odoo/custom/src/repos.yaml",
        "addons.yaml": "odoo/custom/src/addons.yaml",
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
    "dbname": "The DB that will be DESTROYED and recreated. Default: 'devel'.",
    "createdb": "Create the database. Default: False",
}
)
def preparedb_escodoo(c, dbname="devel", createdb=False):
    """Prepare database Escodoo's profile
    """
    if ODOO_VERSION < 11:
        raise exceptions.PlatformError(
            "The preparedb_escodoo script is not available for Doodba environments bellow v11."
        )

    c.run("docker-compose stop odoo", pty=True)
    _run = "docker-compose run --rm -l traefik.enable=false odoo"

    with c.cd(str(PROJECT_ROOT)):

        if createdb:
            c.run(
                f"{_run} click-odoo-initdb -n {dbname} -m base",
                env=UID_ENV,
                pty=True,
            )
        c.run(
            f"{_run} -d {dbname} -i escodoo_setup_base --stop-after-init",
            env=UID_ENV,
            pty=True,
        )
        c.run(
            f"{_run} -d {dbname} -i escodoo_setup_base_br --stop-after-init",
            env=UID_ENV,
            pty=True,
        )
