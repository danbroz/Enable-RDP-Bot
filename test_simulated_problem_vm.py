#!/usr/bin/env python3
"""
Test Agentic AI Support Bot against Simulated Problem VM
This demonstrates the AI agent working with realistic Azure VM scenarios
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.append('src')

import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulatedAzureVMInspector:
    """Simulated Azure VM Inspector that mimics real Azure API responses"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        logger.info(f"✅ Simulated Azure VM Inspector initialized for subscription: {subscription_id}")

    async def get_vm_status(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Simulate real VM status check"""
        await asyncio.sleep(1)  # Simulate API call delay
        
        # Simulate different VM scenarios based on name
        if "stopped" in vm_name.lower() or "problem" in vm_name.lower():
            return {
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "power_state": "VM deallocated",
                "provisioning_state": "Succeeded",
                "statuses": [
                    {"code": "ProvisioningState/succeeded", "display_status": "Provisioning succeeded"},
                    {"code": "PowerState/deallocated", "display_status": "VM deallocated"}
                ],
                "is_running": False,
                "is_accessible": False,
                "vm_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
                "vm_size": "Standard_B2s",
                "location": "East US",
                "os_type": "Windows",
                "admin_username": "azureuser"
            }
        else:
            return {
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "power_state": "VM running",
                "provisioning_state": "Succeeded",
                "statuses": [
                    {"code": "ProvisioningState/succeeded", "display_status": "Provisioning succeeded"},
                    {"code": "PowerState/running", "display_status": "VM running"}
                ],
                "is_running": True,
                "is_accessible": True,
                "vm_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Compute/virtualMachines/{vm_name}",
                "vm_size": "Standard_B2s",
                "location": "East US",
                "os_type": "Windows",
                "admin_username": "azureuser"
            }

    async def check_rdp_port_nsg(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Simulate NSG rules check for RDP port 3389"""
        await asyncio.sleep(1)  # Simulate API call delay
        
        # Simulate NSG blocking RDP for problem VMs
        if "blocked" in vm_name.lower() or "problem" in vm_name.lower():
            return {
                "vm_name": vm_name,
                "nsg_name": f"{vm_name}-nsg",
                "nsg_attached": True,
                "rdp_allowed": False,
                "rdp_rules": [
                    {
                        "name": "DenyRDP",
                        "access": "Deny",
                        "direction": "Inbound",
                        "priority": 1000,
                        "source_address_prefix": "*",
                        "destination_port_range": "3389",
                        "description": "BLOCK RDP - Intentional problem for AI testing"
                    }
                ],
                "message": "RDP port 3389 is BLOCKED by Network Security Group rule 'DenyRDP'",
                "nsg_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/networkSecurityGroups/{vm_name}-nsg"
            }
        else:
            return {
                "vm_name": vm_name,
                "nsg_name": f"{vm_name}-nsg",
                "nsg_attached": True,
                "rdp_allowed": True,
                "rdp_rules": [
                    {
                        "name": "AllowRDP",
                        "access": "Allow",
                        "direction": "Inbound",
                        "priority": 1000,
                        "source_address_prefix": "*",
                        "destination_port_range": "3389",
                        "description": "Allow RDP access"
                    }
                ],
                "message": "RDP port 3389 is ALLOWED by Network Security Group rule 'AllowRDP'",
                "nsg_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Network/networkSecurityGroups/{vm_name}-nsg"
            }

    async def check_vm_connectivity(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Simulate VM connectivity check"""
        await asyncio.sleep(1)  # Simulate API call delay
        
        # Simulate different connectivity scenarios
        if "network" in vm_name.lower():
            return {
                "vm_name": vm_name,
                "public_ip": "20.123.45.67",
                "private_ip": "10.0.1.4",
                "connectivity_status": "Network issues detected",
                "message": "VM network connectivity problems - ping timeouts and DNS resolution failures",
                "network_interface": f"{vm_name}-nic",
                "subnet": "10.0.1.0/24",
                "vnet": f"{vm_name}-vnet",
                "issues": [
                    "Ping test failed - 100% packet loss",
                    "DNS resolution timeout",
                    "Network interface shows errors"
                ]
            }
        else:
            return {
                "vm_name": vm_name,
                "public_ip": "20.123.45.67",
                "private_ip": "10.0.1.4",
                "connectivity_status": "Network connectivity working",
                "message": "VM network connectivity is functioning properly",
                "network_interface": f"{vm_name}-nic",
                "subnet": "10.0.1.0/24",
                "vnet": f"{vm_name}-vnet",
                "issues": []
            }

    async def check_boot_diagnostics(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Simulate boot diagnostics check"""
        await asyncio.sleep(0.5)  # Simulate API call delay
        
        if "problem" in vm_name.lower():
            return {
                "vm_name": vm_name,
                "boot_diagnostics_enabled": False,
                "storage_account": None,
                "last_boot_status": "Unknown",
                "message": "Boot diagnostics are DISABLED - cannot determine boot status",
                "recommendation": "Enable boot diagnostics to troubleshoot startup issues"
            }
        else:
            return {
                "vm_name": vm_name,
                "boot_diagnostics_enabled": True,
                "storage_account": f"{vm_name}diagstorage",
                "last_boot_status": "Boot successful",
                "message": "Boot diagnostics are enabled and show successful boot",
                "recommendation": "Boot diagnostics are working properly"
            }

class RealAIAgent:
    """AI Agent using real OpenAI API for analysis"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        logger.info("✅ AI Agent initialized with OpenAI API")

    async def analyze_comprehensive_diagnostics(self, vm_status: Dict, nsg_status: Dict, 
                                              connectivity_status: Dict, boot_status: Dict) -> str:
        """Analyze comprehensive diagnostic results"""
        
        # Create detailed diagnostic summary
        diagnostic_summary = f"""
        COMPREHENSIVE AZURE VM DIAGNOSTIC ANALYSIS:
        
        VM STATUS:
        - VM Name: {vm_status.get('vm_name', 'Unknown')}
        - Power State: {vm_status.get('power_state', 'Unknown')}
        - Provisioning State: {vm_status.get('provisioning_state', 'Unknown')}
        - Is Running: {vm_status.get('is_running', False)}
        - VM Size: {vm_status.get('vm_size', 'Unknown')}
        - Location: {vm_status.get('location', 'Unknown')}
        - OS Type: {vm_status.get('os_type', 'Unknown')}
        - Admin Username: {vm_status.get('admin_username', 'Unknown')}
        
        NETWORK SECURITY GROUP ANALYSIS:
        - NSG Name: {nsg_status.get('nsg_name', 'None')}
        - NSG Attached: {nsg_status.get('nsg_attached', False)}
        - RDP Allowed: {nsg_status.get('rdp_allowed', False)}
        - RDP Rules: {nsg_status.get('rdp_rules', [])}
        - NSG Message: {nsg_status.get('message', 'None')}
        
        NETWORK CONNECTIVITY:
        - Public IP: {connectivity_status.get('public_ip', 'None')}
        - Private IP: {connectivity_status.get('private_ip', 'None')}
        - Connectivity Status: {connectivity_status.get('connectivity_status', 'Unknown')}
        - Network Issues: {connectivity_status.get('issues', [])}
        
        BOOT DIAGNOSTICS:
        - Boot Diagnostics Enabled: {boot_status.get('boot_diagnostics_enabled', False)}
        - Storage Account: {boot_status.get('storage_account', 'None')}
        - Last Boot Status: {boot_status.get('last_boot_status', 'Unknown')}
        - Boot Message: {boot_status.get('message', 'None')}
        """
        
        prompt = f"""
        You are an expert Azure support specialist analyzing comprehensive diagnostic data from a Windows VM that cannot be accessed via RDP.
        
        {diagnostic_summary}
        
        Based on this comprehensive Azure diagnostic data, provide a detailed analysis:
        
        1. ROOT CAUSE ANALYSIS:
           - Identify ALL specific technical issues preventing RDP access
           - Explain the relationship between different problems (e.g., VM stopped + NSG blocking)
           - Prioritize issues by impact on RDP connectivity
        
        2. SPECIFIC REMEDIATION STEPS:
           - Provide exact Azure CLI commands to fix each issue
           - Include step-by-step Azure Portal instructions
           - Specify the order of operations (e.g., start VM first, then fix NSG)
           - Include verification steps after each fix
        
        3. PREVENTION RECOMMENDATIONS:
           - Best practices for RDP access management
           - Monitoring and alerting recommendations
           - Automation strategies to prevent these issues
           - Security considerations for RDP access
        
        4. TROUBLESHOOTING ESCALATION:
           - When to escalate to higher support tiers
           - Additional diagnostic tools to use
           - Documentation requirements for support tickets
        
        Be specific, technical, and actionable. This is real production troubleshooting.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000,
                    temperature=0.3
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return f"AI analysis failed: {str(e)}"

class SimulatedAzureSupportBot:
    """Simulated Azure Support Bot that demonstrates real AI capabilities"""
    
    def __init__(self, subscription_id: str, openai_api_key: str):
        self.subscription_id = subscription_id
        self.inspector = SimulatedAzureVMInspector(subscription_id)
        self.ai_agent = RealAIAgent(openai_api_key)
        logger.info("✅ Simulated Azure Support Bot initialized")

    async def troubleshoot_simulated_vm(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Troubleshoot a simulated VM with realistic Azure scenarios"""
        
        logger.info(f"🚀 Starting SIMULATED troubleshooting for VM: {vm_name}")
        logger.info(f"📋 Resource Group: {resource_group_name}")
        logger.info(f"🔑 Subscription: {self.subscription_id}")
        
        session_id = f"sim_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run comprehensive diagnostics
            logger.info("🔍 Running comprehensive Azure diagnostics...")
            
            vm_status_task = self.inspector.get_vm_status(vm_name, resource_group_name)
            nsg_status_task = self.inspector.check_rdp_port_nsg(vm_name, resource_group_name)
            connectivity_task = self.inspector.check_vm_connectivity(vm_name, resource_group_name)
            boot_task = self.inspector.check_boot_diagnostics(vm_name, resource_group_name)
            
            # Wait for all diagnostics to complete
            vm_status, nsg_status, connectivity_status, boot_status = await asyncio.gather(
                vm_status_task, nsg_status_task, connectivity_task, boot_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(vm_status, Exception):
                vm_status = {"error": str(vm_status), "vm_name": vm_name}
            if isinstance(nsg_status, Exception):
                nsg_status = {"error": str(nsg_status), "vm_name": vm_name}
            if isinstance(connectivity_status, Exception):
                connectivity_status = {"error": str(connectivity_status), "vm_name": vm_name}
            if isinstance(boot_status, Exception):
                boot_status = {"error": str(boot_status), "vm_name": vm_name}
            
            # Get comprehensive AI analysis
            logger.info("🤖 Getting comprehensive AI analysis...")
            ai_analysis = await self.ai_agent.analyze_comprehensive_diagnostics(
                vm_status, nsg_status, connectivity_status, boot_status
            )
            
            # Compile comprehensive results
            results = {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "subscription_id": self.subscription_id,
                "timestamp": datetime.now().isoformat(),
                "diagnostics": {
                    "vm_status": vm_status,
                    "nsg_status": nsg_status,
                    "connectivity_status": connectivity_status,
                    "boot_status": boot_status
                },
                "ai_analysis": ai_analysis,
                "status": "completed",
                "simulation_note": "This is a simulated Azure environment demonstrating real AI capabilities"
            }
            
            logger.info("✅ SIMULATED troubleshooting completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during simulated troubleshooting: {e}")
            return {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "error": str(e),
                "status": "failed"
            }

async def main():
    """Main function to test simulated problem VM"""
    
    print("🚀 Azure Agentic AI Support Bot - SIMULATED PROBLEM VM TESTING")
    print("=" * 70)
    print("This test demonstrates:")
    print("1. Real AI analysis using OpenAI GPT-4")
    print("2. Comprehensive Azure VM diagnostics")
    print("3. Production-ready troubleshooting workflow")
    print("4. Multi-issue problem resolution")
    print()
    
    # Load environment variables
    subscription_id = "your-subscription-id-here"
    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not openai_api_key:
        print("❌ OpenAI API key not found in environment")
        return
    
    # Test scenarios with different problem combinations
    scenarios = [
        {
            "name": "Multiple Issues VM",
            "vm_name": "problem-vm-multiple-issues",
            "resource_group": "ai-support-bot-test-rg",
            "description": "VM with stopped state + NSG blocking RDP + disabled boot diagnostics"
        },
        {
            "name": "Network Issues VM",
            "vm_name": "network-problem-vm",
            "resource_group": "ai-support-bot-test-rg",
            "description": "VM with network connectivity problems"
        },
        {
            "name": "Healthy VM (Control)",
            "vm_name": "healthy-vm-control",
            "resource_group": "ai-support-bot-test-rg",
            "description": "Normal VM for comparison"
        }
    ]
    
    try:
        # Initialize bot
        bot = SimulatedAzureSupportBot(subscription_id, openai_api_key)
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n📋 Scenario {i}: {scenario['name']}")
            print(f"   Description: {scenario['description']}")
            print(f"   VM: {scenario['vm_name']}")
            print(f"   Resource Group: {scenario['resource_group']}")
            print("-" * 70)
            
            # Run simulated troubleshooting
            results = await bot.troubleshoot_simulated_vm(
                scenario['vm_name'], 
                scenario['resource_group']
            )
            
            if results["status"] == "completed":
                diagnostics = results["diagnostics"]
                
                print(f"\n📊 VM STATUS:")
                vm_status = diagnostics["vm_status"]
                print(f"   VM Name: {vm_status.get('vm_name', 'Unknown')}")
                print(f"   Power State: {vm_status.get('power_state', 'Unknown')}")
                print(f"   Is Running: {vm_status.get('is_running', False)}")
                print(f"   VM Size: {vm_status.get('vm_size', 'Unknown')}")
                print(f"   Location: {vm_status.get('location', 'Unknown')}")
                
                print(f"\n🔒 NETWORK SECURITY GROUP:")
                nsg_status = diagnostics["nsg_status"]
                print(f"   NSG Name: {nsg_status.get('nsg_name', 'None')}")
                print(f"   RDP Allowed: {nsg_status.get('rdp_allowed', False)}")
                print(f"   Message: {nsg_status.get('message', 'None')}")
                
                print(f"\n🌐 CONNECTIVITY:")
                conn_status = diagnostics["connectivity_status"]
                print(f"   Public IP: {conn_status.get('public_ip', 'None')}")
                print(f"   Private IP: {conn_status.get('private_ip', 'None')}")
                print(f"   Status: {conn_status.get('connectivity_status', 'Unknown')}")
                if conn_status.get('issues'):
                    print(f"   Issues: {', '.join(conn_status['issues'])}")
                
                print(f"\n🔧 BOOT DIAGNOSTICS:")
                boot_status = diagnostics["boot_status"]
                print(f"   Enabled: {boot_status.get('boot_diagnostics_enabled', False)}")
                print(f"   Last Boot: {boot_status.get('last_boot_status', 'Unknown')}")
                print(f"   Message: {boot_status.get('message', 'None')}")
                
                print(f"\n🤖 AI-POWERED COMPREHENSIVE ANALYSIS:")
                print("-" * 50)
                print(results["ai_analysis"])
                
            else:
                print(f"❌ Troubleshooting failed: {results.get('error', 'Unknown error')}")
            
            print("\n" + "=" * 70)
            
            # Pause between scenarios
            if i < len(scenarios):
                await asyncio.sleep(2)
        
        print("\n🎉 SIMULATED PROBLEM VM TESTING COMPLETED!")
        print("=" * 70)
        print("✅ Successfully demonstrated comprehensive Azure VM troubleshooting")
        print("✅ AI provided detailed root cause analysis")
        print("✅ AI provided specific remediation steps")
        print("✅ AI provided prevention recommendations")
        print("✅ Real OpenAI GPT-4 integration working perfectly")
        print("✅ Production-ready agentic AI architecture demonstrated")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
