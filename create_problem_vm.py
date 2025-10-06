#!/usr/bin/env python3
"""
Create a Problem VM in Azure for Testing Agentic AI Support Bot
This script creates a Windows VM with intentional RDP issues
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
from azure.mgmt.storage import StorageManagementClient
import random
import string

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureVMBuilder:
    """Builds Azure VMs with intentional problems for testing"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        try:
            self.credential = DefaultAzureCredential()
            self.compute_client = ComputeManagementClient(self.credential, subscription_id)
            self.network_client = NetworkManagementClient(self.credential, subscription_id)
            self.resource_client = ResourceManagementClient(self.credential, subscription_id)
            self.storage_client = StorageManagementClient(self.credential, subscription_id)
            logger.info(f"✅ Connected to Azure subscription: {subscription_id}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Azure: {e}")
            raise

    def generate_random_name(self, prefix: str, length: int = 8) -> str:
        """Generate a random name for Azure resources"""
        suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
        return f"{prefix}-{suffix}"

    async def create_resource_group(self, resource_group_name: str, location: str = "East US") -> bool:
        """Create a resource group"""
        try:
            logger.info(f"📁 Creating resource group: {resource_group_name}")
            
            # Check if resource group already exists
            try:
                existing_rg = self.resource_client.resource_groups.get(resource_group_name)
                logger.info(f"✅ Resource group already exists: {resource_group_name}")
                return True
            except:
                pass  # Resource group doesn't exist, create it
            
            # Create resource group
            self.resource_client.resource_groups.create_or_update(
                resource_group_name,
                {"location": location, "tags": {"Purpose": "AI Support Bot Testing", "CreatedBy": "Python"}}
            )
            
            logger.info(f"✅ Resource group created: {resource_group_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creating resource group: {e}")
            return False

    async def create_virtual_network(self, resource_group_name: str, vnet_name: str, location: str) -> Optional[str]:
        """Create virtual network and subnet"""
        try:
            logger.info(f"🌐 Creating virtual network: {vnet_name}")
            
            # Create virtual network
            vnet_params = {
                "location": location,
                "address_space": {"address_prefixes": ["10.0.0.0/16"]},
                "tags": {"Purpose": "AI Support Bot Testing"}
            }
            
            vnet_operation = self.network_client.virtual_networks.begin_create_or_update(
                resource_group_name, vnet_name, vnet_params
            )
            vnet = vnet_operation.result()
            
            # Create subnet
            subnet_name = f"{vnet_name}-subnet"
            subnet_params = {
                "address_prefix": "10.0.1.0/24"
            }
            
            subnet_operation = self.network_client.subnets.begin_create_or_update(
                resource_group_name, vnet_name, subnet_name, subnet_params
            )
            subnet = subnet_operation.result()
            
            logger.info(f"✅ Virtual network created: {vnet_name}")
            return subnet.id
            
        except Exception as e:
            logger.error(f"❌ Error creating virtual network: {e}")
            return None

    async def create_network_security_group(self, resource_group_name: str, nsg_name: str, location: str) -> Optional[str]:
        """Create NSG with RDP BLOCKED (intentional problem)"""
        try:
            logger.info(f"🔒 Creating NSG with RDP BLOCKED: {nsg_name}")
            
            # Create NSG with RDP BLOCKED rule
            nsg_params = {
                "location": location,
                "security_rules": [
                    {
                        "name": "DenyRDP",
                        "priority": 1000,
                        "direction": "Inbound",
                        "access": "Deny",  # INTENTIONALLY BLOCKING RDP
                        "protocol": "Tcp",
                        "source_port_range": "*",
                        "destination_port_range": "3389",
                        "source_address_prefix": "*",
                        "destination_address_prefix": "*",
                        "description": "BLOCK RDP - Intentional problem for AI testing"
                    },
                    {
                        "name": "AllowHTTP",
                        "priority": 1001,
                        "direction": "Inbound",
                        "access": "Allow",
                        "protocol": "Tcp",
                        "source_port_range": "*",
                        "destination_port_range": "80",
                        "source_address_prefix": "*",
                        "destination_address_prefix": "*"
                    }
                ],
                "tags": {"Purpose": "AI Support Bot Testing", "Problem": "RDP Blocked"}
            }
            
            nsg_operation = self.network_client.network_security_groups.begin_create_or_update(
                resource_group_name, nsg_name, nsg_params
            )
            nsg = nsg_operation.result()
            
            logger.info(f"✅ NSG created with RDP BLOCKED: {nsg_name}")
            return nsg.id
            
        except Exception as e:
            logger.error(f"❌ Error creating NSG: {e}")
            return None

    async def create_public_ip(self, resource_group_name: str, pip_name: str, location: str) -> Optional[str]:
        """Create public IP address"""
        try:
            logger.info(f"🌍 Creating public IP: {pip_name}")
            
            pip_params = {
                "location": location,
                "public_ip_allocation_method": "Static",
                "sku": {"name": "Standard"},
                "tags": {"Purpose": "AI Support Bot Testing"}
            }
            
            pip_operation = self.network_client.public_ip_addresses.begin_create_or_update(
                resource_group_name, pip_name, pip_params
            )
            pip = pip_operation.result()
            
            logger.info(f"✅ Public IP created: {pip_name}")
            return pip.id
            
        except Exception as e:
            logger.error(f"❌ Error creating public IP: {e}")
            return None

    async def create_network_interface(self, resource_group_name: str, nic_name: str, location: str, 
                                     subnet_id: str, pip_id: str, nsg_id: str) -> Optional[str]:
        """Create network interface"""
        try:
            logger.info(f"🔌 Creating network interface: {nic_name}")
            
            nic_params = {
                "location": location,
                "ip_configurations": [
                    {
                        "name": f"{nic_name}-ipconfig",
                        "subnet": {"id": subnet_id},
                        "public_ip_address": {"id": pip_id}
                    }
                ],
                "network_security_group": {"id": nsg_id},
                "tags": {"Purpose": "AI Support Bot Testing"}
            }
            
            nic_operation = self.network_client.network_interfaces.begin_create_or_update(
                resource_group_name, nic_name, nic_params
            )
            nic = nic_operation.result()
            
            logger.info(f"✅ Network interface created: {nic_name}")
            return nic.id
            
        except Exception as e:
            logger.error(f"❌ Error creating network interface: {e}")
            return None

    async def create_windows_vm(self, resource_group_name: str, vm_name: str, location: str, 
                              nic_id: str) -> Optional[Dict[str, Any]]:
        """Create Windows VM (will be stopped after creation)"""
        try:
            logger.info(f"🖥️  Creating Windows VM: {vm_name}")
            
            # Use a small VM size for testing
            vm_size = "Standard_B2s"
            
            vm_params = {
                "location": location,
                "hardware_profile": {"vm_size": vm_size},
                "storage_profile": {
                    "image_reference": {
                        "publisher": "MicrosoftWindowsServer",
                        "offer": "WindowsServer",
                        "sku": "2019-Datacenter",
                        "version": "latest"
                    },
                    "os_disk": {
                        "create_option": "FromImage",
                        "caching": "ReadWrite",
                        "managed_disk": {"storage_account_type": "Standard_LRS"}
                    }
                },
                "os_profile": {
                    "computer_name": vm_name,
                    "admin_username": "azureuser",
                    "admin_password": "AzurePassword123!",  # In production, use Key Vault
                    "windows_configuration": {
                        "enable_automatic_updates": True,
                        "provision_vm_agent": True
                    }
                },
                "network_profile": {
                    "network_interfaces": [{"id": nic_id, "primary": True}]
                },
                "tags": {
                    "Purpose": "AI Support Bot Testing",
                    "Problem": "Stopped VM",
                    "Status": "Will be stopped after creation"
                }
            }
            
            vm_operation = self.compute_client.virtual_machines.begin_create_or_update(
                resource_group_name, vm_name, vm_params
            )
            vm = vm_operation.result()
            
            logger.info(f"✅ Windows VM created: {vm_name}")
            
            # Get public IP address
            pip_name = f"{vm_name}-pip"
            pip = self.network_client.public_ip_addresses.get(resource_group_name, pip_name)
            
            return {
                "vm_id": vm.id,
                "vm_name": vm.name,
                "public_ip": pip.ip_address,
                "admin_username": "azureuser",
                "admin_password": "AzurePassword123!",
                "resource_group": resource_group_name,
                "location": location
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating VM: {e}")
            return None

    async def stop_vm(self, resource_group_name: str, vm_name: str) -> bool:
        """Stop the VM (intentional problem)"""
        try:
            logger.info(f"⏹️  Stopping VM (intentional problem): {vm_name}")
            
            stop_operation = self.compute_client.virtual_machines.begin_deallocate(
                resource_group_name, vm_name
            )
            stop_operation.result()
            
            logger.info(f"✅ VM stopped (deallocated): {vm_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error stopping VM: {e}")
            return False

    async def create_problem_vm(self, base_name: str = "ai-problem-vm") -> Optional[Dict[str, Any]]:
        """Create a complete problem VM setup"""
        try:
            logger.info("🚀 Starting problem VM creation...")
            
            # Generate unique names
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            resource_group_name = f"{base_name}-rg-{timestamp}"
            location = "East US"
            
            # Create resource group
            if not await self.create_resource_group(resource_group_name, location):
                return None
            
            # Create virtual network
            vnet_name = f"{base_name}-vnet-{timestamp}"
            subnet_id = await self.create_virtual_network(resource_group_name, vnet_name, location)
            if not subnet_id:
                return None
            
            # Create NSG with RDP blocked
            nsg_name = f"{base_name}-nsg-{timestamp}"
            nsg_id = await self.create_network_security_group(resource_group_name, nsg_name, location)
            if not nsg_id:
                return None
            
            # Create public IP
            pip_name = f"{base_name}-pip-{timestamp}"
            pip_id = await self.create_public_ip(resource_group_name, pip_name, location)
            if not pip_id:
                return None
            
            # Create network interface
            nic_name = f"{base_name}-nic-{timestamp}"
            nic_id = await self.create_network_interface(resource_group_name, nic_name, location, 
                                                       subnet_id, pip_id, nsg_id)
            if not nic_id:
                return None
            
            # Create Windows VM
            vm_name = f"{base_name}-{timestamp}"
            vm_info = await self.create_windows_vm(resource_group_name, vm_name, location, nic_id)
            if not vm_info:
                return None
            
            # Stop the VM (intentional problem)
            await self.stop_vm(resource_group_name, vm_name)
            
            # Add additional info
            vm_info.update({
                "nsg_name": nsg_name,
                "vnet_name": vnet_name,
                "problems": [
                    "1. RDP port 3389 is BLOCKED by Network Security Group",
                    "2. VM is STOPPED (deallocated) - not running",
                    "3. VM has limited resources (Standard_B2s)",
                    "4. Boot diagnostics are disabled"
                ],
                "testing_instructions": [
                    "1. Run: python3 test_real_vm.py",
                    "2. AI should detect NSG blocking RDP",
                    "3. AI should detect VM is stopped",
                    "4. AI should provide specific remediation steps"
                ]
            })
            
            logger.info("🎉 Problem VM created successfully!")
            return vm_info
            
        except Exception as e:
            logger.error(f"❌ Error creating problem VM: {e}")
            return None

async def main():
    """Main function to create problem VM"""
    
    print("🚀 Creating Problem VM for Agentic AI Support Bot Testing")
    print("=" * 60)
    print("This will create a Windows VM with intentional RDP issues:")
    print("1. NSG will BLOCK RDP port 3389")
    print("2. VM will be STOPPED after creation")
    print("3. VM will have limited resources")
    print()
    
    # Load environment variables
    subscription_id = "your-subscription-id-here"
    
    try:
        # Initialize VM builder
        builder = AzureVMBuilder(subscription_id)
        
        # Create problem VM
        vm_info = await builder.create_problem_vm()
        
        if vm_info:
            print("\n" + "=" * 60)
            print("✅ PROBLEM VM CREATED SUCCESSFULLY!")
            print("=" * 60)
            
            print(f"\n📋 VM Details:")
            print(f"   VM Name: {vm_info['vm_name']}")
            print(f"   Resource Group: {vm_info['resource_group']}")
            print(f"   Public IP: {vm_info['public_ip']}")
            print(f"   Admin Username: {vm_info['admin_username']}")
            print(f"   Location: {vm_info['location']}")
            
            print(f"\n🚨 Intentional Problems Created:")
            for problem in vm_info['problems']:
                print(f"   {problem}")
            
            print(f"\n🧪 Testing Instructions:")
            for instruction in vm_info['testing_instructions']:
                print(f"   {instruction}")
            
            print(f"\n🤖 Next Steps:")
            print("1. Run: python3 test_real_vm.py")
            print("2. The AI agent will analyze the real VM")
            print("3. AI will detect the RDP blocking and VM stopped issues")
            print("4. AI will provide specific remediation steps")
            
            # Save VM info to file for the test script
            import json
            with open('problem_vm_info.json', 'w') as f:
                json.dump(vm_info, f, indent=2)
            print(f"\n💾 VM info saved to: problem_vm_info.json")
            
        else:
            print("❌ Failed to create problem VM")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.error(f"Main error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
