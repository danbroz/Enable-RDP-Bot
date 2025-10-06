#!/bin/bash

# Test Case 10: RDP Rule with Wrong Source Port Range
# This test creates a VM with an RDP rule that has a restricted source port range
# The Enable RDP Bot should detect this and fix it by updating the rule to use * for source ports

set -e

# Configuration
RESOURCE_GROUP="test10-resource-group"
VM_NAME="test10-vm"
LOCATION="eastus"
VM_SIZE="Standard_B2s"
ADMIN_USERNAME="azureuser"
ADMIN_PASSWORD="AzurePassword123!"

echo "🧪 Test Case 10: RDP Rule with Wrong Source Port Range"
echo "======================================================="
echo "This test creates a VM with an RDP rule that has a restricted source port range"
echo "The Enable RDP Bot should detect and fix this configuration issue"
echo ""

# Check if Azure CLI is logged in
if ! az account show &> /dev/null; then
    echo "❌ Error: Not logged in to Azure CLI"
    echo "Please run 'az login' first"
    exit 1
fi

echo "📋 Creating Test Case 10 VM with wrong source port range configuration..."
echo ""

# Create resource group
echo "🏗️  Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION --tags TestCase="Wrong Source Port Range" > /dev/null
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

# Create NSG with WRONG source port range rule
echo "🔒 Creating NSG with WRONG source port range rule (restricted ports instead of *)"
az network nsg create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-nsg > /dev/null

# Add RDP rule with WRONG source port range (restricted ports instead of *)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowRDP \
    --priority 100 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "1024-65535" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" \
    --description "Allow RDP - WRONG SOURCE PORT RANGE (1024-65535 instead of *)" > /dev/null

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

echo "✅ NSG created with WRONG source port range rule (1024-65535 instead of *)"

# Create public IP address
echo "🌍 Creating public IP address"
az network public-ip create 2>/dev/null \
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
az vm create 2>/dev/null \
    --resource-group $RESOURCE_GROUP \
    --name $VM_NAME \
    --location $LOCATION \
    --size $VM_SIZE \
    --nics ${VM_NAME}-nic \
    --image Win2019Datacenter \
    --admin-username $ADMIN_USERNAME \
    --admin-password $ADMIN_PASSWORD \
    --public-ip-sku Standard > /dev/null

# Get VM details
VM_IP=$(az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details --query publicIps --output tsv)

echo "✅ Windows VM created"
echo "✅ VM creation completed!"
echo ""

echo "🎉 Test Case 10 VM Created Successfully!"
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
echo "   1. RDP rule exists but has restricted source port range (1024-65535)"
echo "   2. RDP traffic from source ports 1-1023 will be blocked"
echo "   3. VM is running but RDP may be blocked for some clients"
echo ""
echo "🧪 Testing Instructions:"
echo "   1. Run: python3 enable_rdp_bot.py --rg $RESOURCE_GROUP --vm $VM_NAME"
echo "   2. The Enable RDP Bot will detect the restricted source port range"
echo "   3. Bot will auto-fix by updating the rule to use * for source ports"
echo ""
echo "🔧 Manual Verification:"
echo "   Check NSG: az network nsg rule list --nsg-name ${VM_NAME}-nsg --resource-group $RESOURCE_GROUP"
echo "   Check VM status: az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details"
echo "   Try RDP: May fail due to restricted source port range"
echo ""
echo "🎯 Ready for AI Agent Testing!"
echo "The VM is now ready to test the Enable RDP Bot's source port range detection and fixing."
echo "Run the enable_rdp_bot.py tool to see the AI agent fix the source port range configuration!"
