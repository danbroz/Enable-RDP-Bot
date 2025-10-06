#!/bin/bash

# Enable RDP Bot - Azure CLI Script to Clean Up Example VM
# This script removes the test VM and all associated resources

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="example-resource-group"

echo -e "${BLUE}🧹 Enable RDP Bot - Cleaning Up Example VM${NC}"
echo "=============================================="
echo "This script will remove the test VM and all associated resources."
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed.${NC}"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Check if resource group exists
if ! az group show --name $RESOURCE_GROUP &> /dev/null; then
    echo -e "${YELLOW}⚠️  Resource group '$RESOURCE_GROUP' does not exist.${NC}"
    echo "Nothing to clean up."
    exit 0
fi

echo -e "${YELLOW}⚠️  This will delete the resource group '$RESOURCE_GROUP' and ALL resources in it.${NC}"
echo "This includes:"
echo "  - Virtual Machine"
echo "  - Network Security Group"
echo "  - Virtual Network"
echo "  - Public IP Address"
echo "  - Network Interface"
echo "  - All other resources in the resource group"
echo ""

# Ask for confirmation
read -p "Are you sure you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}❌ Cleanup cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🗑️  Deleting resource group: $RESOURCE_GROUP${NC}"

# Delete the entire resource group (this removes all resources)
az group delete \
    --name $RESOURCE_GROUP \
    --yes \
    --no-wait

echo -e "${GREEN}✅ Resource group deletion initiated${NC}"
echo ""
echo -e "${BLUE}📋 Cleanup Summary:${NC}"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Status: Deletion in progress"
echo "   Note: This may take a few minutes to complete"
echo ""
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo "The example VM and all associated resources are being removed."
echo ""
echo -e "${YELLOW}💡 Tip: You can check the deletion status with:${NC}"
echo "   az group show --name $RESOURCE_GROUP"
