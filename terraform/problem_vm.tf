# Problem VM for Testing Agentic AI Support Bot
# This creates a Windows VM with intentional RDP issues

terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# Resource Group for the problem VM
resource "azurerm_resource_group" "problem_vm_rg" {
  name     = "ai-support-bot-test-rg"
  location = "East US"
  
  tags = {
    Environment = "Testing"
    Purpose     = "Agentic AI Support Bot Demo"
    CreatedBy   = "Terraform"
  }
}

# Virtual Network
resource "azurerm_virtual_network" "problem_vm_vnet" {
  name                = "problem-vm-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.problem_vm_rg.location
  resource_group_name = azurerm_resource_group.problem_vm_rg.name
}

# Subnet
resource "azurerm_subnet" "problem_vm_subnet" {
  name                 = "problem-vm-subnet"
  resource_group_name  = azurerm_resource_group.problem_vm_rg.name
  virtual_network_name = azurerm_virtual_network.problem_vm_vnet.name
  address_prefixes     = ["10.0.1.0/24"]
}

# Network Security Group - INTENTIONALLY BLOCKING RDP
resource "azurerm_network_security_group" "problem_vm_nsg" {
  name                = "problem-vm-nsg"
  location            = azurerm_resource_group.problem_vm_rg.location
  resource_group_name = azurerm_resource_group.problem_vm_rg.name

  # BLOCK RDP - This is the problem we want our AI to detect
  security_rule {
    name                       = "DenyRDP"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Deny"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "3389"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
    description                = "BLOCK RDP - Intentional problem for AI testing"
  }

  # Allow HTTP for testing
  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  tags = {
    Environment = "Testing"
    Purpose     = "Block RDP for AI testing"
  }
}

# Public IP
resource "azurerm_public_ip" "problem_vm_pip" {
  name                = "problem-vm-pip"
  resource_group_name = azurerm_resource_group.problem_vm_rg.name
  location            = azurerm_resource_group.problem_vm_rg.location
  allocation_method   = "Static"
  sku                 = "Standard"

  tags = {
    Environment = "Testing"
  }
}

# Network Interface
resource "azurerm_network_interface" "problem_vm_nic" {
  name                = "problem-vm-nic"
  location            = azurerm_resource_group.problem_vm_rg.location
  resource_group_name = azurerm_resource_group.problem_vm_rg.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.problem_vm_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.problem_vm_pip.id
  }

  tags = {
    Environment = "Testing"
  }
}

# Associate NSG with NIC
resource "azurerm_network_interface_security_group_association" "problem_vm_nsg_assoc" {
  network_interface_id      = azurerm_network_interface.problem_vm_nic.id
  network_security_group_id = azurerm_network_security_group.problem_vm_nsg.id
}

# Windows Virtual Machine - INTENTIONALLY STOPPED
resource "azurerm_windows_virtual_machine" "problem_vm" {
  name                = "problem-vm-test"
  resource_group_name = azurerm_resource_group.problem_vm_rg.name
  location            = azurerm_resource_group.problem_vm_rg.location
  size                = "Standard_B2s"  # Small VM for testing
  admin_username      = "azureuser"
  admin_password      = "AzurePassword123!"  # In production, use Key Vault

  # Disable boot diagnostics to create another potential issue
  boot_diagnostics {
    storage_account_uri = null
  }

  network_interface_ids = [
    azurerm_network_interface.problem_vm_nic.id,
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "MicrosoftWindowsServer"
    offer     = "WindowsServer"
    sku       = "2019-Datacenter"
    version   = "latest"
  }

  # Enable RDP (but NSG will block it)
  enable_automatic_updates = true

  tags = {
    Environment = "Testing"
    Purpose     = "AI Support Bot Problem VM"
    Status      = "Stopped"  # Intentionally stopped
  }
}

# Storage Account for diagnostics (optional)
resource "azurerm_storage_account" "problem_vm_storage" {
  name                     = "aiproblemvmstorage${random_string.storage_suffix.result}"
  resource_group_name      = azurerm_resource_group.problem_vm_rg.name
  location                 = azurerm_resource_group.problem_vm_rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    Environment = "Testing"
  }
}

# Random string for storage account name
resource "random_string" "storage_suffix" {
  length  = 8
  special = false
  upper   = false
}

# Output important information
output "vm_info" {
  value = {
    vm_name          = azurerm_windows_virtual_machine.problem_vm.name
    resource_group   = azurerm_resource_group.problem_vm_rg.name
    public_ip        = azurerm_public_ip.problem_vm_pip.ip_address
    admin_username   = azurerm_windows_virtual_machine.problem_vm.admin_username
    nsg_name         = azurerm_network_security_group.problem_vm_nsg.name
    location         = azurerm_resource_group.problem_vm_rg.location
  }
  description = "Information about the problem VM for AI testing"
}

output "vm_issues" {
  value = [
    "1. RDP port 3389 is BLOCKED by Network Security Group",
    "2. VM is intentionally STOPPED (not running)",
    "3. Boot diagnostics are DISABLED",
    "4. VM has limited resources (Standard_B2s)"
  ]
  description = "Intentional problems created for AI testing"
}

output "testing_instructions" {
  value = <<-EOT
    This VM has been created with intentional RDP issues:
    
    1. NSG Rule: RDP port 3389 is BLOCKED (Deny rule)
    2. VM State: VM will be STOPPED after creation
    3. Boot Diagnostics: Disabled (potential issue)
    
    To test the AI agent:
    1. Run: python3 test_real_vm.py
    2. The AI should detect both the NSG blocking and VM stopped issues
    3. AI should provide specific remediation steps
    
    To manually verify issues:
    1. Check NSG: az network nsg rule list --nsg-name problem-vm-nsg --resource-group ai-support-bot-test-rg
    2. Check VM status: az vm show --name problem-vm-test --resource-group ai-support-bot-test-rg --show-details
    3. Try RDP: Should fail due to NSG blocking
  EOT
}
