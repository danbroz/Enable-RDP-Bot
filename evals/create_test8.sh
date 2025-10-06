#!/bin/bash

# Test Case 8: Multiple Conflicting Rules (Complex NSG Scenario)
# This test creates a VM with multiple conflicting NSG rules that create a complex scenario
# The Enable RDP Bot should detect and resolve the conflicts to enable RDP access

set -e

# Configuration
RESOURCE_GROUP="test8-resource-group"
VM_NAME="test8-vm"
LOCATION="eastus"
VM_SIZE="Standard_B2s"
ADMIN_USERNAME="azureuser"
ADMIN_PASSWORD="AzurePassword123!"

echo "🧪 Test Case 8: Multiple Conflicting Rules (Complex NSG Scenario)"
echo "================================================================="
echo "This test creates a VM with multiple conflicting NSG rules"
echo "The Enable RDP Bot should detect and resolve the conflicts to enable RDP access"
echo ""

# Check if Azure CLI is logged in
if ! az account show &> /dev/null; then
    echo "❌ Error: Not logged in to Azure CLI"
    echo "Please run 'az login' first"
    exit 1
fi

echo "📋 Creating Test Case 8 VM with complex NSG rule conflicts..."
echo ""

# Create resource group
echo "🏗️  Creating resource group: $RESOURCE_GROUP"
az group create --name $RESOURCE_GROUP --location $LOCATION --tags TestCase="Complex NSG Conflicts" > /dev/null
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

# Create NSG with COMPLEX conflicting rules
echo "🔒 Creating NSG with COMPLEX conflicting rules"
az network nsg create \
    --resource-group $RESOURCE_GROUP \
    --name ${VM_NAME}-nsg > /dev/null

# Add multiple conflicting rules to create a complex scenario
# Rule 1: Deny all RDP traffic (highest priority)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name DenyAllRDP \
    --priority 100 \
    --direction Inbound \
    --access Deny \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" \
    --description "Deny all RDP traffic - highest priority" > /dev/null

# Rule 2: Allow RDP from specific IP (lower priority - will be blocked)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowRDPFromOffice \
    --priority 200 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "203.0.113.0/24" \
    --destination-address-prefixes "*" \
    --description "Allow RDP from office IP range - blocked by DenyAllRDP" > /dev/null

# Rule 3: Allow RDP from any IP (even lower priority - will be blocked)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowRDPAny \
    --priority 300 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" \
    --description "Allow RDP from any IP - blocked by DenyAllRDP" > /dev/null

# Rule 4: Deny RDP from specific IP range (medium priority)
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name DenyRDPFromSuspicious \
    --priority 150 \
    --direction Inbound \
    --access Deny \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "3389" \
    --source-address-prefixes "198.51.100.0/24" \
    --destination-address-prefixes "*" \
    --description "Deny RDP from suspicious IP range" > /dev/null

# Rule 5: Allow HTTP for comparison
az network nsg rule create \
    --resource-group $RESOURCE_GROUP \
    --nsg-name ${VM_NAME}-nsg \
    --name AllowHTTP \
    --priority 400 \
    --direction Inbound \
    --access Allow \
    --protocol Tcp \
    --source-port-ranges "*" \
    --destination-port-ranges "80" \
    --source-address-prefixes "*" \
    --destination-address-prefixes "*" > /dev/null

echo "✅ NSG created with COMPLEX conflicting rules"

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
    --public-ip-sku Standard > /dev/null

# Get VM details
VM_IP=$(az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details --query publicIps --output tsv)

echo "✅ Windows VM created"
echo "✅ VM creation completed!"
echo ""

echo "🎉 Test Case 8 VM Created Successfully!"
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
echo "   1. DenyAllRDP rule (priority 100) blocks all RDP traffic"
echo "   2. AllowRDPFromOffice rule (priority 200) is blocked by DenyAllRDP"
echo "   3. AllowRDPAny rule (priority 300) is blocked by DenyAllRDP"
echo "   4. DenyRDPFromSuspicious rule (priority 150) adds additional complexity"
echo "   5. VM is running but RDP is completely blocked"
echo ""
echo "🧪 Testing Instructions:"
echo "   1. Run: python3 enable_rdp_bot.py --rg $RESOURCE_GROUP --vm $VM_NAME"
echo "   2. The Enable RDP Bot will detect the complex rule conflicts"
echo "   3. Bot will auto-fix by resolving conflicts and enabling RDP access"
echo ""
echo "🔧 Manual Verification:"
echo "   Check NSG: az network nsg rule list --nsg-name ${VM_NAME}-nsg --resource-group $RESOURCE_GROUP"
echo "   Check VM status: az vm show --name $VM_NAME --resource-group $RESOURCE_GROUP --show-details"
echo "   Try RDP: Should fail due to complex rule conflicts"
echo ""
echo "🎯 Ready for AI Agent Testing!"
echo "The VM is now ready to test the Enable RDP Bot's complex rule conflict resolution."
echo "Run the enable_rdp_bot.py tool to see the AI agent resolve the complex NSG conflicts!"
