# azure-radar

A CLI tool to inventory, diagram, and run operations on Azure services using Azure CLI, mirroring gcp-radar for GCP.

## Requirements

- **Azure CLI**: Install from https://docs.microsoft.com/cli/azure/install-azure-cli
- **Python 3.8+**

## Installation

```bash
pip install azure-radar
```

## Authentication

This tool uses Azure CLI for authentication, supporting various methods including SSO.

### For SSO-enabled accounts:

1. **Install Azure CLI** (if not already installed):
   ```bash
   brew install azure-cli  # macOS
   # or use appropriate installer for your OS
   ```

2. **Authenticate with SSO**:
   ```bash
   az login --use-device-code
   # or if browser available
   az login
   ```

3. **Set subscription** (if you have multiple):
   ```bash
   az account set --subscription <subscription-id>
   # or export it
   export AZURE_SUBSCRIPTION_ID=<your-subscription-id>
   ```

## Usage

```bash
# Generate CSV inventory of all Azure resources
azure-radar inventory

# Generate draw.io diagram of services
azure-radar diagram

# Run both inventory and diagram
azure-radar run

# Pull the last 30 days of cost data to CSV
azure-radar billing

# ...or fold billing into the full run
azure-radar run --billing
```

### Billing

`azure-radar billing` queries the Azure Cost Management API (via `az rest`) and writes
**daily** cost rows broken down by **service** and **resource**.

```bash
# Last 30 days (default)
azure-radar billing

# Last 60 or 90 days
azure-radar billing --days 60
azure-radar billing --days 90

# Custom output file
azure-radar billing --days 90 --output q3-spend.csv

# Amortized instead of actual cost (spreads reservation/savings-plan purchases)
azure-radar billing --cost-type AmortizedCost

# Narrow to specific services and/or resource groups (both repeatable)
azure-radar billing --service "Virtual Machines" --service "Storage" --resource-group rg-prod

# Same options are available on the full run
azure-radar run --billing --days 90 --billing-output spend.csv
```

| Option | Default | Description |
|--------|---------|-------------|
| `--days`, `-d` | `30` | Lookback window — must be `30`, `60`, or `90` |
| `--output`, `-o` | `azure_billing.csv` | CSV output file |
| `--cost-type` | `ActualCost` | `ActualCost` or `AmortizedCost` |
| `--service` | *(all)* | Filter to a service name; repeat for several |
| `--resource-group` | *(all)* | Filter to a resource group; repeat for several |

The CSV contains one row per day / service / resource:

| Column | Description |
|--------|-------------|
| `Date` | Usage day (`YYYY-MM-DD`) |
| `ServiceName` | Cost Management service name |
| `ServiceType` | Normalized service name, matching `azure_inventory.csv` |
| `ResourceName` | Resource name parsed from the resource ID |
| `ResourceGroup` | Resource group parsed from the resource ID |
| `ResourceType` | ARM type, e.g. `Microsoft.Compute/virtualMachines` |
| `ResourceId` | Full ARM resource ID |
| `Cost` | Cost for that day |
| `Currency` | Billing currency |
| `SubscriptionId` | Subscription the cost belongs to |

Because `ServiceType` is normalized the same way as the inventory output, the two CSVs
can be joined on `ServiceType` (or on resource name/group) for cost-per-service reporting.

> **Permissions:** reading cost data requires the **Cost Management Reader** role (or
> higher) on the subscription, which is separate from the reader role used by `inventory`.

### Output Files

- `azure_inventory.csv` - CSV file with all Azure resources
- `azure_diagram.drawio` - Draw.io diagram of service distribution
- `azure_billing.csv` - CSV file with daily costs per service and resource (with `billing` / `--billing`)

## Supported Azure Services

This tool currently supports the following Azure service categories for inventory and diagram generation:

- Virtual Machines
- Azure SQL
- Azure Functions
- AKS
- Storage Accounts
- Container Apps
- Cosmos DB
- Service Bus
- Azure ML

## Cloud Service Mapping (Azure → AWS → GCP → OCI)

| Azure | AWS | GCP | OCI |
|-------|-----|-----|-----|
| Virtual Machines | EC2 | Compute Engine | OCI Compute |
| Azure SQL | RDS | Cloud SQL | Autonomous Database |
| Azure Functions | Lambda | Cloud Functions | OCI Functions |
| AKS | EKS | GKE | Container Engine for Kubernetes |
| Storage Accounts | S3 | Cloud Storage | Object Storage |
| Container Apps | App Runner | Cloud Run | Container Instances |
| Cosmos DB | DynamoDB | Firestore | NoSQL Database |
| Service Bus | SNS/SQS | Pub/Sub | Streaming Service |
| Azure ML | SageMaker | Vertex AI | Data Science |

## Related PyPI packages

This project is part of a family of "radars" tools available on PyPI. Two related packages you may find useful:

- `aws-radar` — available on PyPI (example versions: 0.1.1, 0.1.0)
- `gcp-radar` — available on PyPI (example versions: 0.1.9, 0.1.3, 0.1.1, 0.1.0)

Install them with pip:

```bash
pip install aws-radar
pip install gcp-radar
```

These packages follow a similar CLI shape (inventory, diagram, run) for their respective clouds.