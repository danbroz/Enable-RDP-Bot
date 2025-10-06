#!/usr/bin/env python3
"""
Demo script for enable_rdp.py
Shows how to use the Azure RDP Troubleshooting Agent
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

async def demo_enable_rdp():
    """Demonstrate the enable_rdp.py functionality"""
    
    print("🚀 Azure RDP Troubleshooting Agent - Demo")
    print("=" * 50)
    print("This demo shows how to use the enable_rdp.py command-line tool")
    print()
    
    # Example usage scenarios
    examples = [
        {
            "description": "Basic RDP troubleshooting",
            "command": "python3 enable_rdp.py --resource-group production-rg --vm web-server-01",
            "explanation": "Diagnose RDP issues on a specific VM"
        },
        {
            "description": "Auto-fix RDP issues",
            "command": "python3 enable_rdp.py --resource-group dev-rg --vm test-vm --auto-fix",
            "explanation": "Automatically fix common RDP issues (start VM, etc.)"
        },
        {
            "description": "Verbose troubleshooting",
            "command": "python3 enable_rdp.py --resource-group prod-rg --vm app-server --verbose",
            "explanation": "Get detailed diagnostic information"
        },
        {
            "description": "JSON output for automation",
            "command": "python3 enable_rdp.py --resource-group staging-rg --vm db-server --output json",
            "explanation": "Get results in JSON format for scripting"
        }
    ]
    
    print("📋 Usage Examples:")
    print("-" * 30)
    
    for i, example in enumerate(examples, 1):
        print(f"\n{i}. {example['description']}")
        print(f"   Command: {example['command']}")
        print(f"   Purpose: {example['explanation']}")
    
    print(f"\n🔧 Command-Line Options:")
    print("-" * 30)
    print("  --resource-group, -g    Azure resource group name (required)")
    print("  --vm, -v               Azure VM name (required)")
    print("  --subscription-id, -s  Azure subscription ID (optional)")
    print("  --auto-fix, -f         Automatically apply fixes")
    print("  --verbose, -V          Enable verbose output")
    print("  --output, -o           Output format (console/json)")
    
    print(f"\n🔐 Authentication:")
    print("-" * 30)
    print("The tool uses Azure Default Credential Chain:")
    print("1. Environment variables (AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, etc.)")
    print("2. Azure CLI authentication (az login)")
    print("3. Managed Identity (if running in Azure)")
    print("4. Visual Studio Code authentication")
    
    print(f"\n📊 What the tool does:")
    print("-" * 30)
    print("1. 🔍 Diagnoses VM power state")
    print("2. 🔒 Checks Network Security Group rules for RDP port 3389")
    print("3. 🌐 Verifies network connectivity configuration")
    print("4. 🤖 Provides AI-powered analysis and recommendations")
    print("5. 🔧 Optionally applies automatic fixes")
    
    print(f"\n📋 Sample Output:")
    print("-" * 30)
    print("""
🔍 AZURE RDP TROUBLESHOOTING RESULTS
============================================================

📊 VM STATUS:
   VM Name: web-server-01
   Power State: VM deallocated
   Is Running: False

🔒 NETWORK SECURITY GROUP:
   NSG Name: web-server-01-nsg
   RDP Allowed: False
   Message: RDP port 3389 is BLOCKED by NSG rules

🌐 CONNECTIVITY:
   Public IP: 20.123.45.67
   Private IP: 10.0.1.4
   Status: VM network configured

🤖 AI-POWERED ANALYSIS:
----------------------------------------
1. ROOT CAUSE ANALYSIS:
   The VM is deallocated and RDP port 3389 is blocked by NSG rules.

2. REMEDIATION STEPS:
   - Start the VM: az vm start --name web-server-01 --resource-group production-rg
   - Fix NSG rules: az network nsg rule create --name AllowRDP --nsg-name web-server-01-nsg --resource-group production-rg --priority 1000 --direction Inbound --access Allow --protocol Tcp --destination-port-range 3389

3. PREVENTION RECOMMENDATIONS:
   - Set up monitoring alerts for VM status changes
   - Review NSG rules regularly
   - Use Azure Bastion for secure RDP access
============================================================
    """)
    
    print(f"\n🎯 Real-World Usage:")
    print("-" * 30)
    print("This tool is perfect for:")
    print("• Azure administrators troubleshooting RDP issues")
    print("• DevOps teams automating VM diagnostics")
    print("• Support teams providing quick RDP fixes")
    print("• CI/CD pipelines checking VM accessibility")
    print("• Incident response for VM connectivity issues")
    
    print(f"\n🚀 Ready to use!")
    print("=" * 50)
    print("The enable_rdp.py tool is ready for production use.")
    print("Make sure you have:")
    print("✅ Azure credentials configured")
    print("✅ OpenAI API key set (for AI analysis)")
    print("✅ Appropriate Azure permissions")
    print()
    print("Try it out with your own VMs!")

if __name__ == "__main__":
    asyncio.run(demo_enable_rdp())
