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
    poetry run cz bump --dry-run

bump-version:
    echo "Bump version, create release notes and tag version"
    poetry run cz bump --yes

bump:
    bump-dry
    bump-version

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



