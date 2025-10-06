#!/bin/bash

# Azure Agentic AI Support Bot - Simplified Deployment Script
# This script deploys the simplified version of the solution

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Azure Agentic AI Support Bot - Simplified Deployment${NC}"
echo "============================================================"

# Check if we're in the right directory
if [ ! -f "src/agents/simple_agent.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the project root directory${NC}"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

if ! command_exists python3; then
    echo -e "${RED}❌ Python 3 is not installed${NC}"
    exit 1
fi

if ! command_exists terraform; then
    echo -e "${RED}❌ Terraform is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Set up Python environment
echo -e "${YELLOW}🐍 Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements_simple.txt

echo -e "${GREEN}✅ Python environment ready${NC}"

# Create environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}📝 Creating environment configuration...${NC}"
    cp env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your Azure and OpenAI credentials${NC}"
    echo -e "${YELLOW}   Required variables:${NC}"
    echo -e "${YELLOW}   - AZURE_SUBSCRIPTION_ID${NC}"
    echo -e "${YELLOW}   - OPENAI_API_KEY${NC}"
    echo ""
    read -p "Press Enter after updating .env file..."
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check required environment variables
if [ -z "$AZURE_SUBSCRIPTION_ID" ]; then
    echo -e "${RED}❌ AZURE_SUBSCRIPTION_ID is not set${NC}"
    exit 1
fi

# Check for either OpenAI API key format
if [ -z "$AZURE_OPENAI_API_KEY" ] && [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${RED}❌ AZURE_OPENAI_API_KEY or OPENAI_API_KEY is not set${NC}"
    exit 1
fi

# Use Azure OpenAI API key if available, otherwise fall back to OpenAI
if [ -n "$AZURE_OPENAI_API_KEY" ]; then
    OPENAI_API_KEY="$AZURE_OPENAI_API_KEY"
    export OPENAI_API_KEY
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"

# Deploy Terraform infrastructure
echo -e "${YELLOW}🏗️  Deploying Azure infrastructure...${NC}"
cd terraform

# Initialize Terraform
terraform init

# Create terraform.tfvars file
cat > terraform.tfvars << EOF
subscription_id = "$AZURE_SUBSCRIPTION_ID"
location = "East US"
resource_group_name = "azure-support-bot-rg"
vm_name = "support-bot-test-vm"
admin_username = "azureuser"
admin_password = "AzurePassword123!"
EOF

# Plan deployment
echo -e "${YELLOW}📋 Planning Terraform deployment...${NC}"
terraform plan -var-file="terraform.tfvars"

# Ask for confirmation
echo ""
read -p "Do you want to proceed with the deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Deployment cancelled${NC}"
    exit 0
fi

# Apply deployment
echo -e "${YELLOW}🚀 Deploying infrastructure...${NC}"
terraform apply -var-file="terraform.tfvars" -auto-approve

# Get outputs
echo -e "${YELLOW}📤 Getting deployment outputs...${NC}"
VM_PUBLIC_IP=$(terraform output -raw vm_public_ip)
RESOURCE_GROUP=$(terraform output -raw resource_group_name)
VM_NAME=$(terraform output -raw vm_name)
KEY_VAULT_NAME=$(terraform output -raw key_vault_name)

cd ..

echo -e "${GREEN}✅ Infrastructure deployment completed!${NC}"
echo ""
echo -e "${BLUE}📋 Deployment Summary:${NC}"
echo "=================================="
echo "Resource Group: $RESOURCE_GROUP"
echo "VM Name: $VM_NAME"
echo "VM Public IP: $VM_PUBLIC_IP"
echo "Key Vault: $KEY_VAULT_NAME"
echo ""

# Test the agent
echo -e "${YELLOW}🧪 Testing the Azure Support Bot...${NC}"
echo "This will run a simulated troubleshooting session..."

# Create a test script
cat > test_agent.py << 'EOF'
#!/usr/bin/env python3
import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from agents.simple_agent import AzureSupportBot

async def test_bot():
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not subscription_id or not openai_api_key:
        print("❌ Missing required environment variables")
        return
    
    print("🤖 Initializing Azure Support Bot...")
    bot = AzureSupportBot(subscription_id, openai_api_key)
    
    # Test with the deployed VM
    vm_name = "support-bot-test-vm"
    resource_group = "azure-support-bot-rg"
    
    print(f"🔍 Starting troubleshooting session for VM: {vm_name}")
    print("   This is a demonstration - some checks may fail in demo environment")
    
    try:
        session_id = await bot.start_troubleshooting(vm_name, resource_group)
        results = bot.get_session_results(session_id)
        
        if results:
            print("\n✅ Troubleshooting completed successfully!")
            print(f"📊 Session ID: {session_id}")
            print(f"🎯 VM: {results['vm_name']}")
            print(f"📅 Started: {results['start_time']}")
            print(f"📋 Status: {results['status']}")
            
            print("\n🔍 Diagnostic Results:")
            for diagnostic in results['diagnostics']:
                status_emoji = "✅" if diagnostic['status'] == "pass" else "❌" if diagnostic['status'] == "fail" else "⚠️"
                print(f"   {status_emoji} {diagnostic['check_name']}: {diagnostic['message']}")
            
            if results['resolution']:
                print(f"\n🤖 AI Analysis:\n{results['resolution']}")
        else:
            print("❌ Failed to get troubleshooting results")
            
    except Exception as e:
        print(f"❌ Error during troubleshooting: {str(e)}")
        print("   This is expected in a demo environment without real Azure credentials")

if __name__ == "__main__":
    asyncio.run(test_bot())
EOF

chmod +x test_agent.py

# Run the test
python3 test_agent.py

echo ""
echo -e "${GREEN}🎉 Azure Agentic AI Support Bot deployment completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "==============="
echo "1. RDP to your test VM: $VM_PUBLIC_IP"
echo "   Username: azureuser"
echo "   Password: AzurePassword123!"
echo "   Port: 3389"
echo ""
echo "2. Test RDP connectivity issues:"
echo "   - Stop the VM to simulate RDP failure"
echo "   - Run the bot again to see diagnostics"
echo "   - Restart the VM to resolve the issue"
echo ""
echo "3. Explore the code:"
echo "   - src/agents/simple_agent.py - Main agent implementation"
echo "   - terraform/simple_main.tf - Infrastructure code"
echo ""
echo -e "${BLUE}📚 Documentation:${NC}"
echo "=================="
echo "- README.md - Setup and usage instructions"
echo "- docs/ - Architecture and design documents"
echo ""
echo -e "${GREEN}✅ Ready to troubleshoot Azure VM RDP issues!${NC}"
