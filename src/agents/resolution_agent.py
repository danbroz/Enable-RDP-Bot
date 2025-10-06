"""
Resolution Agent for Azure VM RDP Troubleshooting

This agent executes fixes and validates resolutions for RDP connectivity issues
identified by the diagnostic agent.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.functions.kernel_arguments import KernelArguments
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.identity import DefaultAzureCredential

from ..plugins.azure_diagnostics import AzureDiagnosticsPlugin
from ..plugins.network_checks import NetworkChecksPlugin
from ..plugins.vm_operations import VmOperationsPlugin
from ..safety.guardrails import SafetyGuardrails


class ResolutionAgent:
    """Agent responsible for executing fixes and validating resolutions."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.credential = DefaultAzureCredential()
        self.safety_guardrails = SafetyGuardrails()
        
        # Initialize Azure operation plugins
        self.azure_diagnostics = AzureDiagnosticsPlugin(self.credential)
        self.network_checks = NetworkChecksPlugin(self.credential)
        self.vm_operations = VmOperationsPlugin(self.credential)
        
        self.logger = logging.getLogger(__name__)
        
        # Register resolution functions with semantic kernel
        self._register_resolution_functions()
    
    def _register_resolution_functions(self):
        """Register resolution functions with the semantic kernel."""
        
        # VM Operations
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="start_vm",
            function=self.start_vm
        )
        
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="restart_vm",
            function=self.restart_vm
        )
        
        # Network Configuration
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="update_nsg_rules",
            function=self.update_nsg_rules
        )
        
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="configure_firewall",
            function=self.configure_firewall
        )
        
        # Service Management
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="start_rdp_service",
            function=self.start_rdp_service
        )
        
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="restart_rdp_service",
            function=self.restart_rdp_service
        )
        
        # Validation
        self.kernel.add_function(
            plugin_name="resolution",
            function_name="validate_resolution",
            function=self.validate_resolution
        )
    
    async def execute_resolution(self, user_input: str, user_context: Dict[str, Any],
                               conversation_history: ChatHistory) -> Dict[str, Any]:
        """
        Execute resolution actions based on diagnostic results.
        
        Args:
            user_input: User's confirmation or specific resolution request
            user_context: User context including subscription, VM details, etc.
            conversation_history: Previous conversation context
            
        Returns:
            Resolution results with actions taken and validation
        """
        try:
            self.logger.info(f"Starting resolution execution for user input: {user_input}")
            
            # Extract resolution plan from conversation history
            resolution_plan = await self._extract_resolution_plan(user_input, conversation_history)
            
            if not resolution_plan:
                return await self._handle_no_resolution_plan(user_input)
            
            # Safety validation
            safety_check = await self.safety_guardrails.validate_resolution_actions(
                resolution_plan, user_context
            )
            
            if not safety_check["safe"]:
                return {
                    "status": "blocked",
                    "message": f"Resolution blocked for safety reasons: {safety_check['reason']}",
                    "requires_confirmation": True
                }
            
            # Execute resolution actions
            execution_results = await self._execute_resolution_actions(
                resolution_plan, user_context
            )
            
            # Validate resolution
            validation_results = await self._validate_resolution(
                resolution_plan, user_context, execution_results
            )
            
            # Generate response
            response_message = await self._generate_resolution_response(
                execution_results, validation_results, resolution_plan
            )
            
            return {
                "status": "resolution_complete",
                "message": response_message,
                "actions_taken": execution_results.get("actions", []),
                "verification_results": validation_results,
                "success": validation_results.get("success", False),
                "requires_followup": not validation_results.get("success", False)
            }
            
        except Exception as e:
            self.logger.error(f"Error in resolution execution: {str(e)}")
            return {
                "status": "resolution_error",
                "message": f"An error occurred during resolution: {str(e)}",
                "error_details": str(e)
            }
    
    async def _extract_resolution_plan(self, user_input: str, 
                                     conversation_history: ChatHistory) -> Optional[List[Dict[str, Any]]]:
        """Extract resolution plan from conversation history and user input."""
        
        # Look for recommended actions in conversation history
        recommended_actions = []
        
        # Search through recent messages for recommended actions
        for message in reversed(conversation_history.messages[-10:]):
            if hasattr(message, 'content') and message.content:
                content = str(message.content)
                if "recommended actions" in content.lower() or "recommended_actions" in content:
                    # Extract actions from the message content
                    # This is a simplified extraction - in production, you'd use more sophisticated parsing
                    if "start the vm" in content.lower():
                        recommended_actions.append({"action": "start_vm", "description": "Start the VM"})
                    if "nsg rule" in content.lower() and "rdp" in content.lower():
                        recommended_actions.append({
                            "action": "update_nsg_rules", 
                            "description": "Add NSG rule to allow RDP on port 3389"
                        })
                    if "firewall" in content.lower():
                        recommended_actions.append({
                            "action": "configure_firewall",
                            "description": "Configure Windows Firewall to allow RDP"
                        })
                    if "rdp service" in content.lower():
                        recommended_actions.append({
                            "action": "start_rdp_service",
                            "description": "Start the Remote Desktop Services"
                        })
        
        # Check user input for confirmation
        user_confirmation = any(word in user_input.lower() for word in 
                              ["yes", "proceed", "execute", "fix", "resolve", "apply"])
        
        if recommended_actions and user_confirmation:
            return recommended_actions
        
        return None
    
    async def _handle_no_resolution_plan(self, user_input: str) -> Dict[str, Any]:
        """Handle cases where no resolution plan is available."""
        
        return {
            "status": "no_plan",
            "message": """
            I don't have a specific resolution plan to execute. 
            
            Please provide more details about what you'd like me to fix, or 
            confirm the specific actions you'd like me to take.
            
            For example:
            - "Yes, please start my VM"
            - "Please add the NSG rule for RDP"
            - "Configure the firewall to allow RDP"
            """,
            "requires_resolution": False
        }
    
    async def _execute_resolution_actions(self, resolution_plan: List[Dict[str, Any]],
                                        user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the resolution actions in the plan."""
        
        execution_results = {
            "actions": [],
            "success_count": 0,
            "failure_count": 0,
            "errors": []
        }
        
        vm_info = user_context.get("vm_info", {})
        vm_name = vm_info.get("vm_name")
        resource_group = vm_info.get("resource_group")
        subscription_id = user_context.get("subscription_id")
        
        for action_item in resolution_plan:
            action_type = action_item["action"]
            description = action_item["description"]
            
            try:
                result = await self._execute_single_action(
                    action_type, vm_name, resource_group, subscription_id
                )
                
                execution_results["actions"].append({
                    "action": action_type,
                    "description": description,
                    "success": result["success"],
                    "message": result["message"]
                })
                
                if result["success"]:
                    execution_results["success_count"] += 1
                else:
                    execution_results["failure_count"] += 1
                    execution_results["errors"].append(result["error"])
                    
            except Exception as e:
                execution_results["actions"].append({
                    "action": action_type,
                    "description": description,
                    "success": False,
                    "message": f"Action failed: {str(e)}"
                })
                execution_results["failure_count"] += 1
                execution_results["errors"].append(str(e))
        
        return execution_results
    
    async def _execute_single_action(self, action_type: str, vm_name: str, 
                                   resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Execute a single resolution action."""
        
        try:
            if action_type == "start_vm":
                result = await self.start_vm(vm_name, resource_group, subscription_id)
            elif action_type == "restart_vm":
                result = await self.restart_vm(vm_name, resource_group, subscription_id)
            elif action_type == "update_nsg_rules":
                result = await self.update_nsg_rules(vm_name, resource_group, subscription_id)
            elif action_type == "configure_firewall":
                result = await self.configure_firewall(vm_name, resource_group, subscription_id)
            elif action_type == "start_rdp_service":
                result = await self.start_rdp_service(vm_name, resource_group, subscription_id)
            elif action_type == "restart_rdp_service":
                result = await self.restart_rdp_service(vm_name, resource_group, subscription_id)
            else:
                return {
                    "success": False,
                    "message": f"Unknown action type: {action_type}",
                    "error": f"Unknown action type: {action_type}"
                }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Action {action_type} failed: {str(e)}",
                "error": str(e)
            }
    
    async def _validate_resolution(self, resolution_plan: List[Dict[str, Any]],
                                 user_context: Dict[str, Any], 
                                 execution_results: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that the resolution was successful."""
        
        validation_results = {
            "success": True,
            "checks": [],
            "overall_status": "success"
        }
        
        vm_info = user_context.get("vm_info", {})
        vm_name = vm_info.get("vm_name")
        resource_group = vm_info.get("resource_group")
        subscription_id = user_context.get("subscription_id")
        
        # Run validation checks based on actions taken
        for action in execution_results["actions"]:
            if action["success"]:
                action_type = action["action"]
                
                if action_type == "start_vm":
                    # Validate VM is running
                    vm_status = await self.vm_operations.get_vm_status(
                        vm_name, resource_group, subscription_id
                    )
                    validation_results["checks"].append({
                        "check": "vm_status",
                        "success": vm_status.get("status") == "running",
                        "message": f"VM status: {vm_status.get('status')}"
                    })
                
                elif action_type == "update_nsg_rules":
                    # Validate NSG rules
                    nsg_check = await self.network_checks.check_nsg_rules(
                        vm_name, resource_group, subscription_id
                    )
                    validation_results["checks"].append({
                        "check": "nsg_rules",
                        "success": nsg_check.get("rdp_allowed"),
                        "message": f"NSG RDP access: {'allowed' if nsg_check.get('rdp_allowed') else 'blocked'}"
                    })
                
                elif action_type == "configure_firewall":
                    # Validate firewall configuration
                    firewall_check = await self.azure_diagnostics.check_guest_firewall(
                        vm_name, resource_group, subscription_id
                    )
                    validation_results["checks"].append({
                        "check": "firewall",
                        "success": not firewall_check.get("rdp_blocked"),
                        "message": f"Firewall RDP access: {'allowed' if not firewall_check.get('rdp_blocked') else 'blocked'}"
                    })
        
        # Determine overall success
        failed_checks = [check for check in validation_results["checks"] if not check["success"]]
        if failed_checks:
            validation_results["success"] = False
            validation_results["overall_status"] = "partial_success"
        
        if execution_results["failure_count"] > 0:
            validation_results["success"] = False
            validation_results["overall_status"] = "failed"
        
        return validation_results
    
    async def _generate_resolution_response(self, execution_results: Dict[str, Any],
                                          validation_results: Dict[str, Any],
                                          resolution_plan: List[Dict[str, Any]]) -> str:
        """Generate a user-friendly resolution response."""
        
        response = "## Resolution Execution Results\n\n"
        
        # Summary of actions taken
        response += f"**Actions Executed:** {execution_results['success_count']}/{len(resolution_plan)} successful\n\n"
        
        for action in execution_results["actions"]:
            status_icon = "✅" if action["success"] else "❌"
            response += f"{status_icon} {action['description']}: {action['message']}\n"
        
        # Validation results
        if validation_results["checks"]:
            response += "\n**Validation Results:**\n"
            for check in validation_results["checks"]:
                status_icon = "✅" if check["success"] else "❌"
                response += f"{status_icon} {check['check']}: {check['message']}\n"
        
        # Overall status
        if validation_results["success"]:
            response += "\n🎉 **Resolution successful!** Your VM should now be accessible via RDP.\n\n"
            response += "Please try connecting to your VM again. If you're still experiencing issues, "
            response += "the problem may be related to network connectivity from your location or "
            response += "authentication credentials."
        else:
            response += "\n⚠️ **Resolution partially successful** or **failed**.\n\n"
            if validation_results["overall_status"] == "partial_success":
                response += "Some issues were resolved, but additional problems may remain. "
            else:
                response += "The resolution was not successful. "
            response += "Please review the validation results above and consider escalating to human support."
        
        return response
    
    # Resolution function implementations
    async def start_vm(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Start a stopped VM."""
        try:
            result = await self.vm_operations.start_vm(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"VM {vm_name} started successfully",
                "operation_id": result.get("operation_id")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start VM: {str(e)}",
                "error": str(e)
            }
    
    async def restart_vm(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Restart a running VM."""
        try:
            result = await self.vm_operations.restart_vm(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"VM {vm_name} restarted successfully",
                "operation_id": result.get("operation_id")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to restart VM: {str(e)}",
                "error": str(e)
            }
    
    async def update_nsg_rules(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Update NSG rules to allow RDP."""
        try:
            result = await self.network_checks.add_rdp_nsg_rule(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"NSG rule for RDP added successfully",
                "rule_id": result.get("rule_id")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to update NSG rules: {str(e)}",
                "error": str(e)
            }
    
    async def configure_firewall(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Configure Windows Firewall to allow RDP."""
        try:
            result = await self.azure_diagnostics.configure_firewall_rdp(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"Firewall configured to allow RDP",
                "configuration_id": result.get("config_id")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to configure firewall: {str(e)}",
                "error": str(e)
            }
    
    async def start_rdp_service(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Start the RDP service on the VM."""
        try:
            result = await self.azure_diagnostics.start_rdp_service(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"RDP service started successfully",
                "service_status": result.get("status")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to start RDP service: {str(e)}",
                "error": str(e)
            }
    
    async def restart_rdp_service(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Restart the RDP service on the VM."""
        try:
            result = await self.azure_diagnostics.restart_rdp_service(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "message": f"RDP service restarted successfully",
                "service_status": result.get("status")
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to restart RDP service: {str(e)}",
                "error": str(e)
            }
    
    async def validate_resolution(self, vm_name: str, resource_group: str, subscription_id: str) -> Dict[str, Any]:
        """Validate that the resolution was successful."""
        try:
            # Run comprehensive validation checks
            vm_status = await self.vm_operations.get_vm_status(vm_name, resource_group, subscription_id)
            nsg_check = await self.network_checks.check_nsg_rules(vm_name, resource_group, subscription_id)
            connectivity_test = await self.network_checks.test_connectivity(vm_name, resource_group, subscription_id)
            
            all_checks_passed = (
                vm_status.get("status") == "running" and
                nsg_check.get("rdp_allowed") and
                connectivity_test.get("reachable")
            )
            
            return {
                "success": all_checks_passed,
                "checks": {
                    "vm_running": vm_status.get("status") == "running",
                    "nsg_allows_rdp": nsg_check.get("rdp_allowed"),
                    "connectivity_ok": connectivity_test.get("reachable")
                },
                "message": "All validation checks passed" if all_checks_passed else "Some validation checks failed"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Validation failed: {str(e)}",
                "error": str(e)
            }
