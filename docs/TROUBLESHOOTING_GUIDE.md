# RDP Troubleshooting Guide

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.

## 🎯 Overview

This guide provides comprehensive procedures for troubleshooting Windows VM RDP connectivity issues using the Enable RDP Bot tool.

## 🔍 Common RDP Issues

### 1. VM Power State Issues
- **Symptom**: Cannot connect to RDP
- **Cause**: VM is stopped, deallocated, or in failed state
- **Diagnosis**: Check VM power state in Azure portal or via CLI
- **Resolution**: Start the VM if stopped

### 2. Network Security Group (NSG) Issues
- **Symptom**: Connection timeout or refused
- **Cause**: NSG rules blocking RDP port 3389
- **Diagnosis**: Check inbound NSG rules for port 3389
- **Resolution**: Add or modify NSG rules to allow RDP

### 3. Network Interface Issues
- **Symptom**: Intermittent connectivity
- **Cause**: Network interface configuration problems
- **Diagnosis**: Check network interface status and configuration
- **Resolution**: Restart network interface or reconfigure

### 4. OS-Level RDP Service Issues
- **Symptom**: Connection established but authentication fails
- **Cause**: RDP service disabled or misconfigured
- **Diagnosis**: Check Windows RDP service status
- **Resolution**: Enable and configure RDP service

## 🛠️ Troubleshooting Procedures

### Step 1: Basic VM Status Check

```bash
# Check VM status
python enable_rdp.py --rg my-rg --vm my-vm
```

**What to Look For:**
- VM power state (should be "running")
- VM size and configuration
- OS type (Windows)
- Network interface count

**Common Issues:**
- VM stopped: `"power_state": "stopped"`
- VM deallocated: `"power_state": "deallocated"`
- VM failed: `"power_state": "failed"`

### Step 2: Network Security Group Analysis

```bash
# Detailed NSG analysis
python enable_rdp.py --rg my-rg --vm my-vm
```

**What to Look For:**
- RDP port 3389 access rules
- Source IP restrictions
- Protocol settings (TCP)
- Rule priority and order

**Common Issues:**
- No RDP rules: `"rdp_allowed": false`
- Restrictive source IPs: `"source": "10.0.0.0/8"`
- Wrong protocol: `"protocol": "UDP"`

### Step 3: AI-Powered Analysis

The tool automatically runs AI analysis using GPT-5 (with fallback to GPT-4) to identify root causes and provide recommendations.

**AI Analysis Output:**
```json
{
  "ai_analysis": {
    "root_cause": "VM is running but NSG rules block RDP access",
    "fix_steps": [
      "Add NSG rule to allow RDP from your IP",
      "Verify rule priority and order",
      "Test connectivity after changes"
    ],
    "prevention": [
      "Document NSG rule changes",
      "Use Azure Policy for NSG compliance",
      "Regular security reviews"
    ],
    "priority": "High",
    "confidence": 0.95
  }
}
```

## 🔧 Manual Troubleshooting Steps

### 1. VM Power State Issues

**Check VM Status:**
```bash
az vm show --resource-group my-rg --name my-vm --show-details
```

**Start VM if Stopped:**
```bash
az vm start --resource-group my-rg --name my-vm
```

**Check Boot Diagnostics:**
```bash
az vm boot-diagnostics get-boot-log --resource-group my-rg --name my-vm
```

### 2. Network Security Group Issues

**List NSG Rules:**
```bash
az network nsg rule list --resource-group my-rg --nsg-name my-nsg
```

**Add RDP Rule:**
```bash
az network nsg rule create \
  --resource-group my-rg \
  --nsg-name my-nsg \
  --name AllowRDP \
  --priority 1000 \
  --source-address-prefixes '*' \
  --destination-port-ranges 3389 \
  --access Allow \
  --protocol Tcp \
  --direction Inbound
```

**Check Rule Priority:**
- Lower numbers = higher priority
- Ensure RDP rule has higher priority than deny rules

### 3. Network Interface Issues

**Check Network Interface:**
```bash
az network nic show --resource-group my-rg --name my-nic
```

**Check IP Configuration:**
```bash
az network nic ip-config list --resource-group my-rg --nic-name my-nic
```

**Restart Network Interface:**
```bash
az network nic update --resource-group my-rg --name my-nic --force
```

### 4. OS-Level RDP Issues

**Connect via Serial Console:**
```bash
az vm serial-console connect --resource-group my-rg --name my-vm
```

**Check RDP Service Status:**
```cmd
# In Windows VM
sc query TermService
sc config TermService start= auto
sc start TermService
```

**Check Windows Firewall:**
```cmd
# In Windows VM
netsh advfirewall firewall show rule name="Remote Desktop"
netsh advfirewall firewall set rule group="Remote Desktop" new enable=Yes
```

## 🚨 Emergency Procedures

### 1. VM Unresponsive

**Force Restart:**
```bash
az vm restart --resource-group my-rg --name my-vm --force
```

**Check Resource Health:**
```bash
az resource show --resource-group my-rg --name my-vm --resource-type Microsoft.Compute/virtualMachines
```

### 2. Network Completely Blocked

**Emergency NSG Rule:**
```bash
az network nsg rule create \
  --resource-group my-rg \
  --nsg-name my-nsg \
  --name EmergencyRDP \
  --priority 100 \
  --source-address-prefixes '0.0.0.0/0' \
  --destination-port-ranges 3389 \
  --access Allow \
  --protocol Tcp \
  --direction Inbound
```

**Remove Emergency Rule After Fix:**
```bash
az network nsg rule delete --resource-group my-rg --nsg-name my-nsg --name EmergencyRDP
```

### 3. Authentication Issues

**Reset VM Password:**
```bash
az vm user update \
  --resource-group my-rg \
  --name my-vm \
  --username adminuser \
  --password 'NewPassword123!'
```

**Check VM Extension Status:**
```bash
az vm extension list --resource-group my-rg --vm-name my-vm
```

## 📊 Diagnostic Commands

### Comprehensive VM Check
```bash
# Full diagnostic run
python enable_rdp.py --rg my-rg --vm my-vm
```

### Network Connectivity Test
```bash
# Test from another VM in same VNet
telnet <vm-private-ip> 3389
```

### Port Scanning
```bash
# Scan for open ports
nmap -p 3389 <vm-public-ip>
```

## 🔍 Troubleshooting Checklist

### Pre-Troubleshooting
- [ ] Verify Azure CLI authentication
- [ ] Confirm resource group and VM names
- [ ] Check OpenAI API key configuration
- [ ] Ensure appropriate Azure permissions

### VM Status
- [ ] VM is running (not stopped/deallocated)
- [ ] VM has valid network interface
- [ ] VM OS is Windows
- [ ] VM size supports RDP

### Network Configuration
- [ ] NSG allows inbound RDP (port 3389)
- [ ] NSG rule priority is correct
- [ ] Source IP is not restricted
- [ ] Protocol is TCP

### OS Configuration
- [ ] RDP service is enabled
- [ ] Windows Firewall allows RDP
- [ ] User account has RDP permissions
- [ ] RDP is not disabled by group policy

### Connectivity
- [ ] Public IP is assigned (if needed)
- [ ] DNS resolution works
- [ ] Network routing is correct
- [ ] No intermediate firewalls blocking

## 📈 Performance Optimization

### NSG Rule Optimization
- Use specific source IP ranges instead of wildcards
- Combine multiple ports in single rules when possible
- Remove unused rules to improve performance
- Use service tags for common scenarios

### VM Configuration
- Use appropriate VM size for workload
- Enable accelerated networking if supported
- Configure proper disk caching
- Monitor resource utilization

## 🛡️ Security Best Practices

### NSG Security
- Use specific source IP ranges
- Implement least privilege access
- Regular security rule reviews
- Document all rule changes

### RDP Security
- Use strong passwords
- Enable multi-factor authentication
- Regular password rotation
- Monitor RDP access logs

### Network Security
- Use private endpoints when possible
- Implement network segmentation
- Regular security assessments
- Monitor network traffic

## 📋 Common Error Messages

### "VM not found"
- Check resource group name
- Verify VM name spelling
- Confirm subscription context

### "Access denied"
- Check Azure CLI authentication
- Verify RBAC permissions
- Confirm subscription access

### "NSG rule not found"
- Check NSG name
- Verify rule exists
- Check rule priority

### "Connection timeout"
- Check NSG rules
- Verify VM is running
- Check network connectivity

## 🔄 Automation and Scripting

### Batch Processing
```bash
# Process multiple VMs
for vm in vm1 vm2 vm3; do
  python enable_rdp.py --rg my-rg --vm $vm
done
```

### Scheduled Monitoring
```bash
# Daily RDP health check
0 9 * * * /path/to/enable_rdp.py --rg prod-rg --vm web-server
```

### Integration with CI/CD
```yaml
# Azure DevOps pipeline step
- script: |
    python enable_rdp.py --rg $(resourceGroup) --vm $(vmName)
  displayName: 'RDP Health Check'
```
