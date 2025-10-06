# Enable RDP Bot

## 🚀 Overview

A simple command-line tool for diagnosing and fixing RDP connectivity issues on Azure VMs using AI-powered analysis.

## ✨ Features

- **🔍 VM Diagnostics**: Check VM status, power state, and configuration
- **🌐 Network Analysis**: Analyze NSG rules and network connectivity
- **🧠 AI-Powered Analysis**: OpenAI GPT-4 integration for intelligent troubleshooting
- **☁️ Azure Native**: Built with Azure SDK and Azure CLI authentication
- **⚡ Simple & Fast**: Command-line tool with minimal setup

## 🎯 Assessment Deliverables

This solution was created for a Microsoft Azure Supportability Test and includes:

- ✅ **Reference Architecture**: Simple CLI tool architecture
- ✅ **Customer Flow**: End-to-end troubleshooting workflow
- ✅ **Troubleshooting Playbook**: RDP diagnostic procedures
- ✅ **Safety & Security**: Secure API key management
- ✅ **Observability**: Logging and output options

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Enable RDP Bot                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Azure     │  │   OpenAI    │  │   CLI       │    │
│  │   SDK       │  │   API       │  │   Tool      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   VM        │  │   Network   │  │   AI        │    │
│  │ Inspector   │  │   Analysis  │  │ Analysis    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
```

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

#### Basic Usage

```bash
python enable_rdp.py --resource-group my-resource-group --vm my-vm-name
```

#### Advanced Usage

```bash
# With auto-fix enabled
python enable_rdp.py --resource-group prod-rg --vm web-server-01 --auto-fix

# With verbose logging
python enable_rdp.py --resource-group test-rg --vm test-vm --verbose

# Save results to file
python enable_rdp.py --resource-group prod-rg --vm app-server --output report.json

# Specify subscription ID
python enable_rdp.py --resource-group my-rg --vm my-vm --subscription-id "your-subscription-id"
```

#### Command Line Options

- `--resource-group, -g`: Azure resource group name (required)
- `--vm, -v`: Virtual machine name (required)
- `--subscription-id, -s`: Azure subscription ID (optional, defaults to Azure CLI default)
- `--auto-fix, -a`: Automatically apply fixes (use with caution)
- `--verbose, -V`: Enable verbose logging
- `--output, -o`: Output file for results (JSON format)

## 🧪 Testing

### Create Test VM

```bash
# Create a test VM with RDP issues
./create_example_vm.sh

# Test the tool
python enable_rdp.py --resource-group example-resource-group --vm example-vm

# Clean up
./cleanup_example_vm.sh
```

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

The tool creates detailed logs in `rdp_troubleshooting.log` when using verbose mode.

## 🛡️ Security

- API keys are stored in `.env` file (not committed to git)
- Uses Azure CLI authentication (no hardcoded credentials)
- All API calls are logged for audit purposes

## 📝 License

This project is created for assessment purposes.

## 🤝 Contributing

This is an assessment project. For questions or issues, please contact the maintainer.

## 📞 Support

For technical support or questions about this assessment solution, please refer to the documentation or contact the development team.