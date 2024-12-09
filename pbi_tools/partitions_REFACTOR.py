from pbi_tools.utils.constants import REPORT_DIR
from pprint import pp
from typing import Literal
import fiscalyear as fy
from datetime import datetime
from pbi_tools.utils.constants import FISCAL_YEAR_START_MONTH
from abc import ABC, abstractmethod

fy.START_MONTH = FISCAL_YEAR_START_MONTH

# TODO This module is not used do!!!!!!!!
# TODO trigger pipeline


def get_tables() -> dict:
    tables = {}
    for f in REPORT_DIR.glob("**/tables/*.tmdl"):
        report = f.parent.parent.parent.stem
        table = f.stem
        partitions = get_partitions(f)
        if tables.get(report) is None:
            tables[report] = {table: partitions}
        else:
            tables[report] = (
                tables[report] | {table: partitions}
                if tables.get(report)
                else {table: partitions}
            )

    return tables


def get_partitions(file) -> list:
    partitions = []
    with open(file) as f:
        lines = f.readlines()
        for line in lines:
            if line.startswith("\tpartition "):
                partitions.append(line.split("=")[0][11:-1].strip("'"))
    return partitions


def get_multi_partitions():
    models = get_tables()
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
    pass


def get_current_fin_year_int() -> int:
    return fy.FiscalYear.current()._fiscal_year


def get_current_year(financial: bool = False) -> int:
    return fy.FiscalYear.current()._fiscal_year if financial else datetime.now().year


# Define a standard partition name... This is the only way we can consitantly pick up the latest partition date...
# {FY|CY}YYYY{M|P}MM{W}WW
class Partition(ABC):
    def __init__(
        self,
        template: str,
        frequency: Literal["WEEK", "MONTH", "YEAR"] = "YEAR",
        calendar: Literal["FINANCIAL", "CALENDAR"] = "CALENDAR",
    ):
        self.frequency = frequency
        self.calendar = calendar
        self.template = template

    def get_partition(self):
        return f"\tpartition FY2023 = m\n\t\tmode: import\n\t\t: full\n\t\tsource = ```\n{self.partition}"

    # FY|CY2023M|W01

    def get_new_partition_periods(self, existing_partitions: list):
        latest_partition = max(existing_partitions)
        if self.frequency == "YEAR":
            year = (
                get_current_year()
                if self.calendar == "FINANCIAL"
                else get_current_year(True)
            )
        return latest_partition, year

    @abstractmethod
    def partition(year: str, month: str, day: str):
        """

        Args:
            year (str): This is either the
            month (str): _description_
            week (str): _description_
        """


if __name__ == "__main__":
    pp(get_multi_partitions())
