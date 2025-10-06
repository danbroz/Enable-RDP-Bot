#!/bin/bash

# Azure Agentic AI Support Bot - Deployment Script
# This script deploys the complete AI support bot infrastructure to Azure

set -e

echo "🚀 Starting Azure Agentic AI Support Bot Deployment"
echo "=================================================="

# Configuration
RESOURCE_GROUP_NAME="azure-ai-support-bot-rg"
LOCATION="East US"
ENVIRONMENT="dev"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Terraform is installed
    if ! command -v terraform &> /dev/null; then
        print_error "Terraform is not installed. Please install it first."
        exit 1
    fi
    
    # Check if Python is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install it first."
        exit 1
    fi
    
    print_success "All prerequisites are installed"
}

# Login to Azure
azure_login() {
    print_status "Logging into Azure..."
    
    # Check if already logged in
    if az account show &> /dev/null; then
        print_success "Already logged into Azure"
    else
        print_status "Please log in to Azure..."
        az login
    fi
    
    # Set subscription
    print_status "Setting Azure subscription..."
    az account set --subscription "your-subscription-id-here"
    
    print_success "Azure login completed"
}

# Create resource group
create_resource_group() {
    print_status "Creating resource group: $RESOURCE_GROUP_NAME"
    
    # Check if resource group exists
    if az group show --name $RESOURCE_GROUP_NAME &> /dev/null; then
        print_warning "Resource group $RESOURCE_GROUP_NAME already exists"
    else
        az group create \
            --name $RESOURCE_GROUP_NAME \
            --location "$LOCATION" \
            --tags Project="Azure-AI-Support-Bot" Environment="$ENVIRONMENT"
        print_success "Resource group created successfully"
    fi
}

# Deploy infrastructure with Terraform
deploy_infrastructure() {
    print_status "Deploying infrastructure with Terraform..."
    
    cd terraform
    
    # Initialize Terraform
    print_status "Initializing Terraform..."
    terraform init
    
    # Create Terraform plan
    print_status "Creating Terraform plan..."
    terraform plan \
        -var="environment=$ENVIRONMENT" \
        -var="location=$LOCATION" \
        -out=tfplan
    
    # Apply Terraform plan
    print_status "Applying Terraform plan..."
    terraform apply tfplan
    
    cd ..
    
    print_success "Infrastructure deployment completed"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    pip install -r requirements.txt
    
    print_success "Python dependencies installed"
}

# Configure environment variables
configure_environment() {
    print_status "Configuring environment variables..."
    
    # Get Terraform outputs
    cd terraform
    OPENAI_ENDPOINT=$(terraform output -raw openai_endpoint)
    OPENAI_KEY=$(terraform output -raw openai_primary_key)
    COSMOS_ENDPOINT=$(terraform output -raw cosmos_db_endpoint)
    COSMOS_KEY=$(terraform output -raw cosmos_db_primary_key)
    APP_INSIGHTS_CONNECTION_STRING=$(terraform output -raw application_insights_connection_string)
    cd ..
    
    # Create .env file
    cat > .env << EOF
# Azure Configuration
AZURE_SUBSCRIPTION_ID=a92124de-c1f5-4fdb-b197-e7367d4988cd
AZURE_TENANT_ID=c7f298f5-9e9d-41c6-9434-c511d401fe8c

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT
AZURE_OPENAI_API_KEY=$OPENAI_KEY
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4-turbo

# Cosmos DB Configuration
COSMOS_DB_ENDPOINT=$COSMOS_ENDPOINT
COSMOS_DB_KEY=$COSMOS_KEY
COSMOS_DB_DATABASE_NAME=ai-support-bot
COSMOS_DB_CONTAINER_NAME=conversations

# Application Insights
APPLICATIONINSIGHTS_CONNECTION_STRING=$APP_INSIGHTS_CONNECTION_STRING

# Bot Configuration
AZURE_BOT_APP_ID=your-bot-app-id
AZURE_BOT_APP_PASSWORD=your-bot-app-password

# Agent Configuration
DEFAULT_TEMPERATURE=0.7
MAX_TOKENS=1000
ENABLE_AUTO_RESOLUTION=true
EOF
    
    print_success "Environment variables configured"
}

# Deploy bot application
deploy_bot_application() {
    print_status "Deploying bot application to Azure Functions..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Deploy to Azure Functions
    cd src
    func azure functionapp publish azure-ai-support-bot-func --python
    cd ..
    
    print_success "Bot application deployed successfully"
}

# Run tests
run_tests() {
    print_status "Running test suite..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run pytest
    python -m pytest tests/ -v --tb=short
    
    print_success "All tests passed"
}

# Display deployment summary
deployment_summary() {
    print_status "Deployment Summary"
    echo "=================="
    
    cd terraform
    
    echo "Resource Group: $(terraform output -raw resource_group_name)"
    echo "OpenAI Endpoint: $(terraform output -raw openai_endpoint)"
    echo "Bot Service: $(terraform output -raw bot_service_endpoint)"
    echo "Functions App: $(terraform output -raw functions_endpoint)"
    echo "Test VM IP: $(terraform output -raw test_vm_public_ip)"
    
    cd ..
    
    echo ""
    print_success "🎉 Azure Agentic AI Support Bot deployment completed successfully!"
    echo ""
    echo "Next Steps:"
    echo "1. Configure your bot application registration in Azure AD"
    echo "2. Update the .env file with your bot credentials"
    echo "3. Test the bot using the web chat interface"
    echo "4. Review the documentation in the docs/ folder"
    echo ""
    echo "For testing RDP connectivity:"
    echo "mstsc /v:$(cd terraform && terraform output -raw test_vm_public_ip)"
}

# Main deployment flow
main() {
    echo "Azure Agentic AI Support Bot - Assessment Solution"
    echo "=================================================="
    echo ""
    
    check_prerequisites
    azure_login
    create_resource_group
    deploy_infrastructure
    install_dependencies
    configure_environment
    
    # Optional: Deploy bot application (requires additional configuration)
    # deploy_bot_application
    
    # Optional: Run tests
    # run_tests
    
    deployment_summary
}

# Handle script interruption
trap 'print_error "Deployment interrupted by user"; exit 1' INT

# Run main function
main "$@"
