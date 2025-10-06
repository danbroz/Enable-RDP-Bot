#!/usr/bin/env python3
"""
Enable RDP Bot - Azure RDP Troubleshooting and Auto-Fix Agent

This tool diagnoses RDP connectivity issues on Azure Virtual Machines and automatically
fixes common problems like stopped VMs and blocked NSG rules.

Usage:
    python enable_rdp_bot.py --rg <rg-name> --vm <vm-name>

Example:
    python enable_rdp_bot.py --rg production-rg --vm web-server-01

Auto-fix capabilities:
    - Starts stopped VMs automatically
    - Adds RDP allow rules to Network Security Groups
    - Provides detailed AI analysis and recommendations
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

# Configure logging (minimal output)
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
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
            return available_models
        except Exception as e:
            logger.warning(f"Could not fetch available models: {e}")
            return []
    
    def select_best_model(self) -> str:
        """Select the best available model, preferring reliable models"""
        preferred_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        for model in preferred_models:
            if model in self.available_models:
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
        """Check Network Security Group rules for RDP (port 3389), including priorities"""
        try:
            vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
            nsg_info = {'rdp_allowed': False, 'rules': [], 'rdp_conflict': False, 'allow_priority': None, 'deny_priority': None}
            
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                nic = self.network_client.network_interfaces.get(resource_group, nic_name)
                
                if nic.network_security_group:
                    nsg_name = nic.network_security_group.id.split('/')[-1]
                    nsg = self.network_client.network_security_groups.get(resource_group, nsg_name)
                    
                    for rule in nsg.security_rules:
                        destination_port_range = getattr(rule, 'destination_port_range', None)
                        destination_port_ranges = getattr(rule, 'destination_port_ranges', None) or []
                        has_rdp = (
                            destination_port_range == '3389' or
                            ('3389' in destination_port_ranges)
                        )
                        if has_rdp:
                            # Normalize enum-like fields which may be strings in some SDK versions
                            access = getattr(rule.access, 'value', rule.access)
                            direction = getattr(rule.direction, 'value', rule.direction)
                            protocol = getattr(rule.protocol, 'value', rule.protocol)

                            nsg_info['rules'].append({
                                'name': rule.name,
                                'access': access,
                                'direction': direction,
                                'priority': getattr(rule, 'priority', None),
                                'source': getattr(rule, 'source_address_prefix', None),
                                'destination': getattr(rule, 'destination_address_prefix', None),
                                'protocol': protocol
                            })
                            
                            if access == 'Allow' and direction == 'Inbound':
                                nsg_info['rdp_allowed'] = True

                            # Track priorities to detect conflicts (lower number = higher precedence)
                            if access == 'Allow' and direction == 'Inbound' and getattr(rule, 'priority', None) is not None:
                                if nsg_info['allow_priority'] is None or rule.priority < nsg_info['allow_priority']:
                                    nsg_info['allow_priority'] = rule.priority
                            if access == 'Deny' and direction == 'Inbound' and getattr(rule, 'priority', None) is not None:
                                if nsg_info['deny_priority'] is None or rule.priority < nsg_info['deny_priority']:
                                    nsg_info['deny_priority'] = rule.priority

                    # After scanning rules, detect conflict: a Deny with higher precedence than Allow
                    if nsg_info['allow_priority'] is not None and nsg_info['deny_priority'] is not None:
                        if nsg_info['deny_priority'] < nsg_info['allow_priority']:
                            nsg_info['rdp_conflict'] = True
            
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
                max_completion_tokens=1000
            )
            
            # Parse AI response
            ai_response = response.choices[0].message.content
            
            # Check for empty response
            if not ai_response or ai_response.strip() == "":
                logger.warning("AI returned empty response")
                return {
                    "root_cause": "AI returned empty response - model may be unavailable or overloaded",
                    "fix_steps": ["Try again later", "Check OpenAI service status", "Consider using a different model"],
                    "prevention": ["Monitor AI service availability", "Use fallback models"],
                    "priority": "High",
                    "confidence": 0.0,
                    "raw_response": ai_response
                }
            
            try:
                # Clean the response - remove markdown code blocks if present
                cleaned_response = ai_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()
                
                parsed_response = json.loads(cleaned_response)
                # Validate that the response has the expected structure
                required_fields = ["root_cause", "fix_steps", "prevention", "priority", "confidence"]
                if all(field in parsed_response for field in required_fields):
                    return parsed_response
                else:
                    logger.warning(f"AI response missing required fields. Got: {list(parsed_response.keys())}")
                    return {
                        "root_cause": "AI response missing required fields",
                        "fix_steps": ["Check the AI response manually"],
                        "prevention": ["Review AI response format"],
                        "priority": "Medium",
                        "confidence": 0.0,
                        "raw_response": ai_response
                    }
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse AI response as JSON: {e}")
                return {
                    "root_cause": "Unable to parse AI response as JSON",
                    "fix_steps": ["Check the AI response manually"],
                    "prevention": ["Review AI response format"],
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
    
    def fix_vm_power_state(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Start a stopped VM"""
        try:
            logger.info(f"Starting VM: {vm_name}")
            async_vm_start = self.compute_client.virtual_machines.begin_start(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            async_vm_start.wait()
            
            return {
                'status': 'success',
                'action': 'vm_started',
                'message': f'VM {vm_name} started successfully'
            }
        except Exception as e:
            logger.error(f"Error starting VM: {e}")
            return {
                'status': 'error',
                'action': 'vm_start_failed',
                'message': f'Failed to start VM: {str(e)}'
            }
    
    def fix_nsg_rdp_rule(self, resource_group: str, vm_name: str, desired_priority: Optional[int] = None) -> Dict[str, Any]:
        """Ensure NSG allows inbound RDP by creating or updating an allow rule with proper priority"""
        try:
            # Get VM to find the NSG
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Get network interface
            nic_id = vm.network_profile.network_interfaces[0].id
            nic_name = nic_id.split('/')[-1]
            
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group,
                network_interface_name=nic_name
            )
            
            # Get NSG
            nsg_id = nic.network_security_group.id
            nsg_name = nsg_id.split('/')[-1]
            
            logger.info(f"Ensuring RDP allow rule on NSG: {nsg_name}")

            # Determine target priority
            # If not provided, try to set to 500 by default
            target_priority = desired_priority if desired_priority is not None else 500

            # Inspect existing rules for AllowRDP and conflicting Deny
            nsg = self.network_client.network_security_groups.get(resource_group, nsg_name)
            existing_allow = None
            highest_precedence_deny = None
            for rule in nsg.security_rules or []:
                destination_port_range = getattr(rule, 'destination_port_range', None)
                destination_port_ranges = getattr(rule, 'destination_port_ranges', None) or []
                has_rdp = (destination_port_range == '3389' or ('3389' in destination_port_ranges))
                if not has_rdp:
                    continue
                access = getattr(rule.access, 'value', rule.access)
                direction = getattr(rule.direction, 'value', rule.direction)
                if direction != 'Inbound':
                    continue
                if access == 'Allow':
                    existing_allow = rule
                if access == 'Deny':
                    if highest_precedence_deny is None or (getattr(rule, 'priority', 4096) < getattr(highest_precedence_deny, 'priority', 4096)):
                        highest_precedence_deny = rule

            # If there is a deny with higher precedence, set target_priority to just above it
            if highest_precedence_deny is not None and getattr(highest_precedence_deny, 'priority', None) is not None:
                deny_pri = highest_precedence_deny.priority
                # choose a lower number (higher precedence) than the deny, but >= 100
                target_priority = max(100, min(deny_pri - 1, target_priority))

            # Build rule payload
            rdp_rule = {
                'name': 'AllowRDP',
                'priority': target_priority,
                'direction': 'Inbound',
                'access': 'Allow',
                'protocol': 'Tcp',
                'source_port_range': '*',
                'destination_port_range': '3389',
                'source_address_prefix': '*',
                'destination_address_prefix': '*',
                'description': 'Allow RDP access - Managed by Enable RDP Bot'
            }

            # Create or update AllowRDP
            self.network_client.security_rules.begin_create_or_update(
                resource_group_name=resource_group,
                network_security_group_name=nsg_name,
                security_rule_name='AllowRDP',
                security_rule_parameters=rdp_rule
            ).wait()

            action = 'nsg_rule_added' if existing_allow is None else 'nsg_rule_updated'
            return {
                'status': 'success',
                'action': action,
                'message': f"RDP allow rule {'created' if existing_allow is None else 'updated'} on NSG {nsg_name} with priority {target_priority}",
                'rule_details': rdp_rule
            }
            
        except Exception as e:
            logger.error(f"Error adding NSG rule: {e}")
            return {
                'status': 'error',
                'action': 'nsg_rule_failed',
                'message': f'Failed to add RDP rule: {str(e)}'
            }
    
    def troubleshoot_rdp(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """Main troubleshooting workflow"""
        logger.info(f"Starting RDP troubleshooting for VM: {vm_name} in resource group: {resource_group}")
        
        # Step 1: Get VM status
        vm_status = self.get_vm_status(resource_group, vm_name)
        
        if 'error' in vm_status:
            return {
                'status': 'error',
                'message': f"Failed to get VM status: {vm_status['error']}",
                'vm_status': vm_status
            }
        
        # Step 2: Check NSG rules
        nsg_info = self.check_nsg_rules(resource_group, vm_name)
        
        # Step 3: AI Analysis
        ai_analysis = self.analyze_with_ai(vm_status, nsg_info)
        
        # Step 4: Auto-fix issues
        fixes_applied = []
        
        # Fix VM power state if stopped
        if vm_status.get('power_state') == 'deallocated':
            logger.info("VM is stopped - attempting to start it")
            vm_fix_result = self.fix_vm_power_state(resource_group, vm_name)
            fixes_applied.append(vm_fix_result)
        
        # Fix NSG rules if RDP is blocked or conflict detected
        if (not nsg_info.get('rdp_allowed', False)) or nsg_info.get('rdp_conflict', False):
            logger.info("Ensuring NSG allows RDP - creating or updating allow rule with correct priority")
            desired_priority = None
            # If we detected a deny with higher precedence, choose a priority just above it
            if nsg_info.get('deny_priority') is not None:
                desired_priority = max(100, nsg_info['deny_priority'] - 1)
            nsg_fix_result = self.fix_nsg_rdp_rule(resource_group, vm_name, desired_priority)
            fixes_applied.append(nsg_fix_result)
        
        # Step 5: Generate report
        report = {
            'timestamp': datetime.now().isoformat(),
            'vm_name': vm_name,
            'resource_group': resource_group,
            'vm_status': vm_status,
            'nsg_info': nsg_info,
            'ai_analysis': ai_analysis,
            'fixes_applied': fixes_applied,
            'status': 'completed'
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(
        description='Enable RDP Bot - Diagnose and auto-fix RDP connectivity issues on Azure VMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python enable_rdp_bot.py --rg production-rg --vm web-server-01
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