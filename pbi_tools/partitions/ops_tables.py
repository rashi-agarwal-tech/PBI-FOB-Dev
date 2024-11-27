import fiscalyear

fiscalyear.START_MONTH = 4

tables = [
    "Allocation Details",
    "Adjustments",
    "Availability",
    "Bridge InventTransID",
    "Bridge PPM Supplier PO",
    "Customer",
    "Customer Sell Out US",
    "Date",
    "Date Slicer",
    "Display Currency",
    "Exchange Rates",
    "From Warehouse",
    "Global Product Forecast",
    "Intake",
    "Metrics",
    "Model Refresh Time",
    "Movements",
    "Pick",
    "PO ETD Date",
    "Product Class",
    "Product Weights",
    "Products",
    "Products - Last PO",
    "Products - Last PO SKU",
    "Purchase Season",
    "Sales Order Pool",
    "Sales Order Type",
    "Selling Status - Invoice",
    "Selling Status - Order Entry",
    "Size",
    "To Warehouse",
    "Vendor",
    "Warehouse",
]

# Below can be automated...
partition_tables = {
    "Availability": [
        "CY2025 12",
        "CY2025 11",
        "CY2025 10",
        "CY2025 09",
        "CY2025 08",
        "CY2025 07",
        "CY2025 06",
        "CY2025 05",
        "CY2025 02",
        "CY2025 03",
        "CY2025 02",
        "CY2025 01",
        "CY2024 12",
        "CY2024 11",
        "CY2024 10",
        "CY2024 09",
        "CY2024 08",
        "CY2024 07",
        "CY2024 Q2",
        "CY2024 Q1",
        "CY2023 Q4",
        "CY2023 Q3",
        "CY2023 Q2",
        "CY2023 Q1",
        "CY2022 Q4",
        "CY2022 Q3",
        "CY2022 Q2",
        "CY2022 Q1",
        "CY2021 Q4",
        "CY2021 Q3",
    ],
    "Movements": [
        "FY2030",
        "FY2029",
        "FY2028",
        "FY2027",
        "FY2026",
        "FY2025",
        "FY2024",
        "FY2023",
        "FY2022",
        "FY2021",
    ],
    "Intake": [
        "CY2025 Q4",
        "CY2025 Q3",
        "CY2025 Q2",
        "CY2025 Q1",
        "CY2024 Q4",
        "CY2024 Q3",
        "CY2024 H1",
        "CY2023 H2",
        "CY2023 H1",
        "CY2022 H2",
        "CY2022 H1",
        "CY2021 H2",
        "CY2021 H1",
    ],
}


def get_latest_partition(partitions: list) -> str:
    partitions.sort(reverse=True)
    return partitions[0]


non_partition_tables: list = [t for t in tables if t not in partition_tables.keys()]

non_partition_tables_dict: dict = {table: [] for table in non_partition_tables}

partition_tables_current_only = {
    table: [get_latest_partition(partitions)]
    for table, partitions in partition_tables.items()
}
