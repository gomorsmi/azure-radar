"""Pull daily cost data from Azure Cost Management via the Azure CLI."""

import json
import os
import subprocess
from datetime import date, timedelta

import pandas as pd

from .inventory import normalize_service_type

API_VERSION = '2023-11-01'
ARM_ENDPOINT = 'https://management.azure.com'

# Supported lookback windows, in days
ALLOWED_DAYS = (30, 60, 90)
DEFAULT_DAYS = 30

# Cost metric name differs by agreement type (MCA uses Cost, EA/PAYG uses PreTaxCost)
COST_METRICS = ('Cost', 'PreTaxCost')

MAX_PAGES = 200


def get_subscription_id():
    """Resolve the subscription ID from the environment or Azure CLI"""
    subscription_id = os.getenv('AZURE_SUBSCRIPTION_ID')
    if subscription_id:
        return subscription_id

    result = subprocess.run(
        ['az', 'account', 'show', '--query', 'id', '-o', 'tsv'],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout.strip()


def build_dataset_filter(services=None, resource_groups=None):
    """Build a Cost Management filter clause for services and resource groups"""
    clauses = []

    if services:
        clauses.append({
            'dimensions': {
                'name': 'ServiceName',
                'operator': 'In',
                'values': list(services),
            }
        })

    if resource_groups:
        clauses.append({
            'dimensions': {
                'name': 'ResourceGroupName',
                'operator': 'In',
                'values': list(resource_groups),
            }
        })

    if not clauses:
        return None
    if len(clauses) == 1:
        return clauses[0]
    return {'and': clauses}


def build_payload(start, end, cost_metric, cost_type='ActualCost',
                  services=None, resource_groups=None):
    """Build the Cost Management query body: daily granularity, grouped by service and resource"""
    dataset = {
        'granularity': 'Daily',
        'aggregation': {
            'totalCost': {'name': cost_metric, 'function': 'Sum'},
        },
        'grouping': [
            {'type': 'Dimension', 'name': 'ServiceName'},
            {'type': 'Dimension', 'name': 'ResourceId'},
        ],
    }

    dataset_filter = build_dataset_filter(services, resource_groups)
    if dataset_filter:
        dataset['filter'] = dataset_filter

    return {
        'type': cost_type,
        'timeframe': 'Custom',
        'timePeriod': {
            'from': f'{start.isoformat()}T00:00:00+00:00',
            'to': f'{end.isoformat()}T23:59:59+00:00',
        },
        'dataset': dataset,
    }


def _post(url, payload):
    """POST a JSON body to ARM through 'az rest'"""
    result = subprocess.run(
        [
            'az', 'rest',
            '--method', 'post',
            '--url', url,
            '--headers', 'Content-Type=application/json',
            '--body', json.dumps(payload),
            '--only-show-errors',
            '-o', 'json',
        ],
        capture_output=True,
        text=True,
        check=True
    )
    return json.loads(result.stdout or '{}')


def query_cost_management(subscription_id, payload):
    """Run a Cost Management query, following nextLink pagination"""
    url = (f'{ARM_ENDPOINT}/subscriptions/{subscription_id}'
           f'/providers/Microsoft.CostManagement/query?api-version={API_VERSION}')

    columns = []
    rows = []
    seen_links = set()
    pages = 0

    while url and pages < MAX_PAGES:
        body = _post(url, payload)
        props = body.get('properties') or body

        if not columns:
            columns = props.get('columns') or []
        rows.extend(props.get('rows') or [])

        pages += 1
        url = props.get('nextLink')
        if url and url in seen_links:
            break
        if url:
            seen_links.add(url)

    if url:
        print(f'Warning: stopped after {MAX_PAGES} pages; results may be incomplete')

    return columns, rows


def parse_resource_id(resource_id):
    """Split an ARM resource ID into resource group, type and name"""
    empty = {'ResourceGroup': '', 'ResourceType': '', 'ResourceName': ''}
    if not resource_id:
        return empty

    parts = [p for p in str(resource_id).split('/') if p]
    lowered = [p.lower() for p in parts]

    resource_group = ''
    if 'resourcegroups' in lowered:
        idx = lowered.index('resourcegroups')
        if idx + 1 < len(parts):
            resource_group = parts[idx + 1]

    resource_type = ''
    resource_name = parts[-1] if parts else ''
    if 'providers' in lowered:
        idx = lowered.index('providers')
        tail = parts[idx + 1:]
        if len(tail) >= 2:
            # namespace/type[/subtype...] with names interleaved after the first pair
            namespace = tail[0]
            segments = tail[1::2]
            resource_type = '/'.join([namespace] + segments)

    return {
        'ResourceGroup': resource_group,
        'ResourceType': resource_type,
        'ResourceName': resource_name,
    }


def _column_index(columns, name):
    """Find a column position by (case-insensitive) name"""
    for i, column in enumerate(columns):
        if str(column.get('name', '')).lower() == name.lower():
            return i
    return None


def _parse_usage_date(value):
    """Cost Management returns UsageDate as an integer like 20260819"""
    text = str(value).strip()
    try:
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8])).isoformat()
    except (ValueError, IndexError):
        return text


def rows_to_records(columns, rows, subscription_id, cost_metric):
    """Turn the columns/rows response into flat CSV records"""
    cost_idx = _column_index(columns, cost_metric)
    date_idx = _column_index(columns, 'UsageDate')
    service_idx = _column_index(columns, 'ServiceName')
    resource_idx = _column_index(columns, 'ResourceId')
    currency_idx = _column_index(columns, 'Currency')

    records = []
    for row in rows:
        def cell(idx, default=''):
            if idx is None or idx >= len(row):
                return default
            value = row[idx]
            return default if value is None else value

        resource_id = cell(resource_idx)
        parsed = parse_resource_id(resource_id)
        service_name = cell(service_idx)

        records.append({
            'Date': _parse_usage_date(cell(date_idx)),
            'ServiceName': service_name,
            'ServiceType': normalize_service_type(parsed['ResourceType'] or service_name),
            'ResourceName': parsed['ResourceName'],
            'ResourceGroup': parsed['ResourceGroup'],
            'ResourceType': parsed['ResourceType'],
            'ResourceId': resource_id,
            'Cost': cell(cost_idx, 0.0),
            'Currency': cell(currency_idx),
            'SubscriptionId': subscription_id,
        })

    return records


def _print_summary(df):
    """Print totals and the top spending services"""
    if df.empty:
        return

    for currency, group in df.groupby(df['Currency'].replace('', 'unknown')):
        print(f'  Total: {group["Cost"].sum():,.2f} {currency}')

    top = df.groupby('ServiceName')['Cost'].sum().sort_values(ascending=False).head(5)
    if not top.empty:
        print('  Top services:')
        for service_name, cost in top.items():
            print(f'    - {service_name or "(unattributed)"}: {cost:,.2f}')


def run_billing(days=DEFAULT_DAYS, output='azure_billing.csv', cost_type='ActualCost',
                services=None, resource_groups=None):
    """Pull daily cost data grouped by service and resource, and write it to CSV"""
    if days not in ALLOWED_DAYS:
        allowed = ', '.join(str(d) for d in ALLOWED_DAYS)
        print(f'Error: --days must be one of {allowed} (got {days})')
        return False

    end = date.today()
    start = end - timedelta(days=days - 1)

    try:
        subscription_id = get_subscription_id()
        if not subscription_id:
            print("Error: Could not determine subscription ID. Set AZURE_SUBSCRIPTION_ID or run 'az login'")
            return False

        print(f'Using subscription: {subscription_id}')
        print(f'Cost window: {start.isoformat()} to {end.isoformat()} ({days} days, daily granularity, {cost_type})')
        if services:
            print(f'  Filtered to services: {", ".join(services)}')
        if resource_groups:
            print(f'  Filtered to resource groups: {", ".join(resource_groups)}')

        columns = rows = None
        last_error = None
        for cost_metric in COST_METRICS:
            payload = build_payload(start, end, cost_metric, cost_type, services, resource_groups)
            try:
                columns, rows = query_cost_management(subscription_id, payload)
                break
            except subprocess.CalledProcessError as e:
                # Agreement type decides which cost metric is valid; try the next one
                last_error = e
                columns = rows = None

        if columns is None:
            print(f'Error querying Cost Management: {(last_error.stderr or "").strip()}')
            print("  Cost data requires the 'Cost Management Reader' role on the subscription.")
            return False

        records = rows_to_records(columns, rows, subscription_id, cost_metric)

        df = pd.DataFrame(records, columns=[
            'Date', 'ServiceName', 'ServiceType', 'ResourceName', 'ResourceGroup',
            'ResourceType', 'ResourceId', 'Cost', 'Currency', 'SubscriptionId',
        ])
        if not df.empty:
            df['Cost'] = pd.to_numeric(df['Cost'], errors='coerce').fillna(0.0)
            df = df.sort_values(['Date', 'Cost'], ascending=[True, False])

        df.to_csv(output, index=False)
        print(f'Billing data saved to {output} ({len(df)} rows)')
        _print_summary(df)
        return True

    except subprocess.CalledProcessError as e:
        print(f'Error running Azure CLI: {(e.stderr or "").strip()}')
        return False
    except FileNotFoundError:
        print('Error: Azure CLI not found. Please install it: https://docs.microsoft.com/cli/azure/install-azure-cli')
        return False
