#!/bin/bash

# Test script to demonstrate Azure CLI VM creation and RDP troubleshooting
# This script shows the complete workflow from VM creation to AI troubleshooting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Azure CLI VM Testing Workflow${NC}"
echo "=============================================="
echo "This script demonstrates the complete workflow:"
echo "1. Create example VM with RDP issues"
echo "2. Test the RDP troubleshooting agent"
echo "3. Clean up resources"
echo ""

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}❌ Azure CLI is not installed${NC}"
    exit 1
fi

# Check if logged in
if ! az account show &> /dev/null; then
    echo -e "${RED}❌ Not logged in to Azure. Please run 'az login' first${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All prerequisites met${NC}"
echo ""

# Get user confirmation
echo -e "${YELLOW}⚠️  This will create Azure resources that may incur costs.${NC}"
echo "The test will:"
echo "  - Create a resource group"
echo "  - Create a Windows VM"
echo "  - Create networking resources"
echo "  - Test the RDP troubleshooting agent"
echo "  - Clean up all resources"
echo ""

read -p "Do you want to continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}❌ Test cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}📋 Starting Azure CLI VM Test${NC}"
echo "=============================================="

# Step 1: Create example VM
echo -e "${YELLOW}Step 1: Creating example VM with RDP issues...${NC}"
./create_example_vm.sh

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ VM creation failed${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✅ VM created successfully${NC}"

# Step 2: Test the RDP troubleshooting agent
echo ""
echo -e "${YELLOW}Step 2: Testing RDP troubleshooting agent...${NC}"
echo "Running: python3 enable_rdp.py --resource-group ai-support-bot-test-rg --vm example-vm"
echo ""

python3 enable_rdp.py --resource-group ai-support-bot-test-rg --vm example-vm

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ RDP troubleshooting test failed${NC}"
    echo "Cleaning up resources..."
    ./cleanup_example_vm.sh
    exit 1
fi

echo ""
echo -e "${GREEN}✅ RDP troubleshooting test completed${NC}"

# Step 3: Ask if user wants to clean up
echo ""
echo -e "${YELLOW}Step 3: Cleanup${NC}"
echo "The test VM is still running. You can:"
echo "  1. Keep it for further testing"
echo "  2. Clean it up now"
echo ""

read -p "Do you want to clean up the test VM now? (yes/no): " -r
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${YELLOW}Cleaning up test VM...${NC}"
    ./cleanup_example_vm.sh
    echo -e "${GREEN}✅ Cleanup completed${NC}"
else
    echo -e "${BLUE}📋 VM kept for further testing${NC}"
    echo "To clean up later, run: ./cleanup_example_vm.sh"
fi

echo ""
echo -e "${GREEN}🎉 Azure CLI VM Test Completed Successfully!${NC}"
echo "=============================================="
echo "The test demonstrated:"
echo "✅ Azure CLI VM creation with intentional RDP issues"
echo "✅ RDP troubleshooting agent diagnostics"
echo "✅ AI-powered analysis and recommendations"
echo "✅ Complete workflow from problem to solution"
echo ""
echo -e "${BLUE}💡 Next Steps:${NC}"
echo "• Try the troubleshooting agent on your own VMs"
echo "• Explore the different command-line options"
echo "• Integrate the tool into your DevOps workflows"
