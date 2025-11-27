Param(
    [string]$ResourceGroup = "finance-diag-rg",
    [string]$Region = "westeurope",
    [string]$AppName = "finance-diag-" + ([System.Guid]::NewGuid().ToString().Substring(0,8))
)

Write-Host "Logging in to Azure..." -ForegroundColor Cyan
az login | Out-Null

Write-Host "Creating resource group $ResourceGroup in $Region..." -ForegroundColor Cyan
az group create --name $ResourceGroup --location $Region | Out-Null

Write-Host "Creating Linux App Service plan..." -ForegroundColor Cyan
az appservice plan create --resource-group $ResourceGroup --name "$AppName-plan" --sku B1 --is-linux --location $Region | Out-Null

Write-Host "Creating Web App $AppName..." -ForegroundColor Cyan
az webapp create --resource-group $ResourceGroup --plan "$AppName-plan" --name $AppName --runtime "PYTHON:3.11" | Out-Null

$secretKey = [Guid]::NewGuid().ToString()
Write-Host "Configuring app settings (APP_SECRET_KEY, SCM_DO_BUILD_DURING_DEPLOYMENT)..." -ForegroundColor Cyan
az webapp config appsettings set --resource-group $ResourceGroup --name $AppName --settings APP_SECRET_KEY="$secretKey" SCM_DO_BUILD_DURING_DEPLOYMENT=true | Out-Null

Write-Host "Deploying current folder to Azure Web App..." -ForegroundColor Cyan
az webapp up --name $AppName --resource-group $ResourceGroup --runtime "PYTHON:3.11" --sku B1 --logs

$url = az webapp show --resource-group $ResourceGroup --name $AppName --query defaultHostName -o tsv
Write-Host "Deployment complete: https://$url" -ForegroundColor Green
