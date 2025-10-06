#!/bin/bash

# Test Case 7: RDP Rule with Restricted Source IP
# This test creates a VM with an RDP rule that only allows access from a specific IP address
# The Enable RDP Bot should detect this and fix it by updating the rule to allow access from any IP

set -e

# Configuration
RESOURCE_GROUP="test7-resource-group"
VM_NAME="test7-vm"
LOCATION="eastus"
VM_SIZE="Standard_B2s"
ADMIN_USERNAME="azureuser"
ADMIN_PASSWORD="AzurePassword123!"

echo "🧪 Test Case 7: RDP Rule with Restricted Source IP"
echo "=================================================="
echo "This test creates a VM with an RDP rule that only allows access from a specific IP"
echo "The Enable RDP Bot should detect and fix this by allowing access from any IP"
echo ""

# Check if Azure CLI is logged in
if ! az account show &> /dev/null; then
    echo "❌ Error: Not logged in to Azure CLI"
    echo "Please run 'az login' first"
    exit 1
fi

echo "📋 Creating Test Case 7 VM with restricted source IP configuration..."
echo ""

# Create resource group
echo "🏗️  Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION --tags TestCase="Restricted Source IP" > /dev/null
echo "✅ Resource group created"

# Create virtual network
echo "🌐 Creating virtual network"
az network vnet create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-vnet \
    --address-prefix 10.0.0.0/16 \
    --subnet-name ${VM_NAME}-subnet \
    --subnet-prefix 10.0.1.0/24 > /dev/null
echo "✅ Virtual network created"

# Create NSG with RESTRICTED source IP rule
echo "🔒 Creating NSG with RESTRICTED source IP rule (only allows 192.168.1.100)"
az network nsg create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-nsg > /dev/null

# Add RDP rule with RESTRICTED source IP (only allows 192.168.1.100)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowRDP \
    --priority 100 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "192.168.1.100" \
    --destination-address-prefixes "*" \
    --description "Allow RDP - RESTRICTED SOURCE IP (only 192.168.1.100)" > /dev/null

# Add HTTP rule for comparison
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowHTTP \
    --priority 200 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "80" \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" > /dev/null

echo "✅ NSG created with RESTRICTED source IP rule (192.168.1.100 only)"

# Create public IP address
echo "🌍 Creating public IP address"
az network public-ip create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-pip \
    --allocation-method Static \
    --sku Standard > /dev/null
echo "✅ Public IP created"

# Create network interface
echo "🔌 Creating network interface"
az network nic create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-nic \
    --vnet-name ${VM_NAME}-vnet \
    --subnet ${VM_NAME}-subnet \
    --public-ip-address ${VM_NAME}-pip \
    --network-security-group ${VM_NAME}-nsg > /dev/null
echo "✅ Network interface created"

# Create Windows VM
echo "🖥️  Creating Windows VM"
az vm create \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --location $LOCATION \
    --size $VM_SIZE \
    --nics ${VM_NAME}-nic \
    --image Win2019Datacenter \
    --admin-username $ADMIN_USERNAME \
    --admin-password $ADMIN_PASSWORD \
    --public-ip-sku Standard \
    --public-ip-sku Standard > /dev/null

# Get VM details
VM_IP=$(az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details --query publicIps --output tsv)

echo "✅ Windows VM created"
echo "✅ VM creation completed!"
echo ""

echo "🎉 Test Case 7 VM Created Successfully!"
echo "=================================================="
echo "📋 VM Details:"
echo "   VM Name: $VM_NAME"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Public IP: $VM_IP"
echo "   Admin Username: $ADMIN_USERNAME"
echo "   Admin Password: $ADMIN_PASSWORD"
echo "   Location: $LOCATION"
echo "   VM Size: $VM_SIZE"
echo ""
echo "🚨 Intentional Problem Created:"
echo "   1. RDP rule exists but only allows access from 192.168.1.100"
echo "   2. RDP traffic from other IP addresses will be blocked"
echo "   3. VM is running but RDP is effectively blocked for most users"
echo ""
echo "🧪 Testing Instructions:"
echo "   1. Run: python3 enable_rdp_bot.py --rg $RESOURCE_GROUP --vm $VM_NAME"
echo "   2. The Enable RDP Bot will detect the restricted source IP configuration"
echo "   3. Bot will auto-fix by updating the rule to allow access from any IP (*)"
echo ""
echo "🔧 Manual Verification:"
echo "   Check NSG: az network nsg rule list --nsg-name ${VM_NAME}-nsg --resource-group $RESOURCE_GROUP"
echo "   Check VM status: az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details"
echo "   Try RDP: Should fail due to restricted source IP configuration"
echo ""
echo "🎯 Ready for AI Agent Testing!"
echo "The VM is now ready to test the Enable RDP Bot's source IP restriction detection and fixing."
echo "Run the enable_rdp_bot.py tool to see the AI agent fix the source IP restriction!"
