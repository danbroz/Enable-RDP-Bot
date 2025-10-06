#!/usr/bin/env python3
"""
Test Azure CLI authentication instead of service principal
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from azure.identity import AzureCliCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient

async def test_azure_cli_auth():
    """Test Azure CLI authentication"""
    
    subscription_id = "your-subscription-id-here"
    
    print("🔐 Testing Azure CLI Authentication")
    print("=" * 50)
    
    try:
        # Try Azure CLI credential
        credential = AzureCliCredential()
        
        # Test with a simple resource group list
        resource_client = ResourceManagementClient(credential, subscription_id)
        
        print("📋 Attempting to list resource groups...")
        resource_groups = list(resource_client.resource_groups.list())
        
        print(f"✅ Successfully authenticated! Found {len(resource_groups)} resource groups:")
        for rg in resource_groups[:5]:  # Show first 5
            print(f"   - {rg.name} ({rg.location})")
        
        if len(resource_groups) > 5:
            print(f"   ... and {len(resource_groups) - 5} more")
            
        return True
        
    except Exception as e:
        print(f"❌ Azure CLI authentication failed: {str(e)}")
        print("\n🔧 To fix this:")
        print("1. Install Azure CLI: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash")
        print("2. Login: az login")
        print("3. Set subscription: az account set --subscription your-subscription-id-here")
        return False

if __name__ == "__main__":
    asyncio.run(test_azure_cli_auth())
