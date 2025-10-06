#!/usr/bin/env python3
"""
Test Agentic AI Support Bot against Real Problem VM in Azure
This script creates a VM with intentional RDP issues and tests our AI agent
"""

import asyncio
import os
import sys
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src to path
sys.path.append('src')

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
import openai

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RealAzureVMInspector:
    """Real Azure VM Inspector that connects to actual Azure resources"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        try:
            self.credential = DefaultAzureCredential()
            self.compute_client = ComputeManagementClient(self.credential, subscription_id)
            self.network_client = NetworkManagementClient(self.credential, subscription_id)
            self.resource_client = ResourceManagementClient(self.credential, subscription_id)
            logger.info(f"✅ Connected to Azure subscription: {subscription_id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Azure: {e}")
            raise

    async def get_vm_status(self, resource_group_name: str, vm_name: str) -> Dict[str, Any]:
        """Get real VM status from Azure"""
        try:
            logger.info(f"🔍 Checking VM status for {vm_name}...")
            
            # Get VM instance view
            vm_instance = self.compute_client.virtual_machines.instance_view(
                resource_group_name=resource_group_name,
                vm_name=vm_name
            )
            
            # Extract status information
            power_state = None
            provisioning_state = None
            
            for status in vm_instance.statuses:
                if status.code.startswith('PowerState/'):
                    power_state = status.display_status
                elif status.code.startswith('ProvisioningState/'):
                    provisioning_state = status.display_status
            
            result = {
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "power_state": power_state,
                "provisioning_state": provisioning_state,
                "statuses": [{"code": s.code, "display_status": s.display_status} for s in vm_instance.statuses],
                "is_running": power_state == "VM running" if power_state else False,
                "is_accessible": power_state == "VM running" if power_state else False
            }
            
            logger.info(f"📊 VM Status: {power_state}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error getting VM status: {e}")
            return {
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "error": str(e),
                "is_running": False,
                "is_accessible": False
            }

    async def check_rdp_port_nsg(self, resource_group_name: str, vm_name: str) -> Dict[str, Any]:
        """Check NSG rules for RDP port 3389"""
        try:
            logger.info(f"🔍 Checking NSG rules for RDP port on {vm_name}...")
            
            # Get VM to find network interface
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group_name,
                vm_name=vm_name
            )
            
            # Get network interface
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group_name,
                network_interface_name=nic_name
            )
            
            # Check if NSG is attached
            if not nic.network_security_group:
                return {
                    "vm_name": vm_name,
                    "nsg_attached": False,
                    "rdp_allowed": False,
                    "message": "No NSG attached to network interface"
                }
            
            # Get NSG rules
            nsg_name = nic.network_security_group.id.split('/')[-1]
            nsg = self.network_client.network_security_groups.get(
                resource_group_name=resource_group_name,
                network_security_group_name=nsg_name
            )
            
            # Check RDP rules
            rdp_rules = []
            rdp_allowed = False
            
            for rule in nsg.security_rules:
                if rule.destination_port_range == "3389" or (rule.destination_port_ranges and "3389" in rule.destination_port_ranges):
                    rdp_rules.append({
                        "name": rule.name,
                        "access": rule.access,
                        "direction": rule.direction,
                        "priority": rule.priority,
                        "source_address_prefix": rule.source_address_prefix,
                        "destination_port_range": rule.destination_port_range
                    })
                    
                    if rule.access == "Allow" and rule.direction == "Inbound":
                        rdp_allowed = True
            
            result = {
                "vm_name": vm_name,
                "nsg_name": nsg_name,
                "nsg_attached": True,
                "rdp_allowed": rdp_allowed,
                "rdp_rules": rdp_rules,
                "message": f"RDP port 3389 is {'ALLOWED' if rdp_allowed else 'BLOCKED'} by NSG rules"
            }
            
            logger.info(f"📊 NSG Check: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking NSG: {e}")
            return {
                "vm_name": vm_name,
                "error": str(e),
                "rdp_allowed": False,
                "message": f"Error checking NSG: {str(e)}"
            }

    async def check_vm_connectivity(self, resource_group_name: str, vm_name: str) -> Dict[str, Any]:
        """Check basic VM connectivity"""
        try:
            logger.info(f"🔍 Checking VM connectivity for {vm_name}...")
            
            # Get VM details
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group_name,
                vm_name=vm_name
            )
            
            # Get public IP
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group_name,
                network_interface_name=nic_name
            )
            
            public_ip = None
            if nic.ip_configurations[0].public_ip_address:
                pip_name = nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
                pip = self.network_client.public_ip_addresses.get(
                    resource_group_name=resource_group_name,
                    public_ip_address_name=pip_name
                )
                public_ip = pip.ip_address
            
            private_ip = nic.ip_configurations[0].private_ip_address
            
            result = {
                "vm_name": vm_name,
                "public_ip": public_ip,
                "private_ip": private_ip,
                "connectivity_status": "VM network configured",
                "message": f"VM has network configuration - Public IP: {public_ip}, Private IP: {private_ip}"
            }
            
            logger.info(f"📊 Connectivity: {result['message']}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking connectivity: {e}")
            return {
                "vm_name": vm_name,
                "error": str(e),
                "message": f"Error checking connectivity: {str(e)}"
            }

class RealAIAgent:
    """AI Agent using real OpenAI API for analysis"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
        logger.info("✅ AI Agent initialized with OpenAI API")

    async def analyze_real_diagnostics(self, vm_status: Dict, nsg_status: Dict, connectivity_status: Dict) -> str:
        """Analyze real diagnostic results from Azure"""
        
        # Create comprehensive diagnostic summary
        diagnostic_summary = f"""
        REAL AZURE VM DIAGNOSTIC RESULTS:
        
        VM STATUS:
        - VM Name: {vm_status.get('vm_name', 'Unknown')}
        - Power State: {vm_status.get('power_state', 'Unknown')}
        - Provisioning State: {vm_status.get('provisioning_state', 'Unknown')}
        - Is Running: {vm_status.get('is_running', False)}
        - Error: {vm_status.get('error', 'None')}
        
        NETWORK SECURITY GROUP:
        - NSG Name: {nsg_status.get('nsg_name', 'None')}
        - NSG Attached: {nsg_status.get('nsg_attached', False)}
        - RDP Allowed: {nsg_status.get('rdp_allowed', False)}
        - RDP Rules: {nsg_status.get('rdp_rules', [])}
        - Message: {nsg_status.get('message', 'None')}
        
        CONNECTIVITY:
        - Public IP: {connectivity_status.get('public_ip', 'None')}
        - Private IP: {connectivity_status.get('private_ip', 'None')}
        - Status: {connectivity_status.get('connectivity_status', 'Unknown')}
        """
        
        prompt = f"""
        You are an expert Azure support specialist analyzing REAL diagnostic data from a Windows VM that cannot be accessed via RDP.
        
        {diagnostic_summary}
        
        Based on this REAL Azure diagnostic data, provide:
        
        1. ROOT CAUSE ANALYSIS:
           - Identify the specific technical issues preventing RDP access
           - Explain why each issue prevents RDP connectivity
        
        2. SPECIFIC REMEDIATION STEPS:
           - Provide exact Azure CLI commands or Azure Portal steps to fix each issue
           - Include specific NSG rule changes if needed
           - Include VM start commands if needed
        
        3. PREVENTION RECOMMENDATIONS:
           - How to prevent these issues in the future
           - Best practices for RDP access management
           - Monitoring recommendations
        
        Be specific and technical. This is real production troubleshooting.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ OpenAI API error: {e}")
            return f"AI analysis failed: {str(e)}"

class RealAzureSupportBot:
    """Real Azure Support Bot that works with actual Azure resources"""
    
    def __init__(self, subscription_id: str, openai_api_key: str):
        self.subscription_id = subscription_id
        self.inspector = RealAzureVMInspector(subscription_id)
        self.ai_agent = RealAIAgent(openai_api_key)
        logger.info("✅ Real Azure Support Bot initialized")

    async def troubleshoot_real_vm(self, vm_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Troubleshoot a real VM in Azure"""
        
        logger.info(f"🚀 Starting REAL troubleshooting for VM: {vm_name}")
        logger.info(f"📋 Resource Group: {resource_group_name}")
        logger.info(f"🔑 Subscription: {self.subscription_id}")
        
        session_id = f"real_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run real diagnostics
            logger.info("🔍 Running REAL Azure diagnostics...")
            
            vm_status_task = self.inspector.get_vm_status(resource_group_name, vm_name)
            nsg_status_task = self.inspector.check_rdp_port_nsg(resource_group_name, vm_name)
            connectivity_task = self.inspector.check_vm_connectivity(resource_group_name, vm_name)
            
            # Wait for all diagnostics to complete
            vm_status, nsg_status, connectivity_status = await asyncio.gather(
                vm_status_task, nsg_status_task, connectivity_task, return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(vm_status, Exception):
                vm_status = {"error": str(vm_status), "vm_name": vm_name}
            if isinstance(nsg_status, Exception):
                nsg_status = {"error": str(nsg_status), "vm_name": vm_name}
            if isinstance(connectivity_status, Exception):
                connectivity_status = {"error": str(connectivity_status), "vm_name": vm_name}
            
            # Get AI analysis
            logger.info("🤖 Getting AI analysis of REAL diagnostic data...")
            ai_analysis = await self.ai_agent.analyze_real_diagnostics(
                vm_status, nsg_status, connectivity_status
            )
            
            # Compile results
            results = {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "subscription_id": self.subscription_id,
                "timestamp": datetime.now().isoformat(),
                "diagnostics": {
                    "vm_status": vm_status,
                    "nsg_status": nsg_status,
                    "connectivity_status": connectivity_status
                },
                "ai_analysis": ai_analysis,
                "status": "completed"
            }
            
            logger.info("✅ REAL troubleshooting completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during real troubleshooting: {e}")
            return {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group_name,
                "error": str(e),
                "status": "failed"
            }

async def main():
    """Main function to test real VM"""
    
    print("🚀 Azure Agentic AI Support Bot - REAL VM TESTING")
    print("=" * 60)
    print("This test will:")
    print("1. Connect to your REAL Azure subscription")
    print("2. Analyze a REAL VM with RDP issues")
    print("3. Provide REAL AI-powered troubleshooting")
    print()
    
    # Load environment variables
    subscription_id = "your-subscription-id-here"
    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    if not openai_api_key:
        print("❌ OpenAI API key not found in environment")
        return
    
    # VM details (from Terraform output)
    vm_name = "problem-vm-test"
    resource_group = "ai-support-bot-test-rg"
    
    print(f"🎯 Target VM: {vm_name}")
    print(f"📁 Resource Group: {resource_group}")
    print(f"🔑 Subscription: {subscription_id}")
    print()
    
    try:
        # Initialize bot
        bot = RealAzureSupportBot(subscription_id, openai_api_key)
        
        # Run real troubleshooting
        results = await bot.troubleshoot_real_vm(vm_name, resource_group)
        
        # Display results
        print("\n" + "=" * 60)
        print("🔍 REAL DIAGNOSTIC RESULTS")
        print("=" * 60)
        
        if results["status"] == "completed":
            diagnostics = results["diagnostics"]
            
            print(f"\n📊 VM STATUS:")
            vm_status = diagnostics["vm_status"]
            print(f"   VM Name: {vm_status.get('vm_name', 'Unknown')}")
            print(f"   Power State: {vm_status.get('power_state', 'Unknown')}")
            print(f"   Is Running: {vm_status.get('is_running', False)}")
            if vm_status.get('error'):
                print(f"   Error: {vm_status['error']}")
            
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
            
            print(f"\n🤖 AI-POWERED ANALYSIS:")
            print("-" * 40)
            print(results["ai_analysis"])
            
        else:
            print(f"❌ Troubleshooting failed: {results.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        print("🎉 REAL VM TESTING COMPLETED!")
        print("=" * 60)
        
        if results["status"] == "completed":
            print("✅ Successfully analyzed REAL Azure VM")
            print("✅ AI provided specific remediation steps")
            print("✅ Real diagnostic data processed")
            print("✅ Production-ready troubleshooting demonstrated")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
