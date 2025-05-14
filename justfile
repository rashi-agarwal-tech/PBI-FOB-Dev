default:
    @echo "Please specify a recipe to run."
    @just --list
    
test-all-cov:
    poetry run pytest -s --cov=pbi_tools --cov-report=xml --cov-report=html --junitxml=test-results.xml
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
    just fix-changelog

bump-skip-ci:
    just bump-version
    just push-tags
    just add-skip-ci "development"

git-config branch:
  echo "Fetching Target Branch: {{branch}}"
  git fetch origin {{branch}}
  git pull --rebase origin {{branch}}:{{branch}}
  echo "Set git user name and email to azuredevops"
  git config --global user.email "azuredevops@drmartens.com"
  git config --global user.name "Azure Devops PBI"
  
add-skip-ci branch:
    #!/usr/bin/env bash
    current_message=$(git log -1 --pretty=%B)
    new_message="${current_message} [skip ci]"
    echo "New commit message: ${new_message}"
    git commit --amend -m "$new_message"
    git push origin HEAD:{{ branch }} --force-with-lease

bump:
    just bump-dry
    just bump-version

last-commit origin:
  @git rev-list --reverse {{origin}}..HEAD | head -n 1

cz-check origin:
  @poetry run cz check --rev-range $(just last-commit {{origin}})..
  
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
    
files-changed branch:
    #!/usr/bin/env bash
    git fetch origin {{ branch }} > /dev/null 2>&1
    git diff --name-only {{ branch }}...HEAD > changed_files.txt
    git diff --name-only $(git merge-base HEAD HEAD~1) HEAD >> changed_files.txt
    CHANGED_FILES=$(paste -sd " " changed_files.txt)
    if [[ "$CHANGED_FILES" == *"powerbi/"* ]]; then
    echo "Power BI Report Changes Detected"
    fi
    if [[ "$CHANGED_FILES" == *"pbi_tools/"* ]]; then
    echo "Application Changes Detected"
    fi
    rm changed_files.txt
    
      
get-env branch:
    #!/usr/bin/env bash
    if [ "{{branch}}" = "development" ]; then
        echo "dev"
    elif [ "{{branch}}" = "uat" ]; then
        echo "uat"
    elif [ "{{branch}}" = "main" ]; then
        echo "prod"
    elif [ "{{branch}}" = "master" ]; then
        echo "prod"
    elif [ "{{branch}}" = "prod" ]; then
        echo "prod"
    elif [ "{{branch}}" = "production" ]; then
        echo "prod"
    else
        echo "unknown"
    fi
    
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
    poetry lock
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

fix-changelog:
    poetry run fix-changelog
