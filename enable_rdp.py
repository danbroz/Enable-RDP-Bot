#!/usr/bin/env python3
"""
Enable RDP Bot
A command-line tool for diagnosing and fixing RDP connectivity issues on Azure VMs.

Usage:
    python enable_rdp.py --rg <rg-name> --vm <vm-name>

Example:
    python enable_rdp.py --rg production-rg --vm web-server-01
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
import openai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging (always verbose)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AzureRDPTroubleshooter:
    """Azure RDP Troubleshooting Agent"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        
        # Initialize Azure clients
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.network_client = NetworkManagementClient(self.credential, subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)
        
        # Initialize OpenAI client
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Check available models and verify GPT-5 availability
        self.available_models = self.check_available_models()
        self.model = self.select_best_model()
    
    def check_available_models(self) -> List[str]:
        """Check available OpenAI models via API"""
        try:
            models = self.openai_client.models.list()
            available_models = [model.id for model in models.data]
            logger.info(f"Available OpenAI models: {available_models}")
            return available_models
        except Exception as e:
            logger.warning(f"Could not fetch available models: {e}")
            return []
    
    def select_best_model(self) -> str:
        """Select the best available model, preferring GPT-5"""
        preferred_models = ["gpt-5", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        for model in preferred_models:
            if model in self.available_models:
                logger.info(f"Selected model: {model}")
                return model
        
        # Fallback to first available model
        if self.available_models:
            fallback_model = self.available_models[0]
            logger.warning(f"Using fallback model: {fallback_model}")
            return fallback_model
        
        # Ultimate fallback
        logger.error("No OpenAI models available, using gpt-4 as fallback")
        return "gpt-4"
    
    def get_vm_status(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Get VM status and basic information"""
        try:
            vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
            instance_view = self.compute_client.virtual_machines.instance_view(resource_group, vm_name)
            
            status = {
                'name': vm.name,
                'location': vm.location,
                'vm_size': vm.hardware_profile.vm_size,
                'os_type': str(vm.storage_profile.os_disk.os_type) if vm.storage_profile.os_disk.os_type else 'Unknown',
                'power_state': 'Unknown',
                'provisioning_state': vm.provisioning_state,
                'network_interfaces': [nic.id for nic in vm.network_profile.network_interfaces]
            }
            
            # Get power state from instance view
            for status_info in instance_view.statuses:
                if status_info.code.startswith('PowerState/'):
                    status['power_state'] = status_info.code.split('/')[1]
                    break
            
            return status
        except Exception as e:
            logger.error(f"Error getting VM status: {e}")
            return {'error': str(e)}
    
    def check_nsg_rules(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Check Network Security Group rules for RDP (port 3389)"""
        try:
            vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
            nsg_info = {'rdp_allowed': False, 'rules': []}
            
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                nic = self.network_client.network_interfaces.get(resource_group, nic_name)
                
                if nic.network_security_group:
                    nsg_name = nic.network_security_group.id.split('/')[-1]
                    nsg = self.network_client.network_security_groups.get(resource_group, nsg_name)
                    
                    for rule in nsg.security_rules:
                        if rule.destination_port_range == '3389' or '3389' in (rule.destination_port_ranges or []):
                            nsg_info['rules'].append({
                                'name': rule.name,
                                'access': rule.access.value,
                                'direction': rule.direction.value,
                                'source': rule.source_address_prefix,
                                'destination': rule.destination_address_prefix,
                                'protocol': rule.protocol.value
                            })
                            
                            if rule.access.value == 'Allow' and rule.direction.value == 'Inbound':
                                nsg_info['rdp_allowed'] = True
            
            return nsg_info
        except Exception as e:
            logger.error(f"Error checking NSG rules: {e}")
            return {'error': str(e)}
    
    def analyze_with_ai(self, vm_status: Dict, nsg_info: Dict, additional_info: Dict = None) -> Dict[str, Any]:
        """Use OpenAI to analyze the RDP issue and provide recommendations"""
        try:
            # Prepare context for AI analysis
            context = {
                'vm_status': vm_status,
                'nsg_info': nsg_info,
                'additional_info': additional_info or {},
                'timestamp': datetime.now().isoformat()
            }
            
            prompt = f"""
            You are an Azure RDP troubleshooting expert. Analyze the following VM and network configuration to diagnose RDP connectivity issues.
            
            VM Status: {json.dumps(vm_status, indent=2)}
            Network Security Group Info: {json.dumps(nsg_info, indent=2)}
            Additional Info: {json.dumps(additional_info or {}, indent=2)}
            
            Please provide:
            1. Root cause analysis
            2. Specific steps to fix the issue
            3. Prevention recommendations
            4. Priority level (High/Medium/Low)
            
            Format your response as JSON with the following structure:
            {{
                "root_cause": "Brief description of the issue",
                "fix_steps": ["Step 1", "Step 2", "Step 3"],
                "prevention": ["Recommendation 1", "Recommendation 2"],
                "priority": "High/Medium/Low",
                "confidence": 0.95
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Azure RDP troubleshooting specialist. Provide clear, actionable recommendations in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            try:
                return json.loads(ai_response)
            except json.JSONDecodeError:
                return {
                    "root_cause": "Unable to parse AI response",
                    "fix_steps": ["Check the AI response manually"],
                    "prevention": ["Review AI response"],
                    "priority": "Medium",
                    "confidence": 0.0,
                    "raw_response": ai_response
                }
                
        except Exception as e:
            logger.error(f"Error in AI analysis: {e}")
            return {
                "root_cause": f"AI analysis failed: {str(e)}",
                "fix_steps": ["Check logs for detailed error information"],
                "prevention": ["Ensure OpenAI API key is valid"],
                "priority": "High",
                "confidence": 0.0
            }
    
    def troubleshoot_rdp(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Main troubleshooting workflow"""
        logger.info(f"Starting RDP troubleshooting for VM: {vm_name} in resource group: {resource_group}")
        
        # Step 1: Get VM status
        logger.info("Step 1: Checking VM status...")
        vm_status = self.get_vm_status(resource_group, vm_name)
        
        if 'error' in vm_status:
            return {
                'status': 'error',
                'message': f"Failed to get VM status: {vm_status['error']}",
                'vm_status': vm_status
            }
        
        # Step 2: Check NSG rules
        logger.info("Step 2: Checking Network Security Group rules...")
        nsg_info = self.check_nsg_rules(resource_group, vm_name)
        
        # Step 3: AI Analysis
        logger.info("Step 3: Running AI analysis...")
        ai_analysis = self.analyze_with_ai(vm_status, nsg_info)
        
        # Step 4: Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'vm_name': vm_name,
            'resource_group': resource_group,
            'vm_status': vm_status,
            'nsg_info': nsg_info,
            'ai_analysis': ai_analysis,
            'status': 'completed'
        }
        
        logger.info("RDP troubleshooting completed successfully")
        return report

def main():
    parser = argparse.ArgumentParser(
        description='Enable RDP Bot - Diagnose and fix RDP connectivity issues on Azure VMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python enable_rdp.py --rg production-rg --vm web-server-01
        """
    )
    
    parser.add_argument('--rg', required=True, help='Azure resource group name')
    parser.add_argument('--vm', '-v', required=True, help='Virtual machine name')
    
    args = parser.parse_args()
    
    # Get subscription ID from Azure CLI
    try:
        import subprocess
        result = subprocess.run(['az', 'account', 'show', '--query', 'id', '-o', 'tsv'], 
                              capture_output=True, text=True, check=True)
        subscription_id = result.stdout.strip()
    except:
        logger.error("Could not determine Azure subscription ID. Please ensure you are logged in with 'az login'")
        sys.exit(1)
    
    try:
        # Initialize troubleshooter
        troubleshooter = AzureRDPTroubleshooter(subscription_id)
        
        # Run troubleshooting
        result = troubleshooter.troubleshoot_rdp(args.rg, args.vm)
        
        # Output results
        print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()