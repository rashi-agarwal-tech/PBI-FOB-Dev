from pathlib import Path
import xmltodict
import csv
import re
import typer
import json
import copy
import pandas as pd
from matplotlib import pyplot as plt
import pprint as pp

app = typer.Typer()

CURRENT_DIR = Path(__file__).parent

BASE_LINE = "DMA_D2C20231030"
TSV_FILE = "events.tsv"
EVENTS_TOP_LEVEL_DIR = "events"
PROFILES_TOP_LEVEL_DIR = "profiles"
CSV_TOP_LEVEL_DIR = "csv"
ANALYSIS_TOP_LEVEL_DIR = "analysis"

PROFILES_DIR = CURRENT_DIR / PROFILES_TOP_LEVEL_DIR
ANALYSIS_DIR = CURRENT_DIR / ANALYSIS_TOP_LEVEL_DIR
TSV_FILE_PATH = CURRENT_DIR / EVENTS_TOP_LEVEL_DIR / TSV_FILE

POWERBI_USER = "PowerBISA-SVC@drmartens.com"

# Columns to keep:
COLUMNS = [
    "StartTime",
    "CurrentTime",
    "ObjectName",
    "EventClass",
    "EventSubclass",
    "ProcessType",
    "TextData",
    "Duration",
    "CPUTime",
    "RequestProperties",
]


def get_trace(xml_file: Path) -> dict:
    return xmltodict.parse(xml_file.read_text(encoding="utf-16"))


def flatten_trace(trace: dict) -> list[dict]:
    flat_rows = []
    for r in trace["TraceData"]["Events"]["Event"]:
        row = {"EventClass": r["@name"]}
        for c in r["Column"]:
            row[c["@name"]] = c["#text"]
        flat_rows.append(row)
    return flat_rows


def load_event_subclasses(file: Path) -> dict:
    tsv_matches = re.findall("\d* - [^\t]*", file.read_text())
    return {e[: e.find("-") - 1]: e[e.find("-") + 2 :] for e in tsv_matches}


def add_event_subclass(data: list[dict], event_subclass: dict = None) -> list[dict]:
    return [
        r
        | {
            "EventSubclass": event_subclass.get(r.get("EventSubclass")),
            "EventSubclassId": r.get("EventSubclass"),
        }
        for r in data
    ]


def add_duration_seconds(data: list[dict]) -> list[dict]:
    return [r | {"Duration": int(r.get("Duration", 0)) / 1000} for r in data]


def add_process_type(data: list[dict]) -> list[dict]:
    return [
        r
        | {
            "ProcessType": r.get("TextData")[20 : r.get("TextData").find("'") - 1]
            if r.get("TextData", "").startswith("Finished processing")
            else ""
        }
        for r in data
    ]


def write_csv(data: list[dict], csv_file: Path, header: list = []) -> None:
    with open(csv_file, "w", newline="") as csv_out:
        header = header if header else get_header(data)
        writer = csv.DictWriter(csv_out, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)


def write_summary(summary: dict, file_out: Path):
    file_out.write_text(json.dumps(summary, indent=4))


def get_header(data: list) -> list:
    return list(set([k for d in data for k in d]))


def filter_rows(
    filter: str | list[str], column: str, data: list[dict], remove: bool = False
) -> list[dict]:
    if isinstance(filter, str):
        filter = [filter]
    if remove is True:
        return [
            r
            for r in data
            if not any(f in str(r.get(column, "") or "") for f in filter)
        ]
    return [r for r in data if any(f in str(r.get(column, "") or "") for f in filter)]


def keep_columns(columns: list, data: list[dict]) -> list[dict]:
    return [{k: r.get(k) for k in columns} for r in data]


def remove_columns(columns: list, data: list[dict]) -> list[dict]:
    for r in data:
        {k: v for k, v in r.items() if k not in columns}
    return [{k: v for k, v in r.items() if k not in columns} for r in data]


def clean_data(data: list[dict]) -> list[dict]:
    data = filter_rows(data=data, filter="Power BI Service", column="NTUserName")
    data = filter_rows(
        filter=get_most_frequent(data, "ConnectionID"), column="ConnectionID", data=data
    )
    return data


def get_most_frequent(data: list[dict], column: str) -> list[dict]:
    conn_id = [r.get(column) for r in data]
    return max(set(conn_id), key=conn_id.count)


def get_min_value(data: list[dict], column: str) -> str:
    return min([r.get(column) for r in data if r.get(column)])


def get_max_value(data: list[dict], column: str) -> str:
    return max([r.get(column) for r in data if r.get(column)])


def find_end(string: str, search: str) -> str:
    return string.find(search) + len(search)


def kb_gb(memory: str) -> float:
    memory = memory.split(" ")[0]
    return round(int(memory) / 1028 / 1028, 2)


def get_summary(data: list[dict]) -> dict:
    cmd_end = max(data, key=lambda x: x["Duration"])
    filtered = filter_rows(column="ProcessType", filter="partition", data=data)
    part_info = min(
        filtered,
        key=lambda x: x["CurrentTime"],
    )

    proc_txt = part_info["TextData"]

    peak_row = filter_rows(column="TextData", filter="[PeakMemory", data=data)[0]
    peak_text = peak_row["TextData"]

    peak_mem_gb = kb_gb(
        peak_text[find_end(peak_text, "[PeakMemory: ") : peak_text.find(" KB, ")]
    )
    # mashup_cpu_time_s = int(peak_text[find_end(peak_text, "MashupCPUTime: "): peak_text.find(" KB, ")-1])/60
    # mashup_peak_mem_gb = peak_text[find_end(peak_text, "MashupPeakMemory: "): peak_text.find(" KB, ")-1]/2056

    summary = {
        "model": get_most_frequent(data, "DatabaseName"),
        "total_time_s": int(get_max_value(data, "Duration")),
        "start_time": cmd_end["StartTime"],
        "end_time": cmd_end["CurrentTime"],
        "memory_peak_gb": peak_mem_gb,
        "cpu_time_s": int(peak_row["CPUTime"]) / 1000,
        "table": proc_txt[
            proc_txt.find("<ccon>", proc_txt.find("<ccon>") + 1) + 6 : proc_txt.find(
                "</ccon>", proc_txt.find("</ccon>") + 1
            )
        ],
        "partition_name": part_info["ObjectName"],
        # {
        #     "name": part_info["ObjectName"],
        #     "total_cpu": proc_txt[
        #         find_end(proc_txt, "MashupCPUTime: ") : proc_txt.find("ms,") - 1
        #     ],
        #     "total_memory":kb_gb(proc_txt[
        #         find_end(proc_txt, "MashupPeakMemory: ") : proc_txt.find("KB]") - 1
        #     ]),
        # },
        "read_data": sum_column(
            columns=["Duration", "CPUTime"],
            data=filter_rows(
                column="TextData", filter="Finished reading data", data=data
            ),
        ),
        "sql_execution": sum_column(
            columns=["Duration"],
            data=filter_rows(column="EventSubclass", filter="ExecuteSQL", data=data),
        ),
        **get_process_type_sum(data),
    }
    summary["file_name"] = (
        f"{remove_invalid_char(summary['model'])}_{remove_invalid_char(summary['table'])}_{remove_invalid_char(summary['partition_name'])}_{remove_invalid_char(summary['start_time'])[:16]}"
    )
    return summary


def get_distinct(data: list[dict], column: str) -> list:
    return list(set([r[column] for r in data]))


def sum_column(data: list[dict], columns: str | list[str]) -> dict[int]:
    if isinstance(columns, str):
        columns = [columns]
    return {
        c: int(
            sum(
                [
                    int(r.get(c, 0)) / 1000 if c in ("CPUTime") else int(r.get(c, 0))
                    for r in data
                ]
            )
        )
        for c in columns
    }


def get_process_type_sum(data: list[dict]) -> dict:
    column = "ProcessType"
    return {
        c: sum_column(
            columns=["Duration", "CPUTime"],
            data=filter_rows(filter=c, column=column, data=data),
        )
        for c in get_distinct(data, column)
        if c not in ("", "the")
    }


def load_baseline_summary(summary: dict) -> dict:
    base_line_path = (
        ANALYSIS_DIR / BASE_LINE / summary["table"] / summary["partition_name"]
    )
    if base_line_path.is_dir():
        latest = max([d for d in base_line_path.iterdir() if d.is_dir()])
        sub_dir = base_line_path / latest
        b_summary = [f for f in sub_dir.iterdir() if "_summary.json" in f.name]
        if len(b_summary) > 0:
            print(b_summary[0])
            return json.loads(b_summary[0].read_text())


def compare_summary(summary: dict, baseline: dict) -> dict:
    duration_labels = [
        "total_time_s",
        "read_data",
        "sql_execution",
        "relationship",
        "calculated column",
        "hierarchy",
    ]
    cpu_labels = [
        "cpu_time_s",
        "read_data",
        "sql_execution",
        "relationship",
        "calculated column",
        "hierarchy",
    ]

    def process(measure: str, labels: list) -> dict:
        metrics = {baseline["model"]: [], summary["model"]: []}
        comp_metrics = []
        for m in labels:
            b = s = pct = 0
            if summary.get(m):
                if isinstance(summary[m], dict):
                    b = baseline[m].get(measure, 0)
                    s = summary[m].get(measure, 0)
                else:
                    b = baseline[m]
                    s = summary[m]

            metrics[baseline["model"]].append(b / 60)
            metrics[summary["model"]].append(s / 60)
            if b != 0:
                pct = round((s * 100 / b), 2)
            comp_metrics.append(pct)
        return metrics, comp_metrics

    duration_metrics, d_cmp_metrics = process("Duration", duration_labels)
    cpu_metics, cpu_cmp_metrics = process("CPUTime", cpu_labels)
    # memory_metric = {
    #     baseline["model"]: [baseline["memory_peak_gb"]],
    #     summary["model"]: [summary["memory_peak_gb"]],
    # }
    print(d_cmp_metrics)

    plotdata = pd.DataFrame(cpu_metics, index=duration_labels)
    plotdata.plot(kind="bar")
    plt.title("Model Refresh Comparison")
    plt.xlabel("Metric")
    plt.ylabel("Time (m)")
    plt.show()


def remove_invalid_char(filename: str) -> str:
    return "".join(c for c in filename.replace(" ", "_") if c.isalnum() or c == "_")


def create_dir(file_path: Path) -> None:
    print(file_path.suffix)
    if file_path.is_file() or file_path.suffix != "":
        file_path = file_path.parent
    file_path.mkdir(parents=True, exist_ok=True)


def ensure_pathlib(file: str | Path) -> Path:
    if not isinstance(file, Path):
        file = Path(file).absolute()
    return file


def copy_xml(file: str | Path, file_out: str | Path) -> None:
    file = ensure_pathlib(file)
    file_out = ensure_pathlib(file_out)
    create_dir(file_out)
    print(file_out)
    xml_data = file.read_text(encoding="utf-16")
    file_out.write_text(xml_data)


@app.command()
def convert2csv(xml_file: str, csv_file: str = None):
    xml_path = Path(xml_file).absolute()
    trace = get_trace(Path(xml_path))

    flat_trace = flatten_trace(trace)
    events = load_event_subclasses(TSV_FILE_PATH)

    data = add_event_subclass(flat_trace, events)
    data = add_duration_seconds(data)
    data = add_process_type(data)

    data_raw = copy.deepcopy(data)
    data = clean_data(data)

    summary = get_summary(data)
    print(summary)

    data = keep_columns(data=data, columns=COLUMNS)

    stem_dir = (
        Path(remove_invalid_char(summary["model"]))
        / remove_invalid_char(summary["table"])
        / remove_invalid_char(summary["partition_name"])
        / remove_invalid_char(summary["start_time"][:16])
    )

    profile_dir = (PROFILES_DIR / stem_dir).absolute()
    analysis_dir = (ANALYSIS_DIR / stem_dir).absolute()
    # baseline_dir = (PROFILES_DIR / "DMA D2C" / remove_invalid_char(summary["table"]) / remove_invalid_char(summary["partition"]) / ).absolute()

    create_dir(profile_dir)
    create_dir(analysis_dir)
    summary_file_name = summary["file_name"]
    if csv_file is None:
        csv_file_raw = analysis_dir / f"{summary_file_name}_raw.csv"
        csv_file = analysis_dir / f"{summary_file_name}.csv"

    copy_xml(xml_path, profile_dir / f"{summary_file_name}_trace.xml")

    write_csv(data, csv_file, COLUMNS)
    write_csv(data_raw, csv_file_raw)
    write_summary(summary, analysis_dir / f"{summary_file_name}_summary.json")

    b_summary = load_baseline_summary(summary)
    pp(b_summary)
    compare_summary(summary, b_summary)


if __name__ == "__main__":
    # app()
    convert2csv(
        "/home/martin/repos/powerbi_analysis/powerbi_tools/mssql_prof2csv/gl-trace.xml"
    )
