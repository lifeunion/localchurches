#!/usr/bin/env python3
"""
Run the fix_userprofile command on Render via Render API.
This script uses the Render API to execute the Django management command.
"""
import requests
import json
import sys
import os

# Render API token from MCP config
API_TOKEN = "rnd_xczni9ggi5bclCcOQwDIWn63sNud"
RENDER_API_BASE = "https://api.render.com/v1"

def get_services():
    """Get list of services to find the web service."""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }
    response = requests.get(f"{RENDER_API_BASE}/services", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching services: {response.status_code} - {response.text}")
        return None

def find_web_service(services):
    """Find the web service (not database)."""
    if not services:
        return None
    for service in services:
        if service.get('type') == 'web_service':
            return service
    return None

def execute_shell_command(service_id, command):
    """Execute a shell command on the Render service."""
    # Note: Render API doesn't directly support shell command execution
    # We need to use the Render Shell feature or trigger a deploy
    print("Render API doesn't support direct shell execution.")
    print("Alternative: We can trigger a deploy that runs the fix.")
    return None

def main():
    print("Connecting to Render API...")
    
    # Get services
    services = get_services()
    if not services:
        print("Could not fetch services. Check API token.")
        sys.exit(1)
    
    # Find web service
    web_service = find_web_service(services)
    if not web_service:
        print("Could not find web service.")
        sys.exit(1)
    
    print(f"Found service: {web_service.get('name')} (ID: {web_service.get('id')})")
    print("\nNote: Render API doesn't support direct shell command execution.")
    print("To run the fix, you have two options:")
    print("\n1. Use Render Dashboard Shell:")
    print("   - Go to https://dashboard.render.com")
    print(f"   - Navigate to service: {web_service.get('name')}")
    print("   - Click 'Shell' and run: python manage.py fix_userprofile")
    print("\n2. Trigger a deploy (fix runs automatically):")
    print("   - The build.sh script will run the fix on next deploy")
    
    # Try to get service details
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json"
    }
    service_id = web_service.get('id')
    response = requests.get(f"{RENDER_API_BASE}/services/{service_id}", headers=headers)
    if response.status_code == 200:
        service_details = response.json()
        print(f"\nService URL: {service_details.get('serviceDetails', {}).get('url', 'N/A')}")

if __name__ == '__main__':
    main()
