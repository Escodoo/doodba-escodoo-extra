"""Escodoo child project tasks.

This file is to be executed with https://www.pyinvoke.org/ in Python 3.6+.
Contains common helpers to develop using this child project.
"""
import os
import subprocess
import sys
from datetime import datetime
from logging import getLogger
from pathlib import Path

from invoke import exceptions, task

try:
    import yaml
except ImportError:
    from invoke.util import yaml

_logger = getLogger(__name__)


def get_invoke_venv_path():
    """Gets the path of invoke's virtual environment managed by pipx."""
    try:
        result = subprocess.run(
            ["pipx", "environment", "--value", "PIPX_LOCAL_VENVS"],
            capture_output=True, text=True, check=True
        )
        pipx_venv_root = Path(result.stdout.strip())
        invoke_venv_path = pipx_venv_root / "invoke" / "bin"
        return invoke_venv_path
    except subprocess.CalledProcessError:
        print("Could not obtain the path of invoke's virtual environment.")
        return None


def install_package_in_venv(venv_path, package):
    """Installs a package in the specified virtual environment."""
    python_executable = venv_path / "python"
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
        import requests  # Tries to import again after installation
    else:
        print("Invoke virtual environment path not found.")
        sys.exit(1)

PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_PATH = PROJECT_ROOT / "odoo" / "custom" / "src"
UID_ENV = {
    "GID": os.environ.get("DOODBA_GID", str(os.getgid())),
    "UID": os.environ.get("DOODBA_UID", str(os.getuid())),
    "DOODBA_UMASK": os.environ.get("DOODBA_UMASK", "27"),
    "DOODBA_GITAGGREGATE_GID": os.environ.get("DOODBA_GITAGGREGATE_GID", ""),
    "DOODBA_GITAGGREGATE_UID": os.environ.get("DOODBA_GITAGGREGATE_UID", ""),
}
UID_ENV["DOODBA_GITAGGREGATE_GID"] = UID_ENV.get("DOODBA_GITAGGREGATE_GID", UID_ENV["GID"])
UID_ENV["DOODBA_GITAGGREGATE_UID"] = UID_ENV.get("DOODBA_GITAGGREGATE_UID", UID_ENV["UID"])
SERVICES_WAIT_TIME = int(os.environ.get("SERVICES_WAIT_TIME", 4))
ODOO_VERSION = float(
    yaml.safe_load((PROJECT_ROOT / "common.yaml").read_text())["services"]["odoo"][
        "build"
    ]["args"]["ODOO_VERSION"]
)


def transform_github_url_to_raw_url(github_url, branch, path):
    """Transforms a GitHub URL to a raw content URL."""
    parts = github_url.split("/")
    user_or_org, repo = parts[3], parts[4]
    raw_url = f"https://raw.githubusercontent.com/{user_or_org}/{repo}/{branch}/{path}"
    return raw_url


def download_file(url):
    """Downloads content from a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException:
        return None


@task(help={"github_url": "URL of the GitHub repository. Default: "
                          "https://github.com/Escodoo/doodba-escodoo-setup-br"})
def get_template_files(c, github_url="https://github.com/Escodoo/doodba-escodoo-setup-br"):
    """Get remote template files (addons.yaml, repos.yaml, pip.txt and others) for Odoo setup.

    This task downloads and updates local configuration files
    with the versions from the specified GitHub repository. It's essential for
    setting up Odoo with the necessary dependencies and custom configurations.
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
        if content:
            local_path = PROJECT_ROOT / file_path
            with open(local_path, 'w') as file:
                file.write(content)
            print(f"File updated: {file_name}")

    print("Files update completed.")


@task(help={
    "dbname": "Database name to be DESTROYED and recreated. Default: 'devel'.",
    "init_modules": "Modules to install during database initialization (comma-separated). Default: 'escodoo_setup_base'.",
    "extra_modules": "Extra modules to install after initial setup (comma-separated). Default: 'escodoo_setup_base_br'. Specify --extra_modules='' to skip.",
    "language": "Language code for database initialization (e.g., 'pt_BR', 'en_US'). "
                "Defaults to the system's Odoo language or 'load_language' in odoo.conf.",
    "demo": "Use demo to install demo data, overwriting the environment's definition.",
    "no_demo": "Use no-demo to exclude demo data, overwriting the environment's definition.",
})
def prepare_db(c, dbname="devel", demo=False, no_demo=False,
               init_modules='escodoo_setup_base', extra_modules='escodoo_setup_base_br',
               language=None):
    """
    Prepares the Escodoo database in multiple steps.

    Sets up an Odoo database for Escodoo by installing specified modules during
    database initialization. Optionally, additional modules are installed in a
    subsequent step if provided. Utilizes docker-compose for managing Odoo containers
    and performs database operations like dropping and installing databases.
    """
    if ODOO_VERSION < 11:
        raise exceptions.PlatformError(
            "Prepare_db script not available for Doodba below v11."
        )
    c.run("docker-compose stop odoo", pty=True)
    _run = "docker-compose run --rm -l traefik.enable=false odoo"

    with c.cd(str(PROJECT_ROOT)):
        demo_param = "--without-demo=ALL" if no_demo else "--without-demo=False" if demo else ""
        language_param = f"--load-language={language}" if language else ""

        # Drop the database if it exists
        c.run(f"docker-compose run --rm odoo click-odoo-dropdb --if-exists {dbname}", env=UID_ENV, warn=True, pty=True)

        # Initialize the database with initial modules
        c.run(f"{_run} -d {dbname} -i {init_modules} {demo_param} {language_param} --stop-after-init",
              env=UID_ENV, pty=True)

        # Install extra modules after initial setup, if specified and not empty
        if extra_modules.strip():
            c.run(f"{_run} -d {dbname} -i {extra_modules} --stop-after-init",
                  env=UID_ENV, pty=True)
            print(f"Extra modules installed: {extra_modules}")
        else:
            print("No extra modules specified for installation.")

        print(f"Database {dbname} prepared with initial modules.")


@task(help={
    "branch": "GitHub repository branch. Default: 'main'.",
    "repo_url": "URL of the GitHub repository. Default: 'https://github.com/Escodoo/doodba-escodoo-extra'.",
    "collection_name": "Name of the invoke collection. Default: 'escodoo'."
})
def update(c, branch="main", repo_url="https://github.com/Escodoo/doodba-escodoo-extra", collection_name="escodoo"):
    """
    Updates the specified invoke collection to the latest version from the given GitHub repository branch.

    This task fetches the latest version of the invoke collection scripts,
    ensuring that the local setup remains aligned with the latest developments and best practices.
    It also creates a backup of the current scripts with a timestamp, before performing the update,
    to safeguard against any potential issues that might arise from the update.
    """
    script_url = transform_github_url_to_raw_url(repo_url, branch, f"{collection_name}.py")
    new_script_content = download_file(script_url)
    if new_script_content:
        script_path = PROJECT_ROOT / f"{collection_name}.py"

        # Read current script content
        with open(script_path, 'r') as file:
            current_script_content = file.read()

        # Check if the content is the same
        if current_script_content == new_script_content:
            print(f"The {collection_name}.py script is already up to date.")
            return

        # If content is different, backup the current script
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_script_path = PROJECT_ROOT / f"{collection_name}.{timestamp}.py"
        os.rename(script_path, backup_script_path)
        print(f"Backup of the current script saved as: {backup_script_path}")

        # Update the script with the new content
        with open(script_path, 'w') as file:
            file.write(new_script_content)
        print(f"The {collection_name}.py script has been updated to the latest version.")

        # Instructions to delete the backup file
        print("\nTo delete the backup file:")
        print(f"Linux/Mac: rm {backup_script_path}")
        print(f"Windows: del {backup_script_path}")
    else:
        print("Failed to update. Please check the URL or your internet connection.")
