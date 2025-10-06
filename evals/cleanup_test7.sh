#!/bin/bash

# Cleanup Test Case 7: RDP Rule with Restricted Source IP
# This script cleans up the resources created by create_test7.sh

set -e

# Configuration
RESOURCE_GROUP="test7-resource-group"

echo "🧹 Cleanup Test Case 7: RDP Rule with Restricted Source IP"
echo "=========================================================="
echo "This script will clean up all resources created for Test Case 7"
echo ""

# Check if Azure CLI is logged in
if ! az account show &> /dev/null; then
    echo "❌ Error: Not logged in to Azure CLI"
    echo "Please run 'az login' first"
    exit 1
fi

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo "ℹ️  Resource group $RESOURCE_GROUP does not exist. Nothing to clean up."
    exit 0
fi

echo "🗑️  Deleting resource group: $RESOURCE_GROUP"
echo "This will delete all resources in the resource group including:"
echo "   - Virtual Machine (test7-vm)"
echo "   - Network Security Group (test7-vm-nsg)"
echo "   - Network Interface (test7-vm-nic)"
echo "   - Public IP Address (test7-vm-pip)"
echo "   - Virtual Network (test7-vm-vnet)"
echo ""

# Delete the resource group (this will delete all resources in it)
az group delete --name $RESOURCE_GROUP --yes --no-wait

echo "✅ Cleanup initiated for Test Case 7"
echo "Resource group deletion is in progress..."
echo "You can check the status with: az group show --name $RESOURCE_GROUP"
echo ""
echo "🎉 Test Case 7 cleanup completed!"
