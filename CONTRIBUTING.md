# Contribute

Getting Started.

pre-commits
    ruff
    commitizen
    mypi???

Conventional Commits:

Pipeline:

Package Management:
    Poetry:
        Installation.


Build:



Scripts:
    Just:
        Installation:
        `pipx install rust-just`

    Poetry:
        CLI is run with click and a poetry script.

Python Version:
    .python-version file is used to specify the python version.

Secrets:
    Currently we are using environmental variables, these are loaded from a .env file in the route directory. The file should contain the following.
    
```type=ini
client_id=
client_secret=
api_username=
api_password=
```