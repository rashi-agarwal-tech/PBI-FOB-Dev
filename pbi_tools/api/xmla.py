import json
from dataclasses import dataclass
from typing import Literal

# @dataclass
# class PowerBITablePartition:
#     table: str
#     partition: list = []

#     def to_dict(self, encode_json=False):
#         return {self.table: self.partition}

# @dataclass
# class PowerBITablePartitions:
#     table: str
#     partition: list = []

#     def to_dict(self, encode_json=False):
#         return {self.table: self.partition}


@dataclass
class PowerBIDaxQuery:
    query: str
    impersonatedUserName: str = "PowerBISA-SVC@drmartens.com"

    def to_dict(self, encode_json=False):
        query = {
            "queries": [{"query": self.query}],
            "impersonatedUserName": self.impersonatedUserName,
        }
        if encode_json:
            query = json.dumps(query)
        return query


@dataclass
class PowerBIParameters:
    name_value: list[tuple[str, str]]

    def to_dict(self, encode_json=False):
        return {
            "updateDetails": [
                {"name": name, "newValue": value} for name, value in self.name_value
            ]
        }


@dataclass
class PowerBIDataset:
    table: str
    partition: str | None = None
    database: str | None = None

    def to_dict(self, encode_json=False):
        dataset = {"table": self.table}
        if self.partition is not None:
            dataset["partition"] = self.partition
        if self.partition is not None:
            dataset["database"] = self.database
        return dataset


@dataclass
class PowerBIRefreshPartition:
    datasets: list[PowerBIDataset] | PowerBIDataset
    refresh_type: Literal[
        "full", "clearValues", "calculate", "dataOnly", "automatic", "defragment"
    ] = "full"
    commit_mode: Literal["transactional", "partialBatch"] = "transactional"
    max_parallelism: int = 10

    def to_dict(self, encode_json=False):
        if not isinstance(self.datasets, list):
            self.datasets = [self.datasets]

        return {
            "type": self.refresh_type,
            "commitMode": self.commit_mode,
            "maxParallelism": self.max_parallelism,
            "objects": [d.to_dict() for d in self.datasets],
        }


def get_refresh_partition_xmla(pw_refresh: PowerBIRefreshPartition) -> dict:
    return {"refresh": pw_refresh}


def get_create_partition_xmla(
    database: str, table: str, partition: str, expression: list[str]
) -> dict:
    return {
        "createOrReplace": {
            "object": {"database": database, "table": table, "partition": partition},
            "partition": {
                "name": partition,
                "mode": "import",
                "dataView": "full",
                "source": {"type": "m", "expression": expression},
            },
        }
    }


def get_m_exp_datetime(
    year: int, month: int, day: int, hour: int = 0, minute: int = 0, seconds: int = 0
) -> str:
    return f"#datetime({year}, {month}, {day}, {hour}, {minute}, {seconds})"


def get_m_exp_filter() -> list[str]:
    return [
        "let",
        '    Source = Value.NativeQuery(Snowflake.Databases("drmartensprod.west-europe.azure.snowflakecomputing.com","REPORTER"){[Name="PRESENTATION"]}[Data], "SELECT#(lf)    ""Product_Key"",#(lf)    ""Size_Key"",#(lf)    ""Warehouse_Key"",#(lf)    ""Company_Key"",#(lf)    ""SalesOrderPool_Key"",#(lf)    ""Customer_Key"",#(lf)    ""SALESORDERPOOLID_SOH"",#(lf)    ""INVOICEDQUANTITY_SIL"",#(lf)    ""COSTAMOUNTPOSTED_SILCS"",#(lf)    ""Invoice Number"",#(lf)    ""Discount"",#(lf)    ""Customer Order Reference"",#(lf)    ""DM Agent"",#(lf)    ""RMA Number"",#(lf)    ""Transaction Type"",#(lf)    ""AREPRICESINCLUDINGSALESTAX_SOH"",#(lf)    ""Barcode"",#(lf)    ""INVENTORYLOTID_SOL_ROL"",#(lf)    ""Time_Key"",#(lf)    ""Order Line"",#(lf)    ""Selling Status"",#(lf)    ""Source"",#(lf)    ""Web Order #"",#(lf)    ""Promo Code"",#(lf)    ""Website Code"",#(lf)    ""Order DateTime"",#(lf)        CASE#(lf)            WHEN ""Goodwill?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Goodwill?"",#(lf)        CASE#(lf)            WHEN ""Display Order?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Display Order?"",#(lf)        CASE#(lf)            WHEN ""Employee Discount?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Employee Discount?"",#(lf)        CASE#(lf)            WHEN ""Marketing?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Marketing?"",#(lf)        CASE#(lf)            WHEN ""Staff Uniform?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Staff Uniform?"",#(lf)    ""ORDEREDSALESQUANTITY_SOL_ZEROS"",#(lf)    ""Territory_Key"",#(lf)    ""DM Sales Associate"",#(lf)    ""Finance Dimension - Analysis"",#(lf)    ""Finance Dimension - Channel"",#(lf)    ""Finance Dimension - Cost Centre"",#(lf)    ""Finance Dimension - Country"",#(lf)    ""Finance Dimension - Selling Status"",#(lf)    ""Web Order Return Reason"",#(lf)        CASE#(lf)            WHEN ""Student Discount?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Student Discount?"",#(lf)    ""Shipping Warehouse"",#(lf)    ""EcomMultipleSizeOrderFlag"",#(lf)    ""Payment Method"",#(lf)    ""Delivery Address Country"",#(lf)    ""Delivery Address Zip Code"",#(lf)    ""Delivery Address State"",#(lf)    ""Delivery Address City"",#(lf)    ""Delivery Address Street"",#(lf)    ""Charge Description Line"",#(lf)    ""Product_Class_Key"",#(lf)    ""Sales Order Number"",#(lf)    ""INVOICECUSTOMERACCOUNTNUMBER_SIH"",#(lf)    ""Cancel Risk Date"",#(lf)    ""Web Affiliate ID"",#(lf)    ""Selling Status - Order Entry"",#(lf)    ""Delivery Mode"",#(lf)    ""Full Price/Promo/Clearance"",#(lf)        CASE#(lf)            WHEN ""Marketing Promo"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Marketing Promo"",#(lf)    ""Staff Email"",#(lf)    ""Retail Returns Reason Col"",#(lf)    ""Order Season"",#(lf)    ""Email"",#(lf)    ""LINEAMOUNT_SIL_CONS_GBP"",#(lf)    ""LINEAMOUNT_SOL_CONS_GBP"",#(lf)    ""ChargeTotalExcTax_CONS_GBP"",#(lf)    ""HeaderDiscount_CONS_GBP"",#(lf)    ""LineDiscount_CONS_GBP"",#(lf)    ""Full Price/Promo/Clearance Sort"",#(lf)    ""INVOICEDATE_SIL"",#(lf)    ""ITEMNUMBER_SOL_ROL"",#(lf)    ""Unit Price"",#(lf)    ""isCarrierBag"",#(lf)        CASE#(lf)            WHEN ""Digital Doc Shop Transaction?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Digital Doc Shop Transaction?"",#(lf)    ""DELIVERYDATE_SOL"",#(lf)    ""Date_Key"",#(lf)    ""REMAININVENTPHYSICAL_SOL_ZEROS"",#(lf)    ""RETURNEDSALESQUANTITY_ROL_ZEROS"",#(lf)    ""RETURNSALESQUANTITY_ROL_ZEROS"",#(lf)    ""CompanyProductSize_Key"",#(lf)    ""Delivery Address Region"",#(lf)            CASE#(lf)            WHEN ""Is Revenue Affecting?"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""Is Revenue Affecting?"",#(lf)    ""Transaction Status"",#(lf)    ""Cancellation Date"",#(lf)    ""Cancellation User"",#(lf)    ""Days Since Last Purchase"",#(lf)    ""Tax_CONS_GBP"",#(lf)    ""eCom Promotion Type"",#(lf)    ""REMAININVENTPHYSICAL_SOL"",#(lf)    ""ORDEREDSALESQUANTITY_SOL"",#(lf)    ""eCom Order Frequency"",#(lf)    ""Return Reason"",#(lf)    ""Cancellation Reason"",#(lf)    ""Cancellation Reason Code"",#(lf)    ""Customer Requisition Number"",#(lf)    ""Retail Faulty Returns Information"",#(lf)        CASE#(lf)            WHEN ""eCom New/Returning?"" THEN \'New\'#(lf)            ELSE \'Returning\'#(lf)        END AS ""eCom New/Returning?"",#(lf)        DATE(""SALESORDERCREATEDDATETIME_SOH"") AS ""SALESORDERCREATEDDATETIME_SOH"",#(lf)    ""Region Sub Channel"",#(lf)    ""Charge Code"",#(lf)    ""REQUESTEDSHIPPINGDATE_SOL"",#(lf)    ""DELIVERYADDRESSDESCRIPTION_SOL"",#(lf)    ""RETURNDISPOSITIONCODE_ROL"",#(lf)    ""CURRENCYCODE_SOH_ROH"",#(lf)    ""LINESTATUS_SOL_ROL"",#(lf)    ""SO_PO_ID"",#(lf)        CASE#(lf)            WHEN ""HDMSALESPRICELINEPERCENTOVERRIDE"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""HDMSALESPRICELINEPERCENTOVERRIDE"",#(lf)        CASE#(lf)            WHEN ""HDMSALESPRICEMANUALOVERRIDE"" THEN \'Yes\'#(lf)            ELSE \'No\'#(lf)        END AS ""HDMSALESPRICEMANUALOVERRIDE"",#(lf)        ""isHistorical""  #(lf)FROM#(lf)    ""PRESENTATION"".""BFN_PRESENTATION"".""D2C_BFN_VW_D365_FACT_SALES""", null, [EnableFolding=true]),',
        "    InvoiceDateSIL_Filter = Table.SelectRows(Source, each [INVOICEDATE_SIL] >= #datetime(2023, 4, 1, 0, 0, 0) and [INVOICEDATE_SIL] < #datetime(2023, 5, 1, 0, 0, 0))",
        "in",
        "    InvoiceDateSIL_Filter",
    ]


def get_sql_xmla():
    raise NotImplementedError


def save_xmla():
    raise NotImplementedError


if __name__ == "__main__":
    ds = PowerBIDataset(table="sales_table", partition="FY2023")
    ds1 = PowerBIDataset(table="availability_table")
    ds_refresh = PowerBIRefreshPartition(datasets=[ds, ds1])
    print(ds_refresh.to_dict())
