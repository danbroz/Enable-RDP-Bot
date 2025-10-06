"""
Diagnostic Agent for Azure VM RDP Troubleshooting

This agent specializes in diagnosing Windows VM RDP connectivity issues using
Azure-native diagnostic tools and services.
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
from azure.mgmt.monitor import MonitorManagementClient
from azure.identity import DefaultAzureCredential

from ..plugins.azure_diagnostics import AzureDiagnosticsPlugin
from ..plugins.network_checks import NetworkChecksPlugin
from ..plugins.vm_operations import VmOperationsPlugin


class DiagnosticAgent:
    """Specialized agent for diagnosing Azure VM RDP connectivity issues."""
    
    def __init__(self, kernel: Kernel):
        self.kernel = kernel
        self.credential = DefaultAzureCredential()
        
        # Initialize Azure diagnostic plugins
        self.azure_diagnostics = AzureDiagnosticsPlugin(self.credential)
        self.network_checks = NetworkChecksPlugin(self.credential)
        self.vm_operations = VmOperationsPlugin(self.credential)
        
        self.logger = logging.getLogger(__name__)
        
        # Register diagnostic functions with semantic kernel
        self._register_diagnostic_functions()
    
    def _register_diagnostic_functions(self):
        """Register diagnostic functions with the semantic kernel."""
        
        # VM Health Check
        self.kernel.add_function(
            plugin_name="diagnostics",
            function_name="check_vm_health",
            function=self.check_vm_health
        )
        
        # Network Security Groups Check
        self.kernel.add_function(
            plugin_name="diagnostics", 
            function_name="validate_network_security_groups",
            function=self.validate_network_security_groups
        )
        
        # Firewall Status Check
        self.kernel.add_function(
            plugin_name="diagnostics",
            function_name="check_firewall_status",
            function=self.check_firewall_status
        )
        
        # RDP Service Status Check
        self.kernel.add_function(
            plugin_name="diagnostics",
            function_name="check_rdp_service_status",
            function=self.check_rdp_service_status
        )
        
        # Network Connectivity Test
        self.kernel.add_function(
            plugin_name="diagnostics",
            function_name="test_network_connectivity",
            function=self.test_network_connectivity
        )
        
        # Authentication Logs Analysis
        self.kernel.add_function(
            plugin_name="diagnostics",
            function_name="analyze_authentication_logs",
            function=self.analyze_authentication_logs
        )
    
    async def analyze_rdp_issue(self, user_input: str, user_context: Dict[str, Any], 
                               conversation_history: ChatHistory) -> Dict[str, Any]:
        """
        Main diagnostic analysis for RDP connectivity issues.
        
        Args:
            user_input: User's description of the RDP issue
            user_context: User context including subscription, VM details, etc.
            conversation_history: Previous conversation context
            
        Returns:
            Diagnostic results with findings and recommendations
        """
        try:
            self.logger.info(f"Starting RDP diagnostic analysis for user input: {user_input}")
            
            # Extract VM information from context
            vm_info = self._extract_vm_info(user_input, user_context)
            
            if not vm_info:
                return await self._handle_missing_vm_info(user_input)
            
            # Run comprehensive diagnostic sequence
            diagnostic_results = await self._run_diagnostic_sequence(vm_info, user_context)
            
            # Analyze results and generate recommendations
            analysis = await self._analyze_diagnostic_results(diagnostic_results, user_input)
            
            # Generate user-friendly response
            response_message = await self._generate_diagnostic_response(analysis, vm_info)
            
            return {
                "status": "diagnostic_complete",
                "message": response_message,
                "diagnostics": diagnostic_results,
                "analysis": analysis,
                "recommended_actions": analysis.get("recommended_actions", []),
                "requires_resolution": analysis.get("requires_resolution", False),
                "escalation_needed": analysis.get("escalation_needed", False),
                "vm_info": vm_info
            }
            
        except Exception as e:
            self.logger.error(f"Error in RDP diagnostic analysis: {str(e)}")
            return {
                "status": "diagnostic_error",
                "message": f"An error occurred during diagnosis: {str(e)}",
                "error_details": str(e)
            }
    
    def _extract_vm_info(self, user_input: str, user_context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract VM information from user input and context."""
        
        # Try to get VM info from user context first
        vm_info = user_context.get("vm_info", {})
        
        # If not provided, try to extract from user input
        if not vm_info.get("vm_name") and not vm_info.get("resource_id"):
            # Use semantic kernel to extract VM information
            extraction_prompt = """
            Extract Azure VM information from the user's message.
            Look for:
            - VM name
            - Resource group name
            - Subscription ID
            - Any specific error messages or symptoms
            
            User input: {user_input}
            
            Return as JSON format.
            """
            
            # This would be implemented with semantic kernel prompt
            # For now, return basic structure
            vm_info = {
                "vm_name": None,
                "resource_group": None,
                "subscription_id": user_context.get("subscription_id"),
                "symptoms": user_input
            }
        
        return vm_info if vm_info.get("vm_name") or vm_info.get("resource_id") else None
    
    async def _handle_missing_vm_info(self, user_input: str) -> Dict[str, Any]:
        """Handle cases where VM information is missing."""
        
        return {
            "status": "information_needed",
            "message": """
            I need more information to help diagnose your RDP connectivity issue.
            
            Please provide:
            1. Your VM name
            2. Resource group name
            3. Any error messages you're seeing
            4. When the problem started
            
            For example: "My VM named 'my-windows-vm' in resource group 'my-rg' cannot connect via RDP. 
            I get a 'connection timed out' error."
            """,
            "requires_resolution": False,
            "escalation_needed": False
        }
    
    async def _run_diagnostic_sequence(self, vm_info: Dict[str, Any], 
                                     user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Run the comprehensive diagnostic sequence."""
        
        diagnostics = {}
        
        try:
            # 1. VM Health Check
            diagnostics["vm_health"] = await self.check_vm_health(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
            # 2. Network Security Groups Validation
            diagnostics["nsg_rules"] = await self.validate_network_security_groups(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
            # 3. Firewall Status Check
            diagnostics["firewall_status"] = await self.check_firewall_status(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
            # 4. RDP Service Status Check
            diagnostics["rdp_service"] = await self.check_rdp_service_status(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
            # 5. Network Connectivity Test
            diagnostics["network_connectivity"] = await self.test_network_connectivity(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
            # 6. Authentication Logs Analysis
            diagnostics["auth_logs"] = await self.analyze_authentication_logs(
                vm_name=vm_info["vm_name"],
                resource_group=vm_info["resource_group"],
                subscription_id=user_context.get("subscription_id")
            )
            
        except Exception as e:
            self.logger.error(f"Error in diagnostic sequence: {str(e)}")
            diagnostics["error"] = str(e)
        
        return diagnostics
    
    async def _analyze_diagnostic_results(self, diagnostics: Dict[str, Any], 
                                        user_input: str) -> Dict[str, Any]:
        """Analyze diagnostic results and generate recommendations."""
        
        analysis = {
            "issues_found": [],
            "root_causes": [],
            "recommended_actions": [],
            "requires_resolution": False,
            "escalation_needed": False,
            "confidence_level": "medium"
        }
        
        # Analyze each diagnostic result
        for check_name, result in diagnostics.items():
            if check_name == "error":
                analysis["escalation_needed"] = True
                analysis["issues_found"].append(f"Diagnostic error: {result}")
                continue
            
            if not result.get("success", False):
                analysis["issues_found"].append(f"{check_name}: {result.get('message', 'Check failed')}")
                
                # Identify specific issues and recommendations
                if check_name == "vm_health":
                    if result.get("vm_stopped"):
                        analysis["root_causes"].append("VM is stopped")
                        analysis["recommended_actions"].append("Start the VM")
                    elif result.get("vm_deallocated"):
                        analysis["root_causes"].append("VM is deallocated")
                        analysis["recommended_actions"].append("Start the VM")
                
                elif check_name == "nsg_rules":
                    if not result.get("rdp_port_open"):
                        analysis["root_causes"].append("RDP port 3389 is blocked by NSG")
                        analysis["recommended_actions"].append("Add NSG rule to allow RDP on port 3389")
                
                elif check_name == "firewall_status":
                    if result.get("firewall_blocking_rdp"):
                        analysis["root_causes"].append("Windows Firewall is blocking RDP")
                        analysis["recommended_actions"].append("Configure Windows Firewall to allow RDP")
                
                elif check_name == "rdp_service":
                    if not result.get("rdp_service_running"):
                        analysis["root_causes"].append("RDP service is not running")
                        analysis["recommended_actions"].append("Start the Remote Desktop Services")
        
        # Determine if resolution is required
        if analysis["recommended_actions"]:
            analysis["requires_resolution"] = True
        
        # Determine escalation needs
        if any("critical" in issue.lower() for issue in analysis["issues_found"]):
            analysis["escalation_needed"] = True
        
        return analysis
    
    async def _generate_diagnostic_response(self, analysis: Dict[str, Any], 
                                          vm_info: Dict[str, Any]) -> str:
        """Generate a user-friendly diagnostic response."""
        
        vm_name = vm_info.get("vm_name", "your VM")
        
        if analysis["issues_found"]:
            response = f"## Diagnostic Results for {vm_name}\n\n"
            response += "**Issues Found:**\n"
            for issue in analysis["issues_found"]:
                response += f"• {issue}\n"
            
            if analysis["root_causes"]:
                response += "\n**Root Causes:**\n"
                for cause in analysis["root_causes"]:
                    response += f"• {cause}\n"
            
            if analysis["recommended_actions"]:
                response += "\n**Recommended Actions:**\n"
                for action in analysis["recommended_actions"]:
                    response += f"• {action}\n"
            
            if analysis["requires_resolution"]:
                response += "\nI can help you implement these fixes. Would you like me to proceed with the recommended actions?"
            
        else:
            response = f"## Diagnostic Results for {vm_name}\n\n"
            response += "✅ No obvious issues found with basic diagnostics.\n\n"
            response += "The problem might be:\n"
            response += "• Network connectivity from your location\n"
            response += "• Authentication/credential issues\n"
            response += "• Temporary service interruptions\n\n"
            response += "Would you like me to run additional network tests or check authentication logs?"
        
        return response
    
    # Diagnostic function implementations
    async def check_vm_health(self, vm_name: str, resource_group: str, 
                            subscription_id: str) -> Dict[str, Any]:
        """Check VM health and status."""
        try:
            result = await self.vm_operations.get_vm_status(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "vm_status": result.get("status"),
                "vm_stopped": result.get("status") == "stopped",
                "vm_deallocated": result.get("status") == "deallocated",
                "message": f"VM status: {result.get('status')}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to check VM health: {str(e)}",
                "error": str(e)
            }
    
    async def validate_network_security_groups(self, vm_name: str, resource_group: str,
                                             subscription_id: str) -> Dict[str, Any]:
        """Validate NSG rules for RDP access."""
        try:
            result = await self.network_checks.check_nsg_rules(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "rdp_port_open": result.get("rdp_allowed"),
                "nsg_rules": result.get("rules"),
                "message": f"NSG validation: {'RDP allowed' if result.get('rdp_allowed') else 'RDP blocked'}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to validate NSG rules: {str(e)}",
                "error": str(e)
            }
    
    async def check_firewall_status(self, vm_name: str, resource_group: str,
                                  subscription_id: str) -> Dict[str, Any]:
        """Check Windows Firewall status for RDP."""
        try:
            result = await self.azure_diagnostics.check_guest_firewall(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "firewall_blocking_rdp": result.get("rdp_blocked"),
                "firewall_rules": result.get("rules"),
                "message": f"Firewall check: {'RDP blocked' if result.get('rdp_blocked') else 'RDP allowed'}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to check firewall status: {str(e)}",
                "error": str(e)
            }
    
    async def check_rdp_service_status(self, vm_name: str, resource_group: str,
                                     subscription_id: str) -> Dict[str, Any]:
        """Check RDP service status on the VM."""
        try:
            result = await self.azure_diagnostics.check_rdp_service(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "rdp_service_running": result.get("service_running"),
                "service_status": result.get("status"),
                "message": f"RDP service: {'running' if result.get('service_running') else 'stopped'}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to check RDP service: {str(e)}",
                "error": str(e)
            }
    
    async def test_network_connectivity(self, vm_name: str, resource_group: str,
                                      subscription_id: str) -> Dict[str, Any]:
        """Test network connectivity to the VM."""
        try:
            result = await self.network_checks.test_connectivity(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "connectivity_ok": result.get("reachable"),
                "latency": result.get("latency"),
                "message": f"Network connectivity: {'OK' if result.get('reachable') else 'Failed'}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to test connectivity: {str(e)}",
                "error": str(e)
            }
    
    async def analyze_authentication_logs(self, vm_name: str, resource_group: str,
                                        subscription_id: str) -> Dict[str, Any]:
        """Analyze authentication logs for RDP issues."""
        try:
            result = await self.azure_diagnostics.get_auth_logs(vm_name, resource_group, subscription_id)
            return {
                "success": True,
                "auth_failures": result.get("failures", []),
                "recent_logins": result.get("logins", []),
                "message": f"Auth analysis: {len(result.get('failures', []))} recent failures"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to analyze auth logs: {str(e)}",
                "error": str(e)
            }
