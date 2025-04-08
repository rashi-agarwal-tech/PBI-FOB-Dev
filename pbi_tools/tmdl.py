from pathlib import Path
from pbi_tools.utils.constants import REPORT_DIR, PARTITIONS_DIR
import re
import networkx as nx

def get_relation_between(model, table_a, table_b, graph: bool = False):
    G = create_relationship_graph(model)
    nodes = nx.shortest_path(G, table_a, table_b, 5)
    if graph:
        plot_relationships(G.subgraph(nodes), f"{model}: {table_a} to {table_b}")
    else:
        print_relationship_between(G, nodes)

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
        for i, line in enumerate(lines):
            if found:
                matched = re.search(r"^\t\w", line)
                if matched:
                    found = False
            if line.startswith("\tpartition "):
                partitions.append("\n")
                first_partition.append(i)
                found = True
            if not found:
                output.append(line)
            else:
                partitions.append(line)
    partitions = remove_duplicate_blanks(partitions)
    return min(first_partition), "".join(output), "".join(partitions)


def get_first_partition_name(partition: str) -> str:
    lines = partition.split("\n")
    for line in lines:
        if line.startswith("\tpartition "):
            return line.split("=")[0][11:-1].strip("'")


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


def get_variable_values(variable: str) -> dict:
    values = {}
    for f in REPORT_DIR.glob("**/expressions.tmdl"):
        tokens = f.read_text().split(" ")
        for i, t in enumerate(tokens):
            if i > 2 and tokens[i - 2] == variable and tokens[i - 1] == "=":
                values[f.parent.parent.stem] = t
                break
    return values


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


def get_multi_partitions():
    models = get_models()
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
    return partitions


def get_expected_partitions():
    return {
        m.name: [t.name for t in m.iterdir()]
        for w in PARTITIONS_DIR.iterdir()
        for m in w.iterdir()
    }


def get_models(write: bool = False) -> dict:
    models = {}
    sn_table_mapper = {}
    params = get_model_parameters()
    exp_partitions = get_expected_partitions()
    for f in REPORT_DIR.glob("**/tables/*.tmdl"):
        model = f.parent.parent.parent.stem
        table = f.stem
        _, _, partitions_str = remove_partitions(f)
        sn_table = extract_sf_object(partitions_str)
        sn_table = (
            params.get(model).get(sn_table)
            if params.get(model, {}).get(sn_table)
            else sn_table
        )
        sn_table_mapper[sn_table] = table
        partition_names = get_partitions(f)
        columns = get_source_columns(f)
        tbl_exp_partition = table in exp_partitions.get(model, [])
        if models.get(model) is None:
            models[model] = {
                table: {
                    "db_table": sn_table,
                    "columns": columns,
                    "partitioned": len(partition_names) > 1,
                    "multi_partition_expected": tbl_exp_partition,
                }
            }
        else:
            models[model] = models[model] | {
                table: {
                    "db_table": sn_table,
                    "columns": columns,
                    "partitioned": len(partition_names) > 1,
                    "multi_partition_expected": tbl_exp_partition,
                }
            }
    if write:
        write_tables(models, sn_table_mapper)
    return models


def get_model_parameters() -> dict:
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


def get_relationships(model: str) -> list[dict]:
    relationships = []
    for f in REPORT_DIR.glob(f"**/{model}.*/**/relationships.tmdl"):
        relations = f.read_text().split("relationship")
        for r in relations:
            if "isActive" not in r and r != "":
                t = r.split("\n")[1:]
                t[0].split(" ")[1]
                from_tbl_col = [
                    " ".join(line.split(" ")[1:]) for line in t if "fromColumn" in line
                ][0]
                from_tbl, from_col = [
                    c.strip("'").strip('"') for c in from_tbl_col.split(".")
                ]
                toColumn = [
                    " ".join(line.split(" ")[1:]) for line in t if "toColumn" in line
                ][0]
                to_tbl, to_col = [c.strip("'").strip('"') for c in toColumn.split(".")]
                relationships.append(
                    {
                        "source_tbl": from_tbl,
                        "source_column": from_col,
                        "dest_tbl": to_tbl,
                        "dest_column": to_col,
                        "join_str": (
                            to_col if from_col == to_col else f"{from_col} = {to_col}"
                        ),
                    }
                )
    return relationships


def print_relationship_between(G, nodes):
    labels = [G.get_edge_data(*e)["columns"] for e in nodes_to_edges(nodes)]
    relationship_str = ["|"]
    for n in range(0, len(nodes) - 1, 1):
        relationship_str.append(f"{nodes[n]}|- ({labels[n]}) -|")
    relationship_str.append(f"{nodes[-1:][0]}|")
    return print("".join(relationship_str))


def create_relationship_graph(model) -> nx.Graph:
    relationships = get_relationships(model)
    G = nx.Graph()
    G.add_edges_from(
        [
            (r["source_tbl"], r["dest_tbl"], {"columns": r["join_str"]})
            for r in relationships
        ]
    )
    return G


def get_neighbors_graph(G: nx.Graph, table: str):
    nodes = [n for n in nx.neighbors(G, table)] + [table]
    return nx.subgraph(G, nodes)


def plot_relationships(G: nx.Graph, title: str = "Table Plot"):
    import matplotlib.pyplot as plt

    pos = nx.spring_layout(G)
    fig = plt.figure(1, figsize=(15, 15), dpi=60)
    fig.canvas.manager.set_window_title(title)
    nx.draw_networkx(
        G,
        pos,
        arrowsize=0,
        arrowstyle="|-|",
        arrows=True,
        alpha=0.5,
        node_size=1500,
        with_labels=True,
    )
    # column_labels = [ for e in G.edges()]
    column_labels = {e: G.get_edge_data(*e)["columns"] for e in G.edges()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=column_labels)
    plt.show()


def get_nx_neighbors(graph):
    neighbors = {n for n in nx.neighbors(graph, "Orders")}
    for n in [n for n in nx.neighbors(graph, "Orders")]:
        neighbors = neighbors | {i for i in nx.neighbors(graph, n)}
    return neighbors


def nodes_to_edges(nodes: list) -> list[tuple]:
    edges = []
    for n in range(0, len(nodes) - 1, 1):
        edges.append((nodes[n], nodes[n + 1]))
    return edges
