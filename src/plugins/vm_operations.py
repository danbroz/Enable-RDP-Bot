"""
VM Operations Plugin for Semantic Kernel

This plugin provides Azure VM management capabilities including start, stop,
restart, and status checking operations.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import AzureError


class VmOperationsPlugin:
    """Plugin for Azure VM management operations."""
    
    def __init__(self, credential: DefaultAzureCredential):
        self.credential = credential
        self.compute_client = ComputeManagementClient(credential, "")
        self.resource_client = ResourceManagementClient(credential, "")
        
        self.logger = logging.getLogger(__name__)
    
    async def get_vm_status(self, vm_name: str, resource_group: str,
                          subscription_id: str) -> Dict[str, Any]:
        """
        Get VM status and health information.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM status and health information
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Get VM instance view
            vm = await self.compute_client.virtual_machines.get(resource_group, vm_name)
            vm_instance_view = await self.compute_client.virtual_machines.get(
                resource_group, vm_name, expand="instanceView"
            )
            
            # Extract status information
            statuses = {}
            for status in vm_instance_view.instance_view.statuses:
                statuses[status.code] = status.display_status
            
            # Determine overall VM status
            vm_status = "unknown"
            if "PowerState/running" in statuses:
                vm_status = "running"
            elif "PowerState/stopped" in statuses:
                vm_status = "stopped"
            elif "PowerState/deallocated" in statuses:
                vm_status = "deallocated"
            
            # Get provisioning state
            provisioning_state = statuses.get("ProvisioningState/succeeded", "unknown")
            
            return {
                "success": True,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "status": vm_status,
                "provisioning_state": provisioning_state,
                "all_statuses": statuses,
                "location": vm.location,
                "vm_size": vm.hardware_profile.vm_size,
                "os_type": vm.storage_profile.os_disk.os_type,
                "message": f"VM status: {vm_status}"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting VM status: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get VM status: {str(e)}",
                "error": str(e)
            }
    
    async def start_vm(self, vm_name: str, resource_group: str,
                      subscription_id: str) -> Dict[str, Any]:
        """
        Start a stopped VM.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM start operation result
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Start the VM
            start_operation = await self.compute_client.virtual_machines.begin_start(
                resource_group, vm_name
            )
            
            # Wait for the operation to complete
            start_result = await start_operation.result()
            
            return {
                "success": True,
                "operation_id": start_operation.id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "message": f"VM {vm_name} started successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error starting VM: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to start VM: {str(e)}",
                "error": str(e)
            }
    
    async def stop_vm(self, vm_name: str, resource_group: str,
                     subscription_id: str) -> Dict[str, Any]:
        """
        Stop a running VM.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM stop operation result
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Stop the VM
            stop_operation = await self.compute_client.virtual_machines.begin_power_off(
                resource_group, vm_name
            )
            
            # Wait for the operation to complete
            stop_result = await stop_operation.result()
            
            return {
                "success": True,
                "operation_id": stop_operation.id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "message": f"VM {vm_name} stopped successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error stopping VM: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to stop VM: {str(e)}",
                "error": str(e)
            }
    
    async def restart_vm(self, vm_name: str, resource_group: str,
                        subscription_id: str) -> Dict[str, Any]:
        """
        Restart a VM.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM restart operation result
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Restart the VM
            restart_operation = await self.compute_client.virtual_machines.begin_restart(
                resource_group, vm_name
            )
            
            # Wait for the operation to complete
            restart_result = await restart_operation.result()
            
            return {
                "success": True,
                "operation_id": restart_operation.id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "message": f"VM {vm_name} restarted successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error restarting VM: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to restart VM: {str(e)}",
                "error": str(e)
            }
    
    async def deallocate_vm(self, vm_name: str, resource_group: str,
                           subscription_id: str) -> Dict[str, Any]:
        """
        Deallocate a VM to stop billing.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM deallocation operation result
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Deallocate the VM
            deallocate_operation = await self.compute_client.virtual_machines.begin_deallocate(
                resource_group, vm_name
            )
            
            # Wait for the operation to complete
            deallocate_result = await deallocate_operation.result()
            
            return {
                "success": True,
                "operation_id": deallocate_operation.id,
                "vm_name": vm_name,
                "resource_group": resource_group,
                "message": f"VM {vm_name} deallocated successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error deallocating VM: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to deallocate VM: {str(e)}",
                "error": str(e)
            }
    
    async def get_vm_metadata(self, vm_name: str, resource_group: str,
                             subscription_id: str) -> Dict[str, Any]:
        """
        Get comprehensive VM metadata.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM metadata information
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Get VM details
            vm = await self.compute_client.virtual_machines.get(resource_group, vm_name)
            
            # Extract metadata
            metadata = {
                "vm_name": vm.name,
                "resource_group": resource_group,
                "location": vm.location,
                "vm_size": vm.hardware_profile.vm_size,
                "os_type": vm.storage_profile.os_disk.os_type,
                "computer_name": vm.os_profile.computer_name,
                "admin_username": vm.os_profile.admin_username,
                "provision_vm_agent": vm.os_profile.windows_configuration.provision_vm_agent if vm.os_profile.windows_configuration else None,
                "enable_automatic_updates": vm.os_profile.windows_configuration.enable_automatic_updates if vm.os_profile.windows_configuration else None,
                "network_interfaces": [],
                "data_disks": [],
                "tags": vm.tags or {}
            }
            
            # Get network interface information
            for nic_ref in vm.network_profile.network_interfaces:
                nic_name = nic_ref.id.split('/')[-1]
                metadata["network_interfaces"].append({
                    "name": nic_name,
                    "id": nic_ref.id,
                    "primary": nic_ref.primary
                })
            
            # Get data disk information
            if vm.storage_profile.data_disks:
                for disk in vm.storage_profile.data_disks:
                    metadata["data_disks"].append({
                        "name": disk.name,
                        "lun": disk.lun,
                        "disk_size_gb": disk.disk_size_gb,
                        "caching": disk.caching,
                        "create_option": disk.create_option
                    })
            
            return {
                "success": True,
                "metadata": metadata,
                "message": "VM metadata retrieved successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error getting VM metadata: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to get VM metadata: {str(e)}",
                "error": str(e)
            }
    
    async def run_vm_command(self, vm_name: str, resource_group: str,
                           subscription_id: str, command: str,
                           parameters: List[str] = None) -> Dict[str, Any]:
        """
        Run a command on the VM using Azure VM Run Command.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            command: Command to run
            parameters: Command parameters
            
        Returns:
            Command execution result
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            if parameters is None:
                parameters = []
            
            # Prepare run command parameters
            run_command_parameters = {
                "command_id": "RunPowerShellScript",
                "script": [command],
                "parameters": [{"name": f"param{i}", "value": param} for i, param in enumerate(parameters)]
            }
            
            # Execute the command
            run_command_operation = await self.compute_client.virtual_machines.begin_run_command(
                resource_group, vm_name, run_command_parameters
            )
            
            # Wait for the operation to complete
            run_command_result = await run_command_operation.result()
            
            return {
                "success": True,
                "operation_id": run_command_operation.id,
                "command": command,
                "parameters": parameters,
                "output": run_command_result.value[0].message if run_command_result.value else "",
                "message": "Command executed successfully"
            }
            
        except Exception as e:
            self.logger.error(f"Error running VM command: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to run command: {str(e)}",
                "error": str(e)
            }
    
    async def check_vm_health_extension(self, vm_name: str, resource_group: str,
                                      subscription_id: str) -> Dict[str, Any]:
        """
        Check VM health using Azure VM Health Extension.
        
        Args:
            vm_name: Name of the VM
            resource_group: Resource group containing the VM
            subscription_id: Azure subscription ID
            
        Returns:
            VM health status
        """
        try:
            # Set subscription
            self.compute_client.config.subscription_id = subscription_id
            
            # Get VM extensions
            extensions = await self.compute_client.virtual_machine_extensions.list(
                resource_group, vm_name
            )
            
            # Look for health extension
            health_extension = None
            for extension in extensions:
                if extension.name == "HealthExtension":
                    health_extension = extension
                    break
            
            if health_extension:
                return {
                    "success": True,
                    "health_extension_found": True,
                    "health_status": health_extension.instance_view.statuses[0].display_status if health_extension.instance_view.statuses else "unknown",
                    "provisioning_state": health_extension.provisioning_state,
                    "message": "Health extension status retrieved"
                }
            else:
                return {
                    "success": True,
                    "health_extension_found": False,
                    "message": "Health extension not found"
                }
                
        except Exception as e:
            self.logger.error(f"Error checking VM health extension: {str(e)}")
            return {
                "success": False,
                "message": f"Failed to check health extension: {str(e)}",
                "error": str(e)
            }
