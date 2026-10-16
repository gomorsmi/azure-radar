from typing import List, Optional

import typer

from . import (
    inventory as inv_mod,
    diagram as dia_mod,
    operations as ops_mod,
    billing as bil_mod,
)

app = typer.Typer()

DAYS_HELP = 'Lookback window in days: 30 (default), 60 or 90'

@app.command()
def inventory():
    """Inventory Azure services"""
    inv_mod.run_inventory()

@app.command()
def diagram():
    """Generate diagram of Azure services"""
    dia_mod.generate_diagram()

@app.command()
def billing(
    days: int = typer.Option(bil_mod.DEFAULT_DAYS, '--days', '-d', help=DAYS_HELP),
    output: str = typer.Option('azure_billing.csv', '--output', '-o', help='CSV output file'),
    cost_type: str = typer.Option('ActualCost', '--cost-type',
                                  help='ActualCost or AmortizedCost'),
    service: Optional[List[str]] = typer.Option(None, '--service',
                                                help='Only include this service name (repeatable)'),
    resource_group: Optional[List[str]] = typer.Option(None, '--resource-group',
                                                       help='Only include this resource group (repeatable)'),
):
    """Pull daily cost data from Azure Cost Management to CSV"""
    bil_mod.run_billing(
        days=days,
        output=output,
        cost_type=cost_type,
        services=service,
        resource_groups=resource_group,
    )

@app.command()
def run(
    billing: bool = typer.Option(False, '--billing',
                                 help='Also pull daily cost data from Cost Management'),
    days: int = typer.Option(bil_mod.DEFAULT_DAYS, '--days', '-d', help=DAYS_HELP),
    billing_output: str = typer.Option('azure_billing.csv', '--billing-output',
                                       help='CSV output file for billing data'),
):
    """Run operations on Azure services"""
    ops_mod.run_operations(
        billing=billing,
        days=days,
        billing_output=billing_output,
    )

def main():
    app()
