default:
    @echo "Please specify a recipe to run."
    @just --list

test-all:
    poetry run pytest -s

test-all-multi:
    poetry run pytest -s -n auto

test-quick:
    poetry run pytest -n auto -m "not api"

pbi-version:
    poetry run cz version -p

bump-dry:
    echo "Dry run bump version, create release notes and tag version"
    poetry run cz bump --dry-run --yes

bump-version:
    echo "Bump version, create release notes and tag version"
    poetry run cz bump --yes

bump-skip-ci:
    just bump-version
    just push-tags
    just add-skip-ci


add-skip-ci:
    #!/usr/bin/env bash
    current_message=$(git log -1 --pretty=%B)
    new_message="${current_message} [skip ci]"
    echo "New commit message: ${new_message}"
    git commit --amend -m "$new_message"
    git push origin HEAD:development --force-with-lease

bump:
    just bump-dry
    just bump-version

push-tag branch:
    #!/usr/bin/env bash
    GIT_TAG=$(git describe --abbrev=0)
    echo "Pushing git tag ${GIT_TAG}..."
    git push origin $GIT_TAG

bump-push:
    bump
    push-tag

list-tags:
    git tag

push-tags:
    git push --tags

push-all branch:
    git push --atomic origin {{branch}} tag --all

update-pip:
    echo "Updating pip..."
    python -m pip install --upgrade pip
    pip install poetry

install-poetry:
    just update-pip
    echo "Install poetry virtual environment and dependencies with dev"
    poetry install --sync --no-interaction --with dev

install-poetry-no-dev:
    just update-pip
    echo "Install poetry virtual environment and dependencies without dev"
    poetry install --sync --no-interaction --without dev
    
check-ruff:
    poetry run ruff check .

run-pre-commits:
    pre-commit run --all-files

check-commit num:
    poetry run cz check --rev-range HEAD~{{num}}..HEAD

install-commitizen:
    pre-commit install --hook-type commit-msg --hook-type pre-push

local-deploy:
    git commit -v -a --no-edit --amend
    git commit -v -a --no-edit --amend
    poetry build
    cp dist/pbi_tools-0.1.0-py3-none-any.whl ../windermere_airflow/dist/




