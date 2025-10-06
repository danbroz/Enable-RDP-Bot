#!/bin/bash

# Enable RDP Bot - Azure CLI Script to Create Example VM
# This script creates a Windows VM with intentional RDP issues for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="test-rg"
VM_NAME="example-vm"
LOCATION="East US"
VM_SIZE="Standard_B2s"
ADMIN_USERNAME="azureuser"
ADMIN_PASSWORD="AzurePassword123!"

echo -e "${BLUE}🚀 Enable RDP Bot - Creating Example VM${NC}"
echo "=================================================="
echo "This script will create a Windows VM with intentional RDP issues"
echo "for testing the Enable RDP Bot."
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed. Please install it first.${NC}"
    echo "Installation: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if user is logged in
if ! az account show &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Azure CLI is installed and user is logged in${NC}"

# Get current subscription
SUBSCRIPTION_ID=$(az account show --query id --output tsv)
echo -e "${BLUE}📋 Using subscription: ${SUBSCRIPTION_ID}${NC}"
echo ""

# Create resource group
echo -e "${YELLOW}📁 Creating resource group: ${RESOURCE_GROUP}${NC}"
az group create \
    --name $RESOURCE_GROUP \
    --location "$LOCATION" \
    --tags Purpose="AI Support Bot Testing" CreatedBy="Azure CLI Script"

echo -e "${GREEN}✅ Resource group created${NC}"

# Create virtual network
echo -e "${YELLOW}🌐 Creating virtual network${NC}"
az network vnet create \
    --resource-group $RESOURCE_GROUP \
    --name "${VM_NAME}-vnet" \
    --address-prefix 10.0.0.0/16 \
    --subnet-name "${VM_NAME}-subnet" \
    --subnet-prefix 10.0.1.0/24

echo -e "${GREEN}✅ Virtual network created${NC}"

# Create Network Security Group with RDP BLOCKED (intentional problem)
echo -e "${YELLOW}🔒 Creating NSG with RDP BLOCKED (intentional problem)${NC}"
az network nsg create \
    --resource-group $RESOURCE_GROUP \
    --name "${VM_NAME}-nsg"

# Add rule to BLOCK RDP (this is the problem we want to test)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name "${VM_NAME}-nsg" \
    --name "DenyRDP" \
    --priority 1000 \
    --direction Inbound \
    --access Deny \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges 3389 \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" \
    --description "BLOCK RDP - Intentional problem for AI testing"

# Add rule to allow HTTP (so VM is accessible for other tests)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name "${VM_NAME}-nsg" \
    --name "AllowHTTP" \
    --priority 1001 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges 80 \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*"

echo -e "${GREEN}✅ NSG created with RDP BLOCKED${NC}"

# Create public IP
echo -e "${YELLOW}🌍 Creating public IP address${NC}"
az network public-ip create \
    --resource-group $RESOURCE_GROUP \
    --name "${VM_NAME}-pip" \
    --allocation-method Static \
    --sku Standard

echo -e "${GREEN}✅ Public IP created${NC}"

# Create network interface
echo -e "${YELLOW}🔌 Creating network interface${NC}"
az network nic create \
    --resource-group $RESOURCE_GROUP \
    --name "${VM_NAME}-nic" \
    --vnet-name "${VM_NAME}-vnet" \
    --subnet "${VM_NAME}-subnet" \
    --public-ip-address "${VM_NAME}-pip" \
    --network-security-group "${VM_NAME}-nsg"

echo -e "${GREEN}✅ Network interface created${NC}"

# Create Windows VM
echo -e "${YELLOW}🖥️  Creating Windows VM${NC}"
az vm create \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --location "$LOCATION" \
    --size $VM_SIZE \
    --nics "${VM_NAME}-nic" \
    --image "Win2019Datacenter" \
    --admin-username $ADMIN_USERNAME \
    --admin-password $ADMIN_PASSWORD \
    --tags Purpose="AI Support Bot Testing" Problem="RDP Blocked" Status="Will be stopped"

echo -e "${GREEN}✅ Windows VM created${NC}"

# Get public IP address
PUBLIC_IP=$(az vm show \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --show-details \
    --query publicIps \
    --output tsv)

echo -e "${GREEN}✅ VM creation completed!${NC}"

# Stop the VM (intentional problem)
echo -e "${YELLOW}⏹️  Stopping VM (intentional problem)${NC}"
az vm deallocate \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME

echo -e "${GREEN}✅ VM stopped (deallocated)${NC}"

# Display results
echo ""
echo -e "${BLUE}🎉 Example VM Created Successfully!${NC}"
echo "=================================================="
echo -e "${GREEN}📋 VM Details:${NC}"
echo "   VM Name: $VM_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Public IP: $PUBLIC_IP"
echo "   Admin Username: $ADMIN_USERNAME"
echo "   Admin Password: $ADMIN_PASSWORD"
echo "   Location: $LOCATION"
echo "   VM Size: $VM_SIZE"

echo ""
echo -e "${RED}🚨 Intentional Problems Created:${NC}"
echo "   1. RDP port 3389 is BLOCKED by Network Security Group"
echo "   2. VM is STOPPED (deallocated) - not running"
echo "   3. VM has limited resources (Standard_B2s)"

echo ""
echo -e "${BLUE}🧪 Testing Instructions:${NC}"
echo "   1. Run: python3 enable_rdp_bot.py --resource-group $RESOURCE_GROUP --vm $VM_NAME"
echo "   2. The Enable RDP Bot will detect the RDP blocking and VM stopped issues"
echo "   3. AI will provide specific remediation steps"

echo ""
echo -e "${YELLOW}🔧 Manual Verification:${NC}"
echo "   Check NSG: az network nsg rule list --nsg-name ${VM_NAME}-nsg --resource-group $RESOURCE_GROUP"
echo "   Check VM status: az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details"
echo "   Try RDP: Should fail due to NSG blocking"

echo ""
echo -e "${GREEN}🎯 Ready for AI Agent Testing!${NC}"
echo "The VM is now ready to test the Enable RDP Bot."
echo "Run the enable_rdp_bot.py tool to see the AI agent in action!"
