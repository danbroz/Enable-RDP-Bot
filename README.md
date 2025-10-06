# Enable RDP Bot

## 🚀 Overview

A simple command-line tool for diagnosing and fixing RDP connectivity issues on Azure VMs using AI-powered analysis.

## ✨ Features

- **🔍 VM Diagnostics**: Check VM status, power state, and configuration
- **🌐 Network Analysis**: Analyze NSG rules and network connectivity
- **🧠 AI-Powered Analysis**: OpenAI GPT-5 integration for intelligent troubleshooting (with fallback to GPT-4)
- **☁️ Azure Native**: Built with Azure SDK and Azure CLI authentication
- **⚡ Simple & Fast**: Command-line tool with minimal setup

## 🎯 Documentation

This solution was created for a Microsoft Azure Supportability Test and includes:

- ✅ **Reference Architecture**: Simple CLI tool architecture ([docs/ARCHITECTURE.md](docs/ARCHITECTURE.md))
- ✅ **Customer Flow**: End-to-end troubleshooting workflow ([docs/ASSESSMENT_SUMMARY.md](docs/ASSESSMENT_SUMMARY.md))
- ✅ **Troubleshooting Playbook**: RDP diagnostic procedures ([docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md))
- ✅ **Safety & Security**: Secure API key management ([docs/SECURITY.md](docs/SECURITY.md))
- ✅ **Observability**: Logging and output options

## 🏗️ Architecture

![Enable RDP Bot Architecture](Diagram.png)

## 🚀 Quick Start

### Prerequisites

- Python 3.9+ (tested with Python 3.13)
- Azure subscription with appropriate permissions
- OpenAI API key
- Azure CLI (for authentication)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/danbroz/Enable-RDP-Bot.git
   cd Enable-RDP-Bot
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Authenticate with Azure:**
   ```bash
   az login
   az account set --subscription "your-subscription-id"
   ```


### Usage

```bash
python enable_rdp_bot.py --rg my-resource-group --vm my-vm-name
```

#### Command Line Options

- `--rg`: Azure resource group name (required)
- `--vm, -v`: Virtual machine name (required)

## 🧪 Testing

### Create Test VM

```bash
# Create a test VM with RDP issues
./create_example_vm.sh

# Test the tool
python enable_rdp_bot.py --rg example-resource-group --vm example-vm

# Clean up
./cleanup_example_vm.sh
```

## 🧠 AI-Powered Analysis

The tool automatically runs AI analysis using GPT-5 (with fallback to GPT-4) to identify root causes and provide recommendations.

### Model Selection
The tool automatically selects the best available model in this order:
1. **GPT-5** (preferred) - Latest model with enhanced reasoning capabilities
2. **GPT-4 Turbo** - High-performance model with extended context
3. **GPT-4** - Standard high-quality model
4. **GPT-3.5 Turbo** - Fast and efficient model

The tool automatically selects the best available model and provides detailed logging output.

## 📊 Output Format

The tool outputs JSON with the following structure:

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "vm_name": "my-vm",
  "resource_group": "my-rg",
  "vm_status": {
    "name": "my-vm",
    "power_state": "running",
    "vm_size": "Standard_B1s",
    "os_type": "Windows"
  },
  "nsg_info": {
    "rdp_allowed": true,
    "rules": [...]
  },
  "ai_analysis": {
    "root_cause": "VM is running and RDP is allowed",
    "fix_steps": ["No action needed"],
    "prevention": ["Monitor NSG rules"],
    "priority": "Low",
    "confidence": 0.95
  },
  "status": "completed"
}
```

## 🔧 Troubleshooting

### Common Issues

1. **Authentication Error**: Make sure you're logged in with `az login`
2. **OpenAI API Error**: Check your API key in the `.env` file
3. **VM Not Found**: Verify the resource group and VM name
4. **Permission Error**: Ensure you have appropriate Azure permissions

### Logs

The tool provides detailed logging output by default, showing all diagnostic steps and AI analysis.

## 🛡️ Security

- API keys are stored in `.env` file (not committed to git)
- Uses Azure CLI authentication (no hardcoded credentials)
- All API calls are logged for audit purposes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

### Assessment Documentation
- **[docs/ASSESSMENT_SUMMARY.md](docs/ASSESSMENT_SUMMARY.md)**: Complete assessment deliverables and requirements
- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**: Detailed system architecture and design
- **[docs/TROUBLESHOOTING_GUIDE.md](docs/TROUBLESHOOTING_GUIDE.md)**: Comprehensive RDP troubleshooting procedures
- **[docs/SECURITY.md](docs/SECURITY.md)**: Security and governance framework

### Quick Reference
- **Setup**: See [Quick Start](#-quick-start) section above
- **Usage**: See [Usage](#usage) section above
- **Troubleshooting**: See [Troubleshooting](#-troubleshooting) section above
