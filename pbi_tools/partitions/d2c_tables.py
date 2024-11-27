import fiscalyear

fiscalyear.START_MONTH = 4

tables = [
    "Website Name",
    "Website",
    "Web Device",
    "Web Channel",
    "Warehouse",
    "TMALL",
    "Time",
    "Territory",
    "Store Activity FC",
    "SmartRes",
    "Size Classification",
    "Size",
    "Selling Status - Order Entry",
    "Selling Status - Invoice",
    "Seasonal Product Info",
    "Seasonal Product Forecast",
    "Retail Payment Methods",
    "Retail Payment Details",
    "Retail Demographics",
    "Regions",
    "Region",
    "Refit Slicer",
    "Refit Exclusion",
    "Purchase Orders",
    "Products",
    "Product Weights",
    "Product Class",
    "Pick",
    "Orders",
    "Order Type",
    "Order Taker",
    "Open eCom Return Info",
    "Net Transactions",
    "Model Refresh Time",
    "Metrics",
    "Hours Worked",
    "Google Analytics Goals",
    "Google Analytics Ads",
    "Google Analytics",
    "GA Demand FC",
    "GA Country",
    "Forecast Version",
    "Forecast Ecom Demand",
    "Forecast Additional Ecom",
    "Forecast",
    "Footfall",
    "Financial Channel",
    "Exchange Rates",
    "Ecom Email Marketing",
    "Display Currency",
    "Date Slicer",
    "Date - Order Date",
    "Date",
    "Customer",
    "Channel",
    "BridgeSalesOrderNumber",
    "Bridge InventTransID",
    "Availability",
    "Adjustments Sales",
    "Adjustments CoGS",
    "Account Details",
    "Retail Mpos",
]

# Below can be automated...
partition_tables = {
    "Availability": [
        "CY2021 H1",
        "CY2021 H2",
        "CY2022 H1",
        "CY2022 H2",
        "CY2023 H1",
        "CY2023 07",
        "CY2023 08",
        "CY2023 09",
        "CY2023 10",
        "CY2023 11",
        "CY2023 12",
        "CY2024 01",
        "CY2024 02",
    ],
    "Orders": ["FY2021", "FY2022", "FY2023", "FY2024"],
    "Google Analytics": ["CY2023 12"],
    "Google Analytics Goals": ["CY2023 12"],
}


def get_latest_partition(partitions: list):
    partitions.sort(reverse=True)
    return partitions[0]

non_partition_tables: list = [t for t in tables if t not in partition_tables.keys()]

non_partition_tables_dict: dict = {table: [] for table in non_partition_tables}

partition_tables_current_only = {
    table: [get_latest_partition(partitions)]
    for table, partitions in partition_tables.items()
}

if __name__ == "__main__":
    pass
