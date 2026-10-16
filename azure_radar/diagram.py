import json
import subprocess
import pandas as pd

def generate_diagram():
    """Generate draw.io diagram from Azure inventory"""
    try:
        # Load inventory if exists
        try:
            df = pd.read_csv('azure_inventory.csv')
        except FileNotFoundError:
            print("Inventory not found. Running inventory first...")
            from . import inventory
            inventory.run_inventory()
            df = pd.read_csv('azure_inventory.csv')
        
        # Count resources by service type
        service_counts = df['ServiceType'].value_counts().to_dict()
        
        # Generate draw.io XML
        xml = generate_drawio_xml(service_counts)
        
        with open('azure_diagram.drawio', 'w') as f:
            f.write(xml)
        
        print("Diagram saved to azure_diagram.drawio")
        return True
        
    except Exception as e:
        print(f"Error generating diagram: {e}")
        return False

def generate_drawio_xml(service_counts):
    """Generate draw.io XML with Azure services"""
    xml = '''<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2026-05-18T00:00:00.000Z" agent="azure-radar" version="15.8.7" type="device">
  <diagram id="diagram1" name="Azure Services">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1100" pageHeight="850" math="0" shadow="0">
      <root>
        <mxCell id="0"/>
        <mxCell id="1" parent="0"/>
        <mxCell id="title" value="Azure Services Inventory" style="text;html=1;fontSize=18;fontStyle=1;verticalAlign=middle;" vertex="1" parent="1">
          <mxGeometry x="400" y="20" width="300" height="40" as="geometry"/>
        </mxCell>
'''
    
    y = 100
    colors = {
        'Virtual Machines': '#FF6B6B',
        'Azure SQL': '#4ECDC4',
        'Azure Functions': '#45B7D1',
        'AKS': '#96CEB4',
        'Storage Accounts': '#FFEAA7',
        'Container Apps': '#DDA0DD',
        'Cosmos DB': '#F8B88B',
        'Service Bus': '#B4A7D6',
        'Azure ML': '#A8E6CF',
    }
    
    for service_type, count in sorted(service_counts.items()):
        color = colors.get(service_type, '#CCCCCC')
        
        xml += f'''        <mxCell id="service_{service_type.replace(' ', '_')}" value="{service_type}&#xa;({count} resources)" style="rounded=1;whiteSpace=wrap;html=1;fillColor={color};fontSize=12;fontStyle=1;" vertex="1" parent="1">
          <mxGeometry x="50" y="{y}" width="200" height="60" as="geometry"/>
        </mxCell>
'''
        y += 80
    
    xml += '''      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    
    return xml