#!/bin/bash

# Install Azure CLI manually without sudo
# This script downloads and installs Azure CLI to a user directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔧 Azure CLI Manual Installation${NC}"
echo "=================================="

# Create local bin directory
mkdir -p ~/.local/bin

# Download Azure CLI
echo -e "${YELLOW}📥 Downloading Azure CLI...${NC}"
cd /tmp
wget -q https://packages.microsoft.com/repos/azure-cli/pool/main/a/azure-cli/azure-cli_2.58.0-1_all.deb

# Extract the package manually
echo -e "${YELLOW}📦 Extracting Azure CLI...${NC}"
mkdir -p azure-cli-extract
cd azure-cli-extract

# Extract the deb package
ar x ../azure-cli_2.58.0-1_all.deb
tar -xf data.tar.xz

# Copy binaries to local directory
echo -e "${YELLOW}📋 Installing to ~/.local/bin...${NC}"
cp usr/bin/az ~/.local/bin/
chmod +x ~/.local/bin/az

# Install Python dependencies
echo -e "${YELLOW}🐍 Installing Python dependencies...${NC}"
pip3 install --user azure-cli

# Add to PATH
echo -e "${YELLOW}🔗 Adding to PATH...${NC}"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
export PATH="$HOME/.local/bin:$PATH"

# Clean up
cd ..
rm -rf azure-cli-extract
rm -f azure-cli_2.58.0-1_all.deb

echo -e "${GREEN}✅ Azure CLI installation completed!${NC}"
echo ""
echo -e "${BLUE}📋 Next Steps:${NC}"
echo "1. Run: source ~/.bashrc"
echo "2. Run: az login"
echo "3. Run: az account set --subscription your-subscription-id-here"
echo "4. Run: ./deploy_simple.sh"
echo ""
echo -e "${GREEN}🎉 Ready to deploy!${NC}"
