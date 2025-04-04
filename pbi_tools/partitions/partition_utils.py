import fiscalyear
import pendulum
from datetime import datetime
from pbi_tools.utils.constants import FISCAL_YEAR_START_MONTH, PBI_META_FILE
import json

fiscalyear.START_MONTH = FISCAL_YEAR_START_MONTH

if PBI_META_FILE.exists():
    models = json.loads(PBI_META_FILE.read_text())
else:
    raise FileExistsError(
        f"It appear that the table partition meta data is not present, {PBI_META_FILE}"
    )


def get_current_fin_year() -> str:
    return str(fiscalyear.FiscalYear.current())


def get_current_month() -> str:
    return str(datetime.now().month)


def get_current_year() -> int:
    return str(datetime.now().year)


def pad_str_integer(integer: str) -> str:
    return integer.rjust(2, "0")


def get_latest_partition(partitions: list):
    partitions.sort(reverse=True)
    return partitions[0]


def get_latest_fy_partition():
    return f"{get_current_fin_year()}"


def get_latest_cy_mm_partition():
    return f"CY{get_current_year()} {pad_str_integer(get_current_month())}"


def get_current_fin_year_int() -> int:
    return fiscalyear.FiscalYear.current()._fiscal_year


def get_fin_years(years:int=3, append_str="FY", future_years:int=0) -> list:
    buffer = {}
    curr_fin_year = get_current_fin_year_int()
    today = datetime.today()
    if today.month in [3, 4]:
        buffer = {f"{append_str}{today.year}", f"{append_str}{today.year+1}"}
    future_years *= -1
    return list({f"{append_str}{str(curr_fin_year-i)}" for i in range(future_years, years)}.union(buffer))


def get_cy_mm(months: int = 3, append_str="CY", future_months: int = 0) -> list:
    today = pendulum.now()
    if future_months > 0:
        today = today.add(months=future_months)
    year_months = get_last_x_year_months(months + future_months, today)
    return [f"{append_str}{i[0]} {pad_str_integer(str(i[1]))}" for i in year_months]


def get_last_x_year_months(months: int, anchor_date=pendulum.now()) -> list:
    return [
        (anchor_date.add(months=-i).year, anchor_date.add(months=-i).month)
        for i in range(months)
    ]


def get_current_cy_qq_partition() -> str:
    month = datetime.now().month
    return f"CY{get_current_year()} {-(-3 // month)}"


def get_tables(dataset: str, partitioned: bool | None = None) -> list:
    return [
        table
        for table, v in models[dataset].items()
        if v["partitioned"] == partitioned or partitioned is None
    ]


if __name__ == "__main__":
    print(get_tables("DMA D2C", False))
