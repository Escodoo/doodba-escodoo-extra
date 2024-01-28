# Escodoo Python Script for Doodba Project Management

This README provides details on the `escodoo.py` script, containing tasks for development and management of Odoo projects, executed using `invoke`.

## Downloading the Invoke Collection

Assuming your Doodba project is set up, open your shell terminal, and within your Doodba project folder, execute the following process to download the `escodoo.py` script:

```shell
wget -O escodoo.py https://raw.githubusercontent.com/Escodoo/doodba-escodoo-extra/main/escodoo.py
```

## Collection Tasks

To list all the available tasks in the escodoo collection, use the command:

```shell
invoke --collection=escodoo --list
```

## Available Tasks

### 1. set-admin-password
- **Description**: Sets or updates the ADMIN_PASSWORD in the specified Odoo environment file.
- **Arguments**:
  - `env-file-path`: Path to the Odoo environment file. Default: '.docker/odoo.env'.
- **Usage**:
  ```shell
  invoke --collection=escodoo set-admin-password
  ```

### 2. set-auth-admin-passkey-password
- **Description**: Sets or updates the AUTH_ADMIN_PASSKEY_PASSWORD in the specified Odoo environment file.
- **Arguments**:
  - `env-file-path`: Path to the Odoo environment file. Default: '.docker/odoo.env'.
- **Usage**:
  ```shell
  invoke --collection=escodoo set-auth-admin-passkey-password
  ```

### 3. set-demo-data
- **Description**: Sets the WITHOUT_DEMO variable in the Odoo environment file to False, ensuring inclusion of demo data.
- **Arguments**:
  - `env-file-path`: Path to the Odoo environment file. Default: '.docker/odoo.env'.
- **Usage**:
  ```shell
  invoke --collection=escodoo set-demo-data
  ```

### 4. get-template-files
- **Description**: Retrieves remote template files for Odoo setup, such as addons.yaml, repos.yaml, and others.
- **Arguments**:
  - `github-url`: URL of the GitHub repository. Default: 'https://github.com/Escodoo/doodba-escodoo-setup-br'.
  - `force-branch`: Force use of a specific branch instead of the Odoo version. Default: False.
- **Usage**:
  ```shell
  invoke --collection=escodoo get-template-files
  ```
- **Post get-template-files**
  ```shell
  invoke git-aggregate # if in develop environment
  invoke img-build
  ```

### 5. prepare-db
- **Description**: Prepares the Escodoo database, configuring it with specified modules and managing it via docker-compose. This involves multiple steps including database creation, module installation, and initial setup.
- **Arguments**:
  - `dbname`: Name of the database to be destroyed and recreated. Default: 'devel'.
  - `init_modules`: Modules to install during database initialization (comma-separated). Default: 'escodoo_setup_base'.
  - `post_init_modules`: Modules to install after database initialization, typically localization modules (comma-separated). Default: 'escodoo_setup_base_br'.
  - `extra_modules`: Extra modules to install after initial setup (comma-separated). Leave empty or set to None to skip.
  - `language`: Language code for database initialization (e.g., 'pt_BR', 'en_US'). Default: Odoo's system language or 'load_language' in odoo.conf.
  - `demo`: Use demo data. Overwrites the environment's definition.
  - `no_demo`: Exclude demo data. Overwrites the environment's definition.
- **Usage**:
  ```shell
  invoke --collection=escodoo prepare-db --dbname="database_name"
  ```

### 6. update
- **Description**: Updates the `escodoo` collection to the latest version from the specified GitHub repository branch.
- **Arguments**:
  - `branch`: Branch of the GitHub repository. Default: 'main'.
  - `repo-url`: URL of the GitHub repository. Default: 'https://github.com/Escodoo/doodba-escodoo-extra'.
  - `collection-name`: Name of the invoke collection. Default: 'escodoo'.
- **Usage**:
  ```shell
  invoke --collection=escodoo update
  ```

---

## General Usage

To execute a task:

1. Install Python and the `invoke` library.
2. Run the script using the `invoke` command, specifying the `escodoo` collection and the desired task, along with the necessary arguments.

---

## Support and Contributions

For support or contributions related to this script, contact the development team or contribute to the project repository.

---

This README provides a comprehensive overview of the `escodoo.py` script, including how to download it, list available tasks, and details on task execution. For more specific information on each task, refer to the source code and internal comments.
