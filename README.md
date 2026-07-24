# azure-radar

A CLI tool to inventory, diagram, and run operations on Azure services using Azure CLI, mirroring gcp-radar for GCP.

## Requirements

- **Azure CLI**: Install from https://docs.microsoft.com/cli/azure/install-azure-cli
- **Python 3.8+**

## Installation

```bash
pip install -e .
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
```

### Output Files

- `azure_inventory.csv` - CSV file with all Azure resources
- `azure_diagram.drawio` - Draw.io diagram of service distribution

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