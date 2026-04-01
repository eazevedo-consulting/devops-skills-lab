# Azure Infrastructure-on-Demand Portal

A self-service portal for deploying Azure resources using Terraform with an approval workflow.

## Overview

1.  **UI**: Simple frontend for non-technical users to request infrastructure.
2.  **API**: FastAPI backend that stores requests in SQLite and handles approvals/rejections.
3.  **Terraform**: Modularized Azure configuration for Resource Groups, Networking, Storage, and VMs.
4.  **GHA**: GitHub Actions workflow that performs the actual deployment using GitHub Secrets.

## Setup Guide

### 1. Azure Service Principal
Create an Azure Service Principal for Terraform:
```bash
az ad sp create-for-rbac --name "iac-on-demand-sp" --role Contributor --scopes /subscriptions/<sub_id>
```

### 2. GitHub Secrets
Add the following secrets to your GitHub repository:
- `ARM_CLIENT_ID`
- `ARM_CLIENT_SECRET`
- `ARM_SUBSCRIPTION_ID`
- `ARM_TENANT_ID`
- `TF_BACKEND_RG` (Resource Group for TF state)
- `TF_BACKEND_SA` (Storage Account for TF state)

### 3. Run the API locally
```bash
cd api
pip install -r requirements.txt
python main.py
```

### 4. Open the UI
Open `ui/index.html` in your browser.

## Workflow Example
1.  **User**: Fills the form in the UI (e.g., Environment: `prod-data`, Region: `West Europe`, Type: `Storage Account`).
2.  **User**: Submits the request.
3.  **Admin**: Views the "Recent Requests" section in the UI.
4.  **Admin**: Clicks **Approve**.
5.  **System**: Updates SQLite status and (optionally) triggers the GitHub Actions workflow via `workflow_dispatch`.
6.  **GHA**: Initializes Terraform, plans the changes, and applies them to Azure.
