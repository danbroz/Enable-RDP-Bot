#!/usr/bin/env python3
"""
Azure RDP Troubleshooting Agent
A command-line tool for diagnosing and fixing RDP connectivity issues on Azure VMs.

Usage:
    python enable_rdp.py --resource-group <rg-name> --vm <vm-name> [options]

Example:
    python enable_rdp.py --resource-group production-rg --vm web-server-01
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

# Add src to path for imports
sys.path.append('src')

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
import openai

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('rdp_troubleshooting.log')
    ]
)
logger = logging.getLogger(__name__)

class AzureRDPTroubleshooter:
    """Azure RDP Troubleshooting Agent"""
    
    def __init__(self, subscription_id: str, verbose: bool = False):
        self.subscription_id = subscription_id
        self.verbose = verbose
        
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        try:
            self.credential = DefaultAzureCredential()
            self.compute_client = ComputeManagementClient(self.credential, subscription_id)
            self.network_client = NetworkManagementClient(self.credential, subscription_id)
            self.resource_client = ResourceManagementClient(self.credential, subscription_id)
            logger.info(f"✅ Connected to Azure subscription: {subscription_id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Azure: {e}")
            raise

    async def diagnose_vm_status(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Diagnose VM power state and basic status"""
        try:
            logger.info(f"🔍 Checking VM status for {vm_name}...")
            
            vm_instance = self.compute_client.virtual_machines.instance_view(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            power_state = None
            provisioning_state = None
            
            for status in vm_instance.statuses:
                if status.code.startswith('PowerState/'):
                    power_state = status.display_status
                elif status.code.startswith('ProvisioningState/'):
                    provisioning_state = status.display_status
            
            result = {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "power_state": power_state,
                "provisioning_state": provisioning_state,
                "is_running": power_state == "VM running" if power_state else False,
                "statuses": [{"code": s.code, "display_status": s.display_status} for s in vm_instance.statuses]
            }
            
            logger.info(f"📊 VM Status: {power_state}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error checking VM status: {e}")
            return {
                "vm_name": vm_name,
                "resource_group": resource_group,
                "error": str(e),
                "is_running": False
            }

    async def diagnose_rdp_port(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Diagnose RDP port accessibility through NSG rules"""
        try:
            logger.info(f"🔍 Checking RDP port accessibility for {vm_name}...")
            
            # Get VM to find network interface
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Get network interface
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group,
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
                resource_group_name=resource_group,
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

    async def diagnose_network_connectivity(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Diagnose basic network connectivity"""
        try:
            logger.info(f"🔍 Checking network connectivity for {vm_name}...")
            
            # Get VM details
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Get network interface
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group,
                network_interface_name=nic_name
            )
            
            # Get public IP
            public_ip = None
            if nic.ip_configurations[0].public_ip_address:
                pip_name = nic.ip_configurations[0].public_ip_address.id.split('/')[-1]
                pip = self.network_client.public_ip_addresses.get(
                    resource_group_name=resource_group,
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

    async def get_ai_analysis(self, vm_status: Dict, nsg_status: Dict, connectivity_status: Dict) -> str:
        """Get AI-powered analysis of diagnostic results"""
        try:
            openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
            if not openai_api_key:
                return "AI analysis unavailable - OpenAI API key not configured"
            
            client = openai.OpenAI(api_key=openai_api_key)
            
            diagnostic_summary = f"""
            AZURE VM RDP DIAGNOSTIC RESULTS:
            
            VM STATUS:
            - VM Name: {vm_status.get('vm_name', 'Unknown')}
            - Power State: {vm_status.get('power_state', 'Unknown')}
            - Is Running: {vm_status.get('is_running', False)}
            - Error: {vm_status.get('error', 'None')}
            
            NETWORK SECURITY GROUP:
            - NSG Name: {nsg_status.get('nsg_name', 'None')}
            - RDP Allowed: {nsg_status.get('rdp_allowed', False)}
            - RDP Rules: {nsg_status.get('rdp_rules', [])}
            - Message: {nsg_status.get('message', 'None')}
            
            CONNECTIVITY:
            - Public IP: {connectivity_status.get('public_ip', 'None')}
            - Private IP: {connectivity_status.get('private_ip', 'None')}
            - Status: {connectivity_status.get('connectivity_status', 'Unknown')}
            """
            
            prompt = f"""
            You are an expert Azure support specialist. Analyze these VM RDP connectivity diagnostics and provide:
            
            1. ROOT CAUSE ANALYSIS: Identify the specific issues preventing RDP access
            2. REMEDIATION STEPS: Provide exact Azure CLI commands to fix each issue
            3. PREVENTION RECOMMENDATIONS: How to prevent these issues in the future
            
            {diagnostic_summary}
            
            Be specific and provide actionable Azure CLI commands.
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=800,
                    temperature=0.3
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"❌ AI analysis error: {e}")
            return f"AI analysis failed: {str(e)}"

    async def fix_rdp_issues(self, resource_group: str, vm_name: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Attempt to automatically fix common RDP issues"""
        fixes_applied = []
        
        try:
            # Check if VM is stopped and start it
            vm_status = await self.diagnose_vm_status(resource_group, vm_name)
            if not vm_status.get('is_running', False) and auto_fix:
                logger.info(f"🚀 Starting VM {vm_name}...")
                start_operation = self.compute_client.virtual_machines.begin_start(
                    resource_group_name=resource_group,
                    vm_name=vm_name
                )
                start_operation.result()
                fixes_applied.append("VM started")
                logger.info("✅ VM started successfully")
            
            # Check NSG rules and fix if needed
            nsg_status = await self.diagnose_rdp_port(resource_group, vm_name)
            if not nsg_status.get('rdp_allowed', False) and auto_fix:
                logger.info(f"🔧 Fixing NSG rules for {vm_name}...")
                # This would require more complex NSG rule management
                # For now, we'll just report what needs to be done
                fixes_applied.append("NSG rules need manual review")
                logger.warning("⚠️ NSG rules require manual intervention")
            
            return {
                "fixes_applied": fixes_applied,
                "status": "completed" if fixes_applied else "no_fixes_needed"
            }
            
        except Exception as e:
            logger.error(f"❌ Error applying fixes: {e}")
            return {
                "fixes_applied": [],
                "status": "failed",
                "error": str(e)
            }

    async def troubleshoot_rdp(self, resource_group: str, vm_name: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Main troubleshooting function"""
        logger.info(f"🚀 Starting RDP troubleshooting for VM: {vm_name}")
        logger.info(f"📋 Resource Group: {resource_group}")
        
        session_id = f"rdp_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            # Run diagnostics
            logger.info("🔍 Running comprehensive diagnostics...")
            
            vm_status_task = self.diagnose_vm_status(resource_group, vm_name)
            nsg_status_task = self.diagnose_rdp_port(resource_group, vm_name)
            connectivity_task = self.diagnose_network_connectivity(resource_group, vm_name)
            
            vm_status, nsg_status, connectivity_status = await asyncio.gather(
                vm_status_task, nsg_status_task, connectivity_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(vm_status, Exception):
                vm_status = {"error": str(vm_status), "vm_name": vm_name}
            if isinstance(nsg_status, Exception):
                nsg_status = {"error": str(nsg_status), "vm_name": vm_name}
            if isinstance(connectivity_status, Exception):
                connectivity_status = {"error": str(connectivity_status), "vm_name": vm_name}
            
            # Get AI analysis
            logger.info("🤖 Getting AI-powered analysis...")
            ai_analysis = await self.get_ai_analysis(vm_status, nsg_status, connectivity_status)
            
            # Apply fixes if requested
            fixes_result = None
            if auto_fix:
                logger.info("🔧 Applying automatic fixes...")
                fixes_result = await self.fix_rdp_issues(resource_group, vm_name, auto_fix)
            
            # Compile results
            results = {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "timestamp": datetime.now().isoformat(),
                "diagnostics": {
                    "vm_status": vm_status,
                    "nsg_status": nsg_status,
                    "connectivity_status": connectivity_status
                },
                "ai_analysis": ai_analysis,
                "fixes_applied": fixes_result,
                "status": "completed"
            }
            
            logger.info("✅ RDP troubleshooting completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error during troubleshooting: {e}")
            return {
                "session_id": session_id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "error": str(e),
                "status": "failed"
            }

def print_results(results: Dict[str, Any], verbose: bool = False):
    """Print troubleshooting results in a formatted way"""
    print("\n" + "="*60)
    print("🔍 AZURE RDP TROUBLESHOOTING RESULTS")
    print("="*60)
    
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
        
        if results.get("fixes_applied"):
            print(f"\n🔧 FIXES APPLIED:")
            fixes = results["fixes_applied"]
            for fix in fixes.get("fixes_applied", []):
                print(f"   ✅ {fix}")
        
        print(f"\n🤖 AI-POWERED ANALYSIS:")
        print("-" * 40)
        print(results["ai_analysis"])
        
        if verbose:
            print(f"\n📋 DETAILED RESULTS (JSON):")
            print(json.dumps(results, indent=2))
        
    else:
        print(f"❌ Troubleshooting failed: {results.get('error', 'Unknown error')}")
    
    print("\n" + "="*60)

async def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Azure RDP Troubleshooting Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enable_rdp.py --resource-group production-rg --vm web-server-01
  python enable_rdp.py --resource-group dev-rg --vm test-vm --auto-fix
  python enable_rdp.py --resource-group prod-rg --vm app-server --verbose
        """
    )
    
    parser.add_argument(
        "--resource-group", "-g",
        required=True,
        help="Azure resource group name"
    )
    
    parser.add_argument(
        "--vm", "-v",
        required=True,
        help="Azure VM name"
    )
    
    parser.add_argument(
        "--subscription-id", "-s",
        help="Azure subscription ID (default: from environment)"
    )
    
    parser.add_argument(
        "--auto-fix", "-f",
        action="store_true",
        help="Automatically apply fixes where possible"
    )
    
    parser.add_argument(
        "--verbose", "-V",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--output", "-o",
        choices=["console", "json"],
        default="console",
        help="Output format (default: console)"
    )
    
    args = parser.parse_args()
    
    # Get subscription ID
    subscription_id = args.subscription_id or os.getenv("AZURE_SUBSCRIPTION_ID")
    if not subscription_id:
        print("❌ Error: Azure subscription ID not provided")
        print("   Use --subscription-id or set AZURE_SUBSCRIPTION_ID environment variable")
        sys.exit(1)
    
    try:
        # Initialize troubleshooter
        troubleshooter = AzureRDPTroubleshooter(subscription_id, args.verbose)
        
        # Run troubleshooting
        results = await troubleshooter.troubleshoot_rdp(
            args.resource_group,
            args.vm,
            args.auto_fix
        )
        
        # Output results
        if args.output == "json":
            print(json.dumps(results, indent=2))
        else:
            print_results(results, args.verbose)
        
        # Exit with appropriate code
        if results["status"] == "completed":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
