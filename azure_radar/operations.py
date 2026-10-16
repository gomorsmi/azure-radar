import subprocess
from . import inventory, diagram, billing as billing_mod

def run_operations(billing=False, days=billing_mod.DEFAULT_DAYS, billing_output='azure_billing.csv'):
    """Run full operations: inventory, diagram and (optionally) billing using Azure CLI"""
    print("=== Azure Radar ===\n")
    
    # Check Azure CLI is available
    try:
        result = subprocess.run(['az', '--version'], capture_output=True, text=True)
        if result.returncode != 0:
            raise FileNotFoundError()
        print("✓ Azure CLI found\n")
    except FileNotFoundError:
        print("✗ Error: Azure CLI not found")
        print("  Install: https://docs.microsoft.com/cli/azure/install-azure-cli")
        return False
    
    # Check authentication
    try:
        subprocess.run(['az', 'account', 'show'], capture_output=True, text=True, check=True)
        print("✓ Azure authentication valid\n")
    except subprocess.CalledProcessError:
        print("✗ Error: Not authenticated to Azure")
        print("  Run: az login --use-device-code")
        return False
    
    # Run inventory
    print("--- Running Inventory ---")
    inventory.run_inventory()
    print()
    
    # Run diagram
    print("--- Generating Diagram ---")
    diagram.generate_diagram()
    print()
    
    # Run billing
    if billing:
        print("--- Pulling Billing Data ---")
        if not billing_mod.run_billing(days=days, output=billing_output):
            return False
        print()
    
    print("✓ Operations completed successfully")
    return True