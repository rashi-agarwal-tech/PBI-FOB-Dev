import typer
from pathlib import Path
from powerbi.utils.constants import REPORT_DIR, PARTITIONS_DIR
import re
from pprint import pp

app = typer.Typer()


@app.command()
def swap_partitions(original: bool = True):
    set_variable("NumberOfRows", "1000" if original else "0")
    set_variable(
        "Datasource_Server", '"drmartensdev.west-europe.azure.snowflakecomputing.com"'
    )
    for partition_dir in PARTITIONS_DIR.iterdir():
        for table_dir in partition_dir.iterdir():
            tmdl_file = (
                REPORT_DIR
                / f"{partition_dir.name}.Dataset"
                / "definition"
                / "tables"
                / f"{table_dir.name}.tmdl"
            )
            line_no, tmdl_str, partitions_str = remove_partitions(tmdl_file)
            default_partition = (
                True if len(partitions_str.split(" ")[1]) > 38 else False
            )
            if not default_partition:
                (table_dir / "partitions.tmdl").write_text(partitions_str)
            partition_file = (
                (table_dir / "original.tmdl")
                if original
                else (table_dir / "partitions.tmdl")
            )
            partitions_str = partition_file.read_text()
            tmdl_final_text = add_partitions(tmdl_str, partitions_str, line_no)
            tmdl_file.write_text(tmdl_final_text)
    print(
        "Multi partitions removed, ready for editing"
        if original
        else "Multi partitions restored for publishing"
    )


def add_partitions(tmdl_text: str, partitions_text: str, line_no: int):
    tmdl_lines = tmdl_text.split("\n")
    partitions_lines = partitions_text.split("\n")
    if partitions_lines[0] in ("", "\n"):
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
        if p == "\n" and found:
            continue
        clean_partitions.append(p)
        if p == "\n":
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
            if i > 2 and token[i - 2] == variable and token[i - 1] == "=":
                tmdl_out.append(value)
            else:
                tmdl_out.append(t)
        f.write_text(" ".join(tmdl_out))


def get_partitions(file) -> list:
    partitions = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("\tpartition "):
                partitions.append(line.split("=")[0][11:-1].strip("'"))
    return partitions


def get_source_columns(file) -> dict:
    columns = {}
    column = ""
    dtype = ""
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            tokens = line.split(" ")
            if tokens[0] == "\t\tdataType:":
                dtype = tokens[1].replace("\n", "")
            if tokens[0] == "\tcolumn":
                column = " ".join(tokens[1:]).replace("'", "").replace("\n", "")
            #     columns.append()
            elif (
                tokens[0] == "\t\tsourceColumn:"
                and " ".join(tokens[1:]).replace("'", "").replace("\n", "") == column
            ):
                columns[column] = dtype
    return columns


@app.command()
def partitions():
    pp(get_multi_partitions())


# am i using this and is it now broken.
def get_multi_partitions():
    raise NotImplementedError
    models = print_models()
    result = {}
    for m, tbls in models.items():
        for t, p in tbls.items():
            if len(p) > 1:
                if result.get(m) is None:
                    result[m] = {t: p}
                else:
                    result[m] = result[m] | {t: p} if result.get(m) else {t: p}
    return result


def update_partitions():
    partitions = get_multi_partitions()


@app.command()
def print_models(write: bool = False) -> dict:
    models = {}
    sn_table_mapper = {}
    params = model_parameters()
    for f in REPORT_DIR.glob("**/tables/*.tmdl"):
        model = f.parent.parent.parent.stem
        table = f.stem
        _, _, partitions_str = remove_partitions(f)
        sn_table = extract_sf_object(partitions_str)
        sn_table = (
            params[model].get(sn_table) if params[model].get(sn_table) else sn_table
        )
        sn_table_mapper[sn_table] = table
        partition_names = get_partitions(f)
        columns = get_source_columns(f)
        if models.get(model) is None:
            models[model] = {sn_table: columns}
        else:
            models[model] = (
                models[model] | {sn_table: columns}
                if models.get(model)
                else {sn_table: columns}
            )
    if write:
        write_tables(models, sn_table_mapper)
    pp(models)


@app.command()
def model_parameters() -> dict:
    params = {}
    for f in REPORT_DIR.glob("**/expressions.tmdl"):
        params[f.parent.parent.stem] = {}
        tokens = f.read_text().replace("\n", " ").split(" ")
        for i, t in enumerate(tokens):
            if t == "expression":
                params[f.parent.parent.stem] = params[f.parent.parent.stem] | {
                    tokens[i + 1]: tokens[i + 3].strip('"')
                }
    return params


def extract_sf_object(partition: str):
    import re

    t = re.compile('\[Name=(\w*|"\w*"),Kind="Table"\]')
    v = re.compile('\[Name=(\w*|"\w*"),Kind="View"\]')
    tables = t.findall(partition)
    views = v.findall(partition)
    if len(tables) > 0:
        return tables[0].strip('"')
    if len(views) > 0:
        return views[0].strip('"')
    return "Table Not Found"


def write_tables(models: dict, table_mapper: dict) -> None:
    import xlsxwriter

    wb = xlsxwriter.Workbook("pbi_models.xlsx")
    for model, tables in models.items():
        ws = wb.add_worksheet(model)
        row_num = 0
        for table, columns in tables.items():
            ws.write(0, 0, "Query Name")
            ws.write(0, 1, "Table Name")
            ws.write(0, 2, "Column Name")
            ws.write(0, 3, "Data Type")
            for column, dtype in columns.items():
                ws.write(row_num := row_num + 1, 0, table_mapper[table])
                ws.write(row_num, 1, table)
                ws.write(row_num, 2, column)
                ws.write(row_num, 3, dtype)

    wb.close()


@app.command()
def order_tables():
    for f in REPORT_DIR.glob("**/model.tmdl"):
        lines = f.read_text().split("\n")
        for i, l in enumerate(lines):
            if l.startswith("annotation PBI_QueryOrder ="):
                tables = eval(l[28:])
                tables.sort()
                lines[i] = f"annotation PBI_QueryOrder = {tables}".replace("'", '"')
        f.write_text("\n".join(lines))


if __name__ == "__main__":
    app()
