import re
from pbi_tools.utils.constants import WORKSPACE_ENVS, ENV


def get_event_query(
    year: int,
    month: int,
    day: int,
    start_hour: int = 0,
    end_hour: int = 0,
    workspace: ENV = "prod",
) -> str:
    time_query = f"'Suboperation - Query'[Start Time (s)] >= TIME({start_hour},0,0) && 'Suboperation - Query'[Start Time (s)] <= TIME({end_hour},0,0)"
    if start_hour == 23 or end_hour == 0:
        time_query = f"'Suboperation - Query'[Start Time (s)] >= TIME({start_hour},0,0)"
    return re.sub(
        " +",
        " ",
        f"""EVALUATE
                DISTINCT(
                    SUMMARIZECOLUMNS( 
                    'Suboperation - Query'[WorkspaceName],
                    'Suboperation - Query'[Dataset],
                    'Suboperation - Query'[EventText],
                    'Suboperation - Query'[Start Date/Time],
                    FILTER('Suboperation - Query', 'Suboperation - Query'[Start Date] = DATE({year}, {month}, {day}) 
	                    &&  {time_query}
                        && 'Suboperation - Query'[WorkspaceName] = \"{WORKSPACE_ENVS[workspace]}\"
	                    )
                    )
                )
                """.replace("\t", "").replace("\n", " "),
    )


if __name__ == "__main__":
    print(get_event_query(10, 12, 2024, 12, 9))
