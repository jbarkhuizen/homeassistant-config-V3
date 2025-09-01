#!/usr/bin/env python3
"""
Home Assistant Sensor Extraction Script
Creates comprehensive sensor documentation with status and details
"""

import requests
import json
import csv
from datetime import datetime
import os

# Configuration
HA_URL = "http://192.168.1.30:8123"
HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJkZWMzOTNlMWE3Mjc0ZTRmYTJkYjY2YmI3NDBlZjNjNiIsImlhdCI6MTc1NjcxNzY4MSwiZXhwIjoyMDcyMDc3NjgxfQ.Lw958tdXTVp23-EAh-36EjpeMV_jtB9cnX0_M3mTDl8"  # Create this in HA Profile
OUTPUT_DIR = "/config/sensor_reports"

# Headers for API requests
headers = {
    "Authorization": f"Bearer {HA_TOKEN}",
    "Content-Type": "application/json"
}

def get_all_entities():
    """Get all entities from Home Assistant"""
    url = f"{HA_URL}/api/states"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        return []

def extract_sensor_info(entity):
    """Extract relevant sensor information"""
    attributes = entity.get('attributes', {})
    
    return {
        'Entity ID': entity.get('entity_id'),
        'Friendly Name': attributes.get('friendly_name', 'N/A'),
        'State': entity.get('state'),
        'Unit': attributes.get('unit_of_measurement', 'N/A'),
        'Device Class': attributes.get('device_class', 'N/A'),
        'State Class': attributes.get('state_class', 'N/A'),
        'Icon': attributes.get('icon', 'N/A'),
        'Last Updated': entity.get('last_updated'),
        'Last Changed': entity.get('last_changed'),
        'Domain': entity.get('entity_id', '').split('.')[0],
        'Integration': attributes.get('attribution', 'N/A'),
        'Restored': attributes.get('restored', False),
        'Supported Features': attributes.get('supported_features', 'N/A')
    }

def main():
    print("🔍 Starting Home Assistant Sensor Extraction...")
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Get all entities
    entities = get_all_entities()
    if not entities:
        print("❌ Failed to retrieve entities")
        return
    
    # Filter and process sensors
    sensors = [entity for entity in entities if entity.get('entity_id', '').startswith('sensor.')]
    binary_sensors = [entity for entity in entities if entity.get('entity_id', '').startswith('binary_sensor.')]
    
    print(f"📊 Found {len(sensors)} sensors and {len(binary_sensors)} binary sensors")
    
    # Process sensors
    sensor_data = [extract_sensor_info(sensor) for sensor in sensors]
    binary_sensor_data = [extract_sensor_info(sensor) for sensor in binary_sensors]
    
    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export to CSV
    csv_file = f"{OUTPUT_DIR}/sensors_report_{timestamp}.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as file:
        if sensor_data:
            writer = csv.DictWriter(file, fieldnames=sensor_data[0].keys())
            writer.writeheader()
            writer.writerows(sensor_data)
            writer.writerows(binary_sensor_data)
    
    # Export to JSON
    json_file = f"{OUTPUT_DIR}/sensors_report_{timestamp}.json"
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump({
            'sensors': sensor_data,
            'binary_sensors': binary_sensor_data,
            'generation_time': datetime.now().isoformat(),
            'total_sensors': len(sensor_data),
            'total_binary_sensors': len(binary_sensor_data)
        }, file, indent=2, ensure_ascii=False)
    
    print(f"✅ Reports generated:")
    print(f"   📄 CSV: {csv_file}")
    print(f"   📄 JSON: {json_file}")
    
    # Generate summary
    generate_summary(sensor_data, binary_sensor_data, timestamp)

def generate_summary(sensors, binary_sensors, timestamp):
    """Generate a human-readable summary report"""
    summary_file = f"{OUTPUT_DIR}/sensors_summary_{timestamp}.md"
    
    # Group by domain/integration
    integrations = {}
    for sensor in sensors + binary_sensors:
        integration = sensor.get('Integration', 'Unknown')
        if integration not in integrations:
            integrations[integration] = []
        integrations[integration].append(sensor)
    
    with open(summary_file, 'w', encoding='utf-8') as file:
        file.write(f"# Home Assistant Sensor Report\n\n")
        file.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        file.write(f"**Total Sensors:** {len(sensors)}\n")
        file.write(f"**Total Binary Sensors:** {len(binary_sensors)}\n")
        file.write(f"**Total Entities:** {len(sensors) + len(binary_sensors)}\n\n")
        
        file.write("## Sensors by Integration\n\n")
        for integration, entities in sorted(integrations.items()):
            file.write(f"### {integration}\n")
            file.write(f"**Count:** {len(entities)}\n\n")
            
            file.write("| Entity ID | Friendly Name | State | Unit | Status |\n")
            file.write("|-----------|---------------|-------|------|--------|\n")
            
            for entity in entities[:10]:  # Limit to first 10 per integration
                status = "✅ OK" if entity['State'] not in ['unknown', 'unavailable'] else "❌ Issue"
                file.write(f"| `{entity['Entity ID']}` | {entity['Friendly Name']} | {entity['State']} | {entity['Unit']} | {status} |\n")
            
            if len(entities) > 10:
                file.write(f"| ... | *{len(entities) - 10} more entities* | ... | ... | ... |\n")
            
            file.write("\n")
    
    print(f"   📄 Summary: {summary_file}")

if __name__ == "__main__":
    main()