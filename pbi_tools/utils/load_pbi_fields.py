"""
This module is used to extract data from the PBI AS Engine report and sync the data to snowflake.
"""

from pbi_tools.api.auth import get_user_token
from pbi_tools.api.dax_query import MSApiQuery
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
import re
from collections import Counter
from pbi_tools.utils.constants import PBI_AS_ENGINE_ID
from pbi_tools.dax.query import get_event_query


def extract_fields(date: datetime = datetime.now(), delta_days: int = 0) -> list[tuple]:
    print(f"Received date as: {type(date)} -> {date}")
    previous_date = date - timedelta(days=delta_days)
    result = []

    with ThreadPoolExecutor() as pool:
        dax_exe = MSApiQuery(token=get_user_token())
        futures = [
            pool.submit(
                dax_exe.execute_query,
                PBI_AS_ENGINE_ID,
                get_event_query(
                    start_hour=hour,
                    end_hour=hour + 1,
                    year=previous_date.year,
                    month=previous_date.month,
                    day=previous_date.day,
                ),
            )
            for hour in range(0, 24)
        ]

        for future in futures:
            data = future.result()
            rows = [
                [
                    row["Suboperation - Query[WorkspaceName]"],
                    row["Suboperation - Query[Dataset]"],
                    row["Suboperation - Query[Start Date/Time]"][0:14] + "00:00",
                ]
                + re.findall(
                    r"\[[^\]]+\]\.\[[^\]]+\]", row["Suboperation - Query[EventText]"]
                )
                for row in data["results"][0]["tables"][0]["rows"]
            ]
            # Each table and column has a number in brackets associated with it [Orders (33)].[Shoes (8)]
            # These are removed with the regex below.
            rows = list(
                Counter(
                    [
                        (
                            row[0],
                            row[1],
                            *re.sub(r"\ \(\d+\)", "", column).split("."),
                            row[2],
                        )
                        for row in rows
                        for i, column in enumerate(row)
                        if i > 1
                    ]
                ).items()
            )
            result.extend(rows)
    return [(*r[0], r[1]) for r in result if len(r[0]) > 4]


def write_snowflake():
    pass


def run(days: int = 1):
    extract_fields(days=days)
    write_snowflake()


# ('Dr. Martens Datasets', 'DMA D2C', '2025-01-07T00:00:00', '[Orders]', '[Invoiced Full Value Col Cons GBP]', 1)
if __name__ == "__main__":
    data = extract_fields()
    print(data)
# 'Dr. Martens Datasets', 'DMA D2C', '[Orders]', '[DateMaster Order]', '2025-01-14T00:00:00', 3)
