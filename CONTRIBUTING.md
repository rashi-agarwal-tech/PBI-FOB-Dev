# Contributing to Power BI Datasets

Thank you for considering contributing to Dr Marten's Power BI datasets repository! This document outlines the process for contributing to this project.

## Getting Started

### Prerequisites

- Python 3.x (see `.python-version` file for the specific version)
- [Poetry](https://python-poetry.org/) for dependency management
- [Just](https://github.com/casey/just) for running development scripts
- [Pre-commit](https://pre-commit.com/) for code quality checks

### Setup Development Environment

1. Clone the repository
2. Install Poetry (if not already installed):

   ```bash
   pipx install poetry
   ```

3. Install Just (if not already installed):

   ```bash
   pipx install rust-just
   ```

4. Set up the development environment:

   ```bash
   just install-poetry
   ```

5. Set up pre-commit hooks:

   ```bash
   just install-commitizen
   pre-commit install
   ```

### Secrets Configuration

Create a `.env` file in the root directory with the following structure:

```ini
client_id=
client_secret=
api_username=
api_password=
```

## Development Workflow

### Code Quality Tools

We use the following tools to maintain code quality:

- **Ruff**: For linting and code formatting
- **Commitizen**: For standardized commit messages
- **mypy**: For static type checking

### Running Tests

```bash
# Run all tests
just test-all

# Run tests in parallel
just test-all-multi

# Run quick tests (skipping API tests)
just test-quick
```

### Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages. This helps with generating changelogs and versioning.

Example commit format:

Common types:

- **feat**: A new feature
- **fix**: A bug fix
- **docs**: Documentation changes
- **style**: Changes that do not affect the meaning of the code
- **refactor**: Code changes that neither fix a bug nor add a feature
- **test**: Adding or modifying tests
- **chore**: Changes to the build process or auxiliary tools

You can check your commits using:

```bash
just check-commit <number-of-commits>
```

### Versioning

We use semantic versioning managed through Commitizen:

# Dry run version bump

just bump-dry

# Bump version

just bump-version

# Bump version and skip CI

just bump-skip-ci

## Power BI Development

### Multi-Partition Management

When working with multi-partition models:

1. Place single partition files in the appropriate subdirectory under `partitions/`
2. Use the CLI tool to swap partitions in and out during development

### Deployment Process

1. Make changes in the repository
2. Create a pull request to the `development` branch
3. After merging, sync changes to the Power BI development workspace using the Source Control feature
4. Use the deployment pipeline to promote changes to higher environments

## Azure DevOps Pipeline

Our CI/CD process is managed through Azure DevOps pipelines:

### Pipeline Structure

- The pipeline is triggered on pushes to the main branch and pull requests
- It performs the following stages:
  - Build: Validates code, runs linting and tests
  - Deploy: Handles deployment to appropriate environments

### Deployment Pipeline

The deployment pipeline follows these steps:

1. Changes merged to the `development` branch in Azure repository [windermere_powerbi](https://projectreboot.visualstudio.com/Windermere%20Discovery/_git/windermere_powerbi/pullrequests)
2. Manual sync is performed to the [D&A Dev - Dr. Martens Datasets](https://app.powerbi.com/groups/e8649e55-b7f9-42aa-91f7-326ed4c8a36d/list?experience=power-bi) workspace
3. Deployment to higher environments is done through the Power BI deployment pipeline [Dr Marten's Datasets DP](https://app.powerbi.com/pipelines/37cfd15a-6d60-4fd6-ba6d-86fd1a042d8d?experience=power-bi)

### CI Skip

If you need to skip CI for a commit (e.g., for documentation-only changes), you can use:

```bash
just add-skip-ci
```

This will amend your last commit message to include `[skip ci]`.

## Submitting Changes

1. Create a new branch for your changes
   - Branch names should include ticket numbers when applicable
2. Make your changes following the project's code style
3. Run tests to ensure no regressions
4. Submit a pull request with a clear description of the changes
5. Ensure all CI checks pass

## Changelog Management

Our CHANGELOG.md is maintained through the CI/CD process and follows the conventional commits format. Each release includes:

- Feature additions
- Bug fixes
- Refactoring changes
- Documentation updates

Each entry is linked to the relevant ticket in Jira and includes the commit hash for reference.

## Additional Resources

Please refer to README.md for more detailed information on:

- Repository structure
- Power BI workspaces
- Deployment notes
- Report formatting guidelines

