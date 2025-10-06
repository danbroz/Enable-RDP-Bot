# Azure Agentic AI Support Bot - Setup Instructions

## 🔐 Security Notice

**This package has been sanitized for sharing. All sensitive credentials and personal information have been removed.**

## 📋 Prerequisites

Before running this solution, you'll need to set up the following:

### 1. Azure Resources
- Azure subscription with appropriate permissions
- Azure OpenAI Service with GPT-4 deployment
- Azure Bot Service (optional)
- Cosmos DB (optional)
- Key Vault (optional)
- Application Insights (optional)

### 2. Local Environment
- Python 3.9+ (tested with Python 3.13)
- Azure CLI (for deployment)
- Terraform (for infrastructure)

## 🚀 Quick Setup

### 1. Clone and Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements_simple.txt

# Or for full dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create a `.env` file based on `env.example`:

```bash
cp env.example .env
# Edit .env with your actual Azure credentials
```

Required variables:
- `AZURE_SUBSCRIPTION_ID` - Your Azure subscription ID
- `AZURE_TENANT_ID` - Your Azure tenant ID  
- `AZURE_CLIENT_ID` - Your service principal client ID
- `AZURE_CLIENT_SECRET` - Your service principal secret
- `AZURE_OPENAI_API_KEY` - Your OpenAI API key

### 3. Run the Demo
```bash
# Run the simulated problem VM test (recommended)
python3 test_simulated_problem_vm.py

# Or run the final demo
python3 final_demo.py
```

## 🏗️ Infrastructure Deployment

### Using Terraform
```bash
cd terraform/
terraform init
terraform plan
terraform apply
```

### Using Azure CLI
```bash
# Login to Azure
az login

# Set your subscription
az account set --subscription "your-subscription-id-here"

# Run deployment script
./deploy.sh
```

## 🧪 Testing Scenarios

The solution includes several test scenarios:

1. **Simulated Problem VM Test** (`test_simulated_problem_vm.py`)
   - Tests AI agent against simulated Azure VM issues
   - No real Azure resources required
   - Demonstrates complete functionality

2. **Real VM Test** (`test_real_vm.py`)
   - Tests against actual Azure VMs
   - Requires valid Azure credentials
   - Creates real diagnostic data

3. **Final Demo** (`final_demo.py`)
   - Comprehensive demonstration
   - Shows all capabilities
   - Production-ready examples

## 📁 Project Structure

```
├── src/                    # Source code
│   ├── agents/            # AI agents
│   ├── bot/               # Bot service
│   ├── memory/            # Conversation storage
│   ├── plugins/           # Azure diagnostic plugins
│   └── safety/            # Content safety
├── terraform/             # Infrastructure as code
├── docs/                  # Documentation
├── tests/                 # Test scenarios
├── prompts/               # AI prompt templates
├── config/                # Configuration files
└── requirements.txt       # Python dependencies
```

## 🔧 Configuration

### Agent Configuration (`config/agent_config.yaml`)
- AI model settings
- Diagnostic parameters
- Safety thresholds

### Model Configuration (`config/model_config.yaml`)
- OpenAI model settings
- Temperature and token limits
- Fallback configurations

## 🛡️ Security Considerations

- Never commit `.env` files or `terraform.tfvars`
- Use Azure Key Vault for production secrets
- Implement proper RBAC for service principals
- Enable Azure Security Center monitoring
- Regular credential rotation

## 📊 Monitoring

The solution includes comprehensive monitoring:
- Application Insights integration
- Azure Monitor dashboards
- Custom metrics and alerts
- Performance tracking

## 🤝 Support

For questions or issues:
1. Check the documentation in `docs/`
2. Review the test scenarios
3. Examine the configuration files
4. Check Azure service health

## 📄 License

This solution is provided as-is for demonstration purposes. Please ensure compliance with your organization's policies and Azure terms of service.

---

**🎯 This solution demonstrates advanced Azure AI integration and is ready for production deployment with proper credential configuration.**
