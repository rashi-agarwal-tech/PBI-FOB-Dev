import typer
import yaml
from pathlib import Path
import re

app = typer.Typer()

PROJECT_DIR = Path(__file__).parent.parent
PARTITIONS_DIR = PROJECT_DIR / "partitions"
REPORT_DIR = PROJECT_DIR / "reports"

@app.command()
def swap_partitions(original: bool = True):
    set_variable("NumberOfRows", "1000" if original else "0")
    set_variable("Datasource_Server", '"drmartensdev.west-europe.azure.snowflakecomputing.com"')
    for partition_dir in PARTITIONS_DIR.iterdir():
        for table_dir in partition_dir.iterdir():
            tmdl_file = REPORT_DIR / f"{partition_dir.name}.Dataset" / "definition" / "tables" / f"{table_dir.name}.tmdl"
            line_no, tmdl_str, partitions_str = remove_partitions(tmdl_file)
            default_partition = True if len(partitions_str.split(" ")[1]) > 38 else False
            if not default_partition:
                (table_dir / "partitions.tmdl").write_text(partitions_str)
            partition_file = (table_dir / "original.tmdl") if original else (table_dir / "partitions.tmdl")
            partitions_str = partition_file.read_text()
            tmdl_final_text = add_partitions(tmdl_str, partitions_str, line_no)
            tmdl_file.write_text(tmdl_final_text)


def add_partitions(tmdl_text: str, partitions_text: str, line_no: int):
    tmdl_lines = tmdl_text.split("\n")
    partitions_lines = partitions_text.split("\n")
    if partitions_lines[0] in ('', '\n'):
        partitions_lines = partitions_lines[1:]
    final_lines = tmdl_lines[0:line_no] + partitions_lines + tmdl_lines[line_no:] 
    return "\n".join(final_lines)


def remove_partitions(file: Path):
    output = []
    partitions = []
    first_partition = []
    with open(file) as f:
        lines = f.readlines()
        found = False
        for i, l in enumerate(lines):
            if found:
                matched = re.search(r"^\t\w", l)
                if matched:
                    found = False 
            if l.startswith("\tpartition "):
                partitions.append("\n")
                first_partition.append(i)
                found = True
            if not found:
                output.append(l)
            else:
                partitions.append(l)
    partitions = remove_duplicate_blanks(partitions)
    return min(first_partition), "".join(output), "".join(partitions)


def remove_duplicate_blanks(partitions: list) -> list:
    found = False
    clean_partitions = []
    for p in partitions:
        if p == '\n' and found:
            continue
        clean_partitions.append(p)
        if p == '\n':
            found = True
        else:
            found = False
    return clean_partitions


def set_variable(variable: str, value: str):
    for f in REPORT_DIR.glob("**/expressions.tmdl"):
        tmdl = f.read_text()
        token = tmdl.split(" ")
        tmdl_out = []
        for i, t in enumerate(token):
            if i > 2 and token[i-2] == variable and token[i-1] == "=":
                tmdl_out.append(value)
            else:
                tmdl_out.append(t)
        f.write_text(" ".join(tmdl_out))
                    

if __name__ == "__main__":
    app()