import json
import subprocess
import os
import pandas as pd

def run_inventory():
    """Run inventory using Azure CLI"""
    try:
        # Get subscription ID
        subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            result = subprocess.run(
                ['az', 'account', 'show', '--query', 'id', '-o', 'tsv'],
                capture_output=True,
                text=True,
                check=True
            )
            subscription_id = result.stdout.strip()
        
        if not subscription_id:
            print("Error: Could not determine subscription ID. Set AZURE_SUBSCRIPTION_ID or run 'az login'")
            return
        
        print(f"Using subscription: {subscription_id}")
        
        # Get all resources
        result = subprocess.run(
            ['az', 'resource', 'list', '--query', '[*].[name, type, resourceGroup, location]', '-o', 'json'],
            capture_output=True,
            text=True,
            check=True
        )
        
        resources_raw = json.loads(result.stdout)
        
        resources = []
        for item in resources_raw:
            name, res_type, rg, location = item
            # Normalize service type
            service_type = normalize_service_type(res_type)
            resources.append({
                'Name': name,
                'Type': res_type,
                'ServiceType': service_type,
                'ResourceGroup': rg,
                'Location': location,
            })
        
        df = pd.DataFrame(resources)
        df.to_csv('azure_inventory.csv', index=False)
        print(f"Inventory saved to azure_inventory.csv ({len(resources)} resources)")
        
    except subprocess.CalledProcessError as e:
        print(f"Error running Azure CLI: {e.stderr}")
        return
    except FileNotFoundError:
        print("Error: Azure CLI not found. Please install it: https://docs.microsoft.com/cli/azure/install-azure-cli")
        return

def normalize_service_type(resource_type):
    """Map Azure resource types to service mappings"""
    type_lower = resource_type.lower()
    
    mappings = {
        'microsoft.compute/virtualmachines': 'Virtual Machines',
        'microsoft.sql/servers/databases': 'Azure SQL',
        'microsoft.web/functions': 'Azure Functions',
        'microsoft.containerservice/managedclusters': 'AKS',
        'microsoft.storage/storageaccounts': 'Storage Accounts',
        'microsoft.app/containerapps': 'Container Apps',
        'microsoft.documentdb/databaseaccounts': 'Cosmos DB',
        'microsoft.servicebus/namespaces': 'Service Bus',
        'microsoft.machinelearningservices/workspaces': 'Azure ML',
    }
    
    return mappings.get(type_lower, resource_type)