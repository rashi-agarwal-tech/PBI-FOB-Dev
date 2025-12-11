# FOB Power BI Reports

This folder contains Power BI reports and semantic models for the FOB project.

## Structure

When you save a Power BI report (`.pbip` format) to this folder, it will create:

```
fob/
├── YourReportName.Report/
│   ├── definition.pbir
│   ├── report.json
│   └── StaticResources/
│       └── RegisteredResources/
└── YourReportName.SemanticModel/
    ├── definition.pbism
    └── definition/
        ├── database.tmdl
        ├── model.tmdl
        ├── tables/
        └── ...
```

## Workflow

1. **Development**: Make changes in Power BI Desktop, save to this folder
2. **Version Control**: Commit and push changes to GitHub
3. **Review**: Create a Pull Request for review
4. **Merge**: Once approved, merge to main branch
5. **Auto-Sync**: FOB DEV workspace on powerbi.com syncs automatically
6. **Promotion**: Use Power BI Deployment Pipeline to promote:
   - FOB DEV → FOB UAT (manual)
   - FOB UAT → FOB PROD (manual)

## Power BI Desktop Settings

Before saving reports, ensure these settings are enabled in Power BI Desktop:
- `File → Options and settings → Options → Preview features`
- ✅ Store semantic model using TMDL format
- ✅ Power BI Project (.pbip) save option

## Connected Workspace

| Environment | Workspace | Git Branch |
|-------------|-----------|------------|
| DEV | FOB DEV | main |
| UAT | FOB UAT | (via Deployment Pipeline) |
| PROD | FOB PROD | (via Deployment Pipeline) |

