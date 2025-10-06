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
    """
    Azure RDP Troubleshooting Agent
    
    This class provides comprehensive RDP connectivity diagnosis and auto-fix capabilities
    for Azure Virtual Machines. It integrates with Azure SDK for infrastructure analysis
    and OpenAI API for intelligent problem diagnosis.
    """
    
    def __init__(self, subscription_id: str):
        """
        Initialize the RDP troubleshooter with Azure and OpenAI clients
        
        Args:
            subscription_id (str): Azure subscription ID for resource access
        """
        self.subscription_id = subscription_id
        
        # Initialize Azure clients using DefaultAzureCredential for authentication
        # This supports multiple auth methods: Azure CLI, Managed Identity, Service Principal, etc.
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(self.credential, subscription_id)
        self.network_client = NetworkManagementClient(self.credential, subscription_id)
        self.resource_client = ResourceManagementClient(self.credential, subscription_id)
        
        # Initialize OpenAI client for AI-powered analysis
        openai_api_key = os.getenv('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.openai_client = openai.OpenAI(api_key=openai_api_key)
        
        # Check available models and select the best one for analysis
        self.available_models = self.check_available_models()
        self.model = self.select_best_model()
    
    def check_available_models(self) -> List[str]:
        """
        Check available OpenAI models via API
        
        Returns:
            List[str]: List of available model IDs
        """
        try:
            models = self.openai_client.models.list()
            available_models = [model.id for model in models.data]
            return available_models
        except Exception as e:
            logger.warning(f"Could not fetch available models: {e}")
            return []
    
    def select_best_model(self) -> str:
        """
        Select the best available model, preferring reliable models
        
        Model selection priority:
        1. GPT-4o (most capable and reliable)
        2. GPT-4 Turbo (high performance with extended context)
        3. GPT-4 (standard high-quality model)
        4. GPT-3.5 Turbo (fast and efficient)
        
        Returns:
            str: Selected model ID
        """
        preferred_models = ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        # Try each preferred model in order
        for model in preferred_models:
            if model in self.available_models:
                return model
        
        # Fallback to first available model if none of the preferred ones are available
        if self.available_models:
            fallback_model = self.available_models[0]
            logger.warning(f"Using fallback model: {fallback_model}")
            return fallback_model
        
        # Ultimate fallback - use gpt-4 even if not confirmed available
        logger.error("No OpenAI models available, using gpt-4 as fallback")
        return "gpt-4"
    
    def get_vm_status(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """
        Get comprehensive VM status and configuration information
        
        Args:
            resource_group (str): Azure resource group name
            vm_name (str): Virtual machine name
            
        Returns:
            Dict[str, Any]: VM status information including power state, size, OS type, etc.
        """
        try:
            # Get VM configuration and instance view for power state
            vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
            instance_view = self.compute_client.virtual_machines.instance_view(resource_group, vm_name)
            
            # Build comprehensive status dictionary
            status = {
                'name': vm.name,
                'location': vm.location,
                'vm_size': vm.hardware_profile.vm_size,
                'os_type': str(vm.storage_profile.os_disk.os_type) if vm.storage_profile.os_disk.os_type else 'Unknown',
                'power_state': 'Unknown',  # Will be updated from instance view
                'provisioning_state': vm.provisioning_state,
                'network_interfaces': [nic.id for nic in vm.network_profile.network_interfaces]
            }
            
            # Extract power state from instance view statuses
            # Power state is reported as "PowerState/running", "PowerState/deallocated", etc.
            for status_info in instance_view.statuses:
                if status_info.code.startswith('PowerState/'):
                    status['power_state'] = status_info.code.split('/')[1]
                    break
            
            return status
        except Exception as e:
            logger.error(f"Error getting VM status: {e}")
            return {'error': str(e)}
    
    def check_nsg_rules(self, resource_group: str, vm_name: str) -> Dict[str, Any]:
        """
        Check Network Security Group rules for RDP (port 3389) and analyze rule priorities
        
        This method examines all NSG rules affecting RDP traffic and detects conflicts
        between allow and deny rules based on their priority values.
        
        Args:
            resource_group (str): Azure resource group name
            vm_name (str): Virtual machine name
            
        Returns:
            Dict[str, Any]: NSG analysis including rules, priorities, and conflict detection
        """
        try:
            vm = self.compute_client.virtual_machines.get(resource_group, vm_name)
            
            # Initialize NSG analysis structure
            nsg_info = {
                'rdp_allowed': False,      # Whether RDP is explicitly allowed
                'rules': [],               # List of all RDP-related rules
                'rdp_conflict': False,     # Whether there's a priority conflict
                'allow_priority': None,    # Highest priority (lowest number) allow rule
                'deny_priority': None,     # Highest priority (lowest number) deny rule
                'has_deny_rdp': False      # Whether any deny rules exist for RDP
            }
            
            # Iterate through all network interfaces attached to the VM
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                nic = self.network_client.network_interfaces.get(resource_group, nic_name)
                
                # Check if the NIC has an associated NSG
                if nic.network_security_group:
                    nsg_name = nic.network_security_group.id.split('/')[-1]
                    nsg = self.network_client.network_security_groups.get(resource_group, nsg_name)
                    
                    # Analyze each security rule in the NSG
                    for rule in nsg.security_rules:
                        # Check if this rule affects RDP port 3389
                        destination_port_range = getattr(rule, 'destination_port_range', None)
                        destination_port_ranges = getattr(rule, 'destination_port_ranges', None) or []
                        has_rdp = (
                            destination_port_range == '3389' or
                            ('3389' in destination_port_ranges)
                        )
                        
                        if has_rdp:
                            # Normalize enum-like fields which may be strings in different SDK versions
                            access = getattr(rule.access, 'value', rule.access)
                            direction = getattr(rule.direction, 'value', rule.direction)
                            protocol = getattr(rule.protocol, 'value', rule.protocol)

                            # Add rule details to the analysis
                            nsg_info['rules'].append({
                                'name': rule.name,
                                'access': access,
                                'direction': direction,
                                'priority': getattr(rule, 'priority', None),
                                'source': getattr(rule, 'source_address_prefix', None),
                                'destination': getattr(rule, 'destination_address_prefix', None),
                                'protocol': protocol
                            })
                            
                            # Check if RDP is explicitly allowed
                            if access == 'Allow' and direction == 'Inbound':
                                nsg_info['rdp_allowed'] = True

                            # Track rule priorities to detect conflicts
                            # Lower priority numbers = higher precedence in Azure NSG
                            if access == 'Allow' and direction == 'Inbound' and getattr(rule, 'priority', None) is not None:
                                if nsg_info['allow_priority'] is None or rule.priority < nsg_info['allow_priority']:
                                    nsg_info['allow_priority'] = rule.priority
                                    
                            if access == 'Deny' and direction == 'Inbound' and getattr(rule, 'priority', None) is not None:
                                if nsg_info['deny_priority'] is None or rule.priority < nsg_info['deny_priority']:
                                    nsg_info['deny_priority'] = rule.priority
                                nsg_info['has_deny_rdp'] = True

                    # Detect priority conflicts: deny rule with higher precedence than allow rule
                    if nsg_info['allow_priority'] is not None and nsg_info['deny_priority'] is not None:
                        if nsg_info['deny_priority'] < nsg_info['allow_priority']:
                            nsg_info['rdp_conflict'] = True
            
            return nsg_info
        except Exception as e:
            logger.error(f"Error checking NSG rules: {e}")
            return {'error': str(e)}
    
    def analyze_with_ai(self, vm_status: Dict, nsg_info: Dict, additional_info: Dict = None) -> Dict[str, Any]:
        """
        Use OpenAI to analyze RDP connectivity issues and provide intelligent recommendations
        
        This method sends VM and network configuration data to an AI model for analysis,
        then parses the response to extract structured recommendations.
        
        Args:
            vm_status (Dict): VM status and configuration information
            nsg_info (Dict): Network Security Group analysis results
            additional_info (Dict, optional): Additional context for analysis
            
        Returns:
            Dict[str, Any]: AI analysis with root cause, fix steps, and recommendations
        """
        try:
            # Prepare comprehensive context for AI analysis
            context = {
                'vm_status': vm_status,
                'nsg_info': nsg_info,
                'additional_info': additional_info or {},
                'timestamp': datetime.now().isoformat()
            }
            
            # Construct detailed prompt for AI analysis
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
            
            # Send request to OpenAI API
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Azure RDP troubleshooting specialist. Provide clear, actionable recommendations in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=1000
            )
            
            # Extract AI response content
            ai_response = response.choices[0].message.content
            
            # Handle empty or invalid responses
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
                # Some models return JSON wrapped in ```json ... ``` blocks
                cleaned_response = ai_response.strip()
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]  # Remove ```json
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]   # Remove ```
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]  # Remove trailing ```
                cleaned_response = cleaned_response.strip()
                
                # Parse JSON response
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
        """
        Start a stopped or deallocated VM
        
        This method initiates the VM start operation and waits for completion.
        It's used when the VM is found to be in a stopped state during diagnosis.
        
        Args:
            resource_group (str): Azure resource group name
            vm_name (str): Virtual machine name
            
        Returns:
            Dict[str, Any]: Result of the VM start operation
        """
        try:
            logger.info(f"Starting VM: {vm_name}")
            
            # Begin asynchronous VM start operation
            async_vm_start = self.compute_client.virtual_machines.begin_start(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Wait for the operation to complete
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
        """
        Ensure NSG allows inbound RDP by creating or updating an allow rule with proper priority
        
        This method intelligently manages NSG rules to ensure RDP access is allowed.
        It automatically adjusts rule priorities to outrank any conflicting deny rules.
        
        Args:
            resource_group (str): Azure resource group name
            vm_name (str): Virtual machine name
            desired_priority (Optional[int]): Desired priority for the allow rule
            
        Returns:
            Dict[str, Any]: Result of the NSG rule operation
        """
        try:
            # Get VM to find the associated network interface and NSG
            vm = self.compute_client.virtual_machines.get(
                resource_group_name=resource_group,
                vm_name=vm_name
            )
            
            # Get the primary network interface
            nic_id = vm.network_profile.network_interfaces[0].id
            nic_name = nic_id.split('/')[-1]
            
            nic = self.network_client.network_interfaces.get(
                resource_group_name=resource_group,
                network_interface_name=nic_name
            )
            
            # Get the Network Security Group
            nsg_id = nic.network_security_group.id
            nsg_name = nsg_id.split('/')[-1]
            
            logger.info(f"Ensuring RDP allow rule on NSG: {nsg_name}")

            # Determine target priority - default to 500 if not specified
            target_priority = desired_priority if desired_priority is not None else 500

            # Analyze existing NSG rules to detect conflicts and existing allow rules
            nsg = self.network_client.network_security_groups.get(resource_group, nsg_name)
            existing_allow = None
            highest_precedence_deny = None
            
            for rule in nsg.security_rules or []:
                # Check if this rule affects RDP port 3389
                destination_port_range = getattr(rule, 'destination_port_range', None)
                destination_port_ranges = getattr(rule, 'destination_port_ranges', None) or []
                has_rdp = (destination_port_range == '3389' or ('3389' in destination_port_ranges))
                if not has_rdp:
                    continue
                    
                access = getattr(rule.access, 'value', rule.access)
                direction = getattr(rule.direction, 'value', rule.direction)
                if direction != 'Inbound':
                    continue
                    
                # Track existing allow rules
                if access == 'Allow':
                    existing_allow = rule
                    
                # Track deny rules to determine priority conflicts
                if access == 'Deny':
                    if highest_precedence_deny is None or (getattr(rule, 'priority', 4096) < getattr(highest_precedence_deny, 'priority', 4096)):
                        highest_precedence_deny = rule

            # Adjust target priority if there's a conflicting deny rule
            # Lower numbers = higher precedence in Azure NSG
            if highest_precedence_deny is not None and getattr(highest_precedence_deny, 'priority', None) is not None:
                deny_pri = highest_precedence_deny.priority
                # Set priority to be higher precedence (lower number) than the deny rule, but >= 100
                target_priority = max(100, min(deny_pri - 1, target_priority))

            # Build the RDP allow rule configuration
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

            # Create or update the AllowRDP rule
            self.network_client.security_rules.begin_create_or_update(
                resource_group_name=resource_group,
                network_security_group_name=nsg_name,
                security_rule_name='AllowRDP',
                security_rule_parameters=rdp_rule
            ).wait()

            # Determine the action taken
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
        """
        Main troubleshooting workflow that diagnoses and auto-fixes RDP connectivity issues
        
        This method orchestrates the complete RDP troubleshooting process:
        1. VM status analysis
        2. Network Security Group rule analysis
        3. AI-powered problem diagnosis
        4. Automatic issue remediation
        5. Comprehensive reporting
        
        Args:
            resource_group (str): Azure resource group name
            vm_name (str): Virtual machine name
            
        Returns:
            Dict[str, Any]: Complete troubleshooting report with diagnosis and fixes applied
        """
        logger.info(f"Starting RDP troubleshooting for VM: {vm_name} in resource group: {resource_group}")
        
        # Step 1: Get comprehensive VM status and configuration
        vm_status = self.get_vm_status(resource_group, vm_name)
        
        if 'error' in vm_status:
            return {
                'status': 'error',
                'message': f"Failed to get VM status: {vm_status['error']}",
                'vm_status': vm_status
            }
        
        # Step 2: Analyze Network Security Group rules for RDP access
        nsg_info = self.check_nsg_rules(resource_group, vm_name)
        
        # Step 3: Use AI to analyze the collected data and provide recommendations
        ai_analysis = self.analyze_with_ai(vm_status, nsg_info)
        
        # Step 4: Auto-fix identified issues
        fixes_applied = []
        
        # Fix VM power state if the VM is stopped or deallocated
        if vm_status.get('power_state') == 'deallocated':
            logger.info("VM is stopped - attempting to start it")
            vm_fix_result = self.fix_vm_power_state(resource_group, vm_name)
            fixes_applied.append(vm_fix_result)
        
        # Ensure NSG allows RDP access with proper priority
        # If deny rules exist, ensure allow rule has higher precedence (lower priority number)
        logger.info("Verifying NSG RDP allow rule priority and presence")
        desired_priority = None
        if nsg_info.get('deny_priority') is not None:
            # Set allow rule priority to be higher precedence than deny rule
            desired_priority = max(100, nsg_info['deny_priority'] - 1)
        nsg_fix_result = self.fix_nsg_rdp_rule(resource_group, vm_name, desired_priority)
        fixes_applied.append(nsg_fix_result)
        
        # Step 5: Generate comprehensive troubleshooting report
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
    """
    Main entry point for the Enable RDP Bot command-line tool
    
    This function handles command-line argument parsing, Azure authentication,
    and orchestrates the RDP troubleshooting process.
    """
    parser = argparse.ArgumentParser(
        description='Enable RDP Bot - Diagnose and auto-fix RDP connectivity issues on Azure VMs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python enable_rdp_bot.py --rg production-rg --vm web-server-01
        """
    )
    
    # Define command-line arguments
    parser.add_argument('--rg', required=True, help='Azure resource group name')
    parser.add_argument('--vm', '-v', required=True, help='Virtual machine name')
    
    args = parser.parse_args()
    
    # Get Azure subscription ID from Azure CLI
    # This requires the user to be logged in with 'az login'
    try:
        import subprocess
        result = subprocess.run(['az', 'account', 'show', '--query', 'id', '-o', 'tsv'], 
                              capture_output=True, text=True, check=True)
        subscription_id = result.stdout.strip()
    except:
        logger.error("Could not determine Azure subscription ID. Please ensure you are logged in with 'az login'")
        sys.exit(1)
    
    try:
        # Initialize the RDP troubleshooter with Azure and OpenAI clients
        troubleshooter = AzureRDPTroubleshooter(subscription_id)
        
        # Execute the complete RDP troubleshooting workflow
        result = troubleshooter.troubleshoot_rdp(args.rg, args.vm)
        
        # Output the results as formatted JSON
        print(json.dumps(result, indent=2))
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()