tables = [
    "Budget",
    "Channel",
    "Analysis",
    "Region",
    "Cost Centre",
    "Country",
    "Main Account",
    "Retail Store",
    "General Ledger Fact",
    "Comparatives",
    "Metrics",
    "Vendor",
    "Selling Status",
    "Date",
]

partition_tables = {
    "General Ledger Fact": ["FY2021", "FY2022", "FY2023", "FY2024"],
}

non_partition_tables: list = [t for t in tables if t not in partition_tables.keys()]

non_partition_tables_dict: dict = {table: [] for table in non_partition_tables}
