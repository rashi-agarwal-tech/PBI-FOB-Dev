# Introduction 
All of the DMA Power BI dataset reside in this repository. The repository is automatically synced to the Dev Dr martens dataset when merged to master.

## Power BI Reports:
Reports are located in `powerbi/reports`

Any reports that have custom partitions will have to be swapped out to enable you to open the report. 

I have create a cli tool to make this easier. To use this create a new virtual environment using poetry.

`poetry install`

You should then be able to use the cli tool to remove the custom partitions:

`pbi`

and run the following command to remove the original partition:

`pbi --no-original`

# Getting Started

# Contribute