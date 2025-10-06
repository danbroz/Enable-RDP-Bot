#!/bin/bash

# Cleanup Test Case 9: RDP Rule with Wrong Destination
# This script cleans up the resources created by create_test9.sh

set -e

# Configuration
RESOURCE_GROUP="test9-resource-group"

echo "🧹 Cleanup Test Case 9: RDP Rule with Wrong Destination"
echo "======================================================="
echo "This script will clean up all resources created for Test Case 9"
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
echo "   - Virtual Machine (test9-vm)"
echo "   - Network Security Group (test9-vm-nsg)"
echo "   - Network Interface (test9-vm-nic)"
echo "   - Public IP Address (test9-vm-pip)"
echo "   - Virtual Network (test9-vm-vnet)"
echo ""

# Delete the resource group (this will delete all resources in it)
az group delete --name $RESOURCE_GROUP --yes --no-wait

echo "✅ Cleanup initiated for Test Case 9"
echo "Resource group deletion is in progress..."
echo "You can check the status with: az group show --name $RESOURCE_GROUP"
echo ""
echo "🎉 Test Case 9 cleanup completed!"
