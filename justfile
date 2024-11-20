default:
    @echo "Please specify a recipe to run."
    @just --list

test-all:
    pytest -n auto

test-quick:
    pytest -n auto -m "not api"

bpi-version:
    cz version -p

bump-dry:
    echo "Dry run bump version, create release notes and tag version"
    cz bump --dry-run

bump-version:
    echo "Bump version, create release notes and tag version"
    cz bump --yes

bump:
    bump-dry
    bump-version

list-tags:
    git tag

push-tags:
    git push --tags

push-all branch:
    git push --atomic origin {{branch}} tag --all

poetry-install:
    echo "Updating pip..."
    python -m pip install --upgrade pip
    echo "Install poetry virtual environment and dependencies"
    poetry install --sync --no-interaction --with dev
    
check-ruff:
    poetry run ruff check .

run-pre-commits:
    pre-commit run --all-files

check-commit num:
    cz check --rev-range HEAD~{{num}}..HEAD

install-commitizen:
    pre-commit install --hook-type commit-msg --hook-type pre-push  



