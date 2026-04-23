# Personal Finance Diagnostics MVP

An MVP web app that analyzes personal finance data and provides diagnostics, alerts, and actionable recommendations. Built with Flask + Pandas; charts powered by Plotly.

## Features

- Upload CSVs for transactions and accounts
- Automated analytics: income vs expenses, savings rate, overspending categories
- Emergency fund progress check
- Dashboard with charts and recommendations
- Session-based authentication with SQLite user store
- Health check endpoint for monitoring
- **Dynamic Questionnaire**: JSON-based questionnaire system for gathering additional financial information

## Questionnaire System

The app includes a flexible, bilingual questionnaire system (English + Portuguese) that allows clients to provide comprehensive financial information.

### JSON Configuration

Questionnaires are defined in `questionnaire.json` with the following structure:

```json
{
  "questionnaire": {
    "title": "Financial Analysis Questionnaire / Questionário de Análise Financeira",
    "description": "Bilingual form for financial analysis (English + Portuguese).",
    "questions": [
      {
        "id": "full_name",
        "category": "Personal Information",
        "question": "Full Name / Nome Completo",
        "type": "text",
        "required": true
      }
    ]
  }
}
```

### Supported Question Types

- `text`: Free-form text input (single line or paragraph)
- `single_choice`: Radio buttons for single selection
- `multiple_choice`: Checkboxes for multiple selections
- `yes_no`: Yes/No radio buttons

### Questionnaire Categories

- **Personal Information**: Basic personal details
- **Contact Information**: Email and phone
- **Family Information**: Marital status and dependents
- **Employment**: Job status and details
- **Income**: Salary and additional sources
- **Expenses**: Fixed and variable costs
- **Debts**: Liabilities and obligations
- **Assets**: Savings and investments
- **Habits**: Financial behavior patterns
- **Goals**: Financial objectives
- **Concerns**: Challenges and worries
- **Additional**: Extra information

### API Endpoints

- `GET /api/questionnaire`: Returns the questionnaire JSON
- `POST /api/questionnaire/responses`: Submits questionnaire responses
- `GET /questionnaire/client`: Client-side questionnaire interface

### Usage

1. Edit `questionnaire.json` to customize questions
2. Access `/questionnaire/client` for the interactive bilingual form
3. Responses are stored in user session for analysis
4. Use `process_questionnaire_responses.py` to export and analyze collected data

### Response Processing

The `process_questionnaire_responses.py` script provides tools to:

- Export responses to CSV format for spreadsheet analysis
- Export responses to JSON format for programmatic processing
- Analyze completion rates and response patterns
- Generate basic insights from questionnaire data

Example usage:
```python
from process_questionnaire_responses import export_responses_to_csv, analyze_responses

# Export session responses to CSV
csv_file = export_responses_to_csv(session['questionnaire_responses'])

# Get analysis insights
analysis = analyze_responses(session['questionnaire_responses'])
print(f"Completion rate: {analysis['completion_rate']:.1f}%")
```

## Data Format

Transactions CSV: `date,type,category,amount,description` (`type` is `income` or `expense`).

Accounts CSV: `account,type,balance` (`type`: `cash`, `savings`, or `investment`).

Sample files in `data/sample/`.

## Run Locally (Windows PowerShell)

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:APP_SECRET_KEY="local-dev-change-me"
python app.py
```

Open <http://localhost:5000> in your browser.

## Deploy to Azure App Service (CLI)

Option 1: Scripted

```powershell
./deploy.ps1 -ResourceGroup finance-diag-rg -Region westeurope -AppName finance-diag-<yourtag>
```

Option 2: Manual

```powershell
$rg="finance-diag-rg"
$region="westeurope"
$appName="finance-diag-<yourtag>"

az login
az group create --name $rg --location $region
az appservice plan create --resource-group $rg --name "$appName-plan" --sku B1 --is-linux --location $region
az webapp create --resource-group $rg --plan "$appName-plan" --name $appName --runtime "PYTHON:3.11"
az webapp config appsettings set --resource-group $rg --name $appName --settings APP_SECRET_KEY="<rotate-this>" SCM_DO_BUILD_DURING_DEPLOYMENT=true
az webapp up --name $appName --resource-group $rg --runtime "PYTHON:3.11" --sku B1 --logs
```

### CI/CD with GitHub Actions

Add repository secrets:

- `AZURE_CREDENTIALS`: JSON from `az ad sp create-for-rbac` (App Service deploy perms)
- `AZURE_WEBAPP_NAME`: your web app name
- `AZURE_RESOURCE_GROUP`: your resource group

Workflow file: `.github/workflows/azure-deploy.yml` deploys on pushes to `main`.

### Key Vault (production)

Store secrets in Azure Key Vault via Managed Identity. Enable Managed Identity on the Web App and grant Key Vault `get` permissions.

App settings for Key Vault-backed secret:

```powershell
az webapp identity assign --resource-group $rg --name $appName
$principalId = az webapp show --resource-group $rg --name $appName --query identity.principalId -o tsv
az keyvault set-policy --name <kv-name> --resource-group <kv-rg> --object-id $principalId --secret-permissions get list
az webapp config appsettings set --resource-group $rg --name $appName --settings KEYVAULT_URL="https://<kv-name>.vault.azure.net/" KEYVAULT_APP_SECRET_NAME="APP_SECRET_KEY"
```

## Notes

This MVP uses simple heuristics and dummy benchmarks. In production, add proper authentication, encryption at rest/in-transit, and GDPR-compliant data handling.
