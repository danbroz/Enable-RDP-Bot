# RDP Troubleshooting Playbook - Windows VM Connectivity Issues

## Overview

This playbook provides a comprehensive framework for diagnosing and resolving Windows VM RDP connectivity issues using Azure-native diagnostic tools and services. The playbook is designed to be executed by the AI diagnostic agent but can also serve as a reference for human support engineers.

## Diagnostic Framework

### Prerequisites
- Azure subscription with appropriate permissions
- Access to Azure Resource Graph, Monitor, and Network Watcher
- VM Guest Diagnostics enabled
- Network connectivity to Azure services

### Diagnostic Sequence
The diagnostic process follows a systematic approach from basic connectivity checks to deep technical analysis:

```
1. VM Health Check → 2. Network Security → 3. VM Configuration → 
4. Network Connectivity → 5. Authentication → 6. Performance Analysis
```

## Detailed Diagnostic Procedures

### 1. VM Health and Status Check

#### 1.1 Power State Verification
**Tool**: Azure Resource Graph, Compute Management API
**Query**: 
```kusto
Resources
| where type == "microsoft.compute/virtualmachines"
| where name == "{vm_name}"
| extend powerState = properties.extended.instanceView.statuses[1].displayStatus
| project name, powerState, resourceGroup
```

**Expected Results**:
- ✅ **Running**: VM is powered on and operational
- ❌ **Stopped**: VM is shut down, needs to be started
- ❌ **Deallocated**: VM is stopped and deallocated, needs to be started
- ❌ **Unknown**: VM state unclear, requires investigation

**Resolution Actions**:
- **Stopped**: Start VM using Azure portal or PowerShell
- **Deallocated**: Start VM (will allocate resources first)
- **Unknown**: Check Azure service health and retry

#### 1.2 Provisioning State Check
**Tool**: Azure Resource Graph
**Query**:
```kusto
Resources
| where type == "microsoft.compute/virtualmachines"
| where name == "{vm_name}"
| extend provisioningState = properties.provisioningState
| project name, provisioningState, resourceGroup
```

**Expected Results**:
- ✅ **Succeeded**: VM provisioning completed successfully
- ❌ **Failed**: VM provisioning failed, requires manual intervention
- ❌ **Creating/Updating**: VM is still being provisioned

### 2. Network Security Group (NSG) Analysis

#### 2.1 NSG Rule Validation for RDP
**Tool**: Azure Resource Graph, Network Management API
**Query**:
```kusto
Resources
| where type == "microsoft.network/networksecuritygroups"
| where name in ({nsg_names})
| extend rules = properties.securityRules
| mvexpand rules
| where rules.destinationPortRange == "3389" or rules.destinationPortRanges contains "3389"
| project nsgName = name, ruleName = rules.name, access = rules.access, 
         direction = rules.direction, protocol = rules.protocol
```

**Critical Checks**:
- **Inbound Rules**: Verify RDP (port 3389) is allowed from source
- **Priority**: Check rule priority (lower numbers = higher priority)
- **Source**: Validate source address prefix/cidr
- **Protocol**: Confirm TCP protocol is specified

**Common Issues**:
- ❌ **No RDP Rule**: NSG blocks all inbound RDP traffic
- ❌ **Wrong Source**: Rule allows only specific IPs, not customer's IP
- ❌ **Wrong Port**: Rule configured for different port
- ❌ **Deny Rule**: Higher priority rule explicitly denies RDP

#### 2.2 NSG Association Check
**Tool**: Azure Resource Graph
**Query**:
```kusto
Resources
| where type == "microsoft.compute/virtualmachines"
| where name == "{vm_name}"
| extend networkInterfaces = properties.networkProfile.networkInterfaces
| mvexpand networkInterfaces
| extend nicId = networkInterfaces.id
| join kind=leftouter (
    Resources
    | where type == "microsoft.network/networkinterfaces"
    | extend networkSecurityGroup = properties.networkSecurityGroup.id
) on $left.nicId == $right.id
```

**Resolution Actions**:
- **Missing NSG**: Create NSG with appropriate RDP rules
- **Wrong NSG**: Update NSG association to correct one
- **Incorrect Rules**: Modify NSG rules to allow RDP access

### 3. VM-Level Configuration Analysis

#### 3.1 Windows Firewall Status
**Tool**: Azure VM Guest Diagnostics, Run Command
**PowerShell Command**:
```powershell
Get-NetFirewallRule -DisplayName "*Remote Desktop*" | 
Select-Object DisplayName, Enabled, Direction, Action, Profile
```

**Expected Results**:
- ✅ **Enabled**: RDP firewall rule is active
- ❌ **Disabled**: RDP firewall rule is disabled
- ❌ **Missing**: No RDP firewall rule exists

**Resolution Actions**:
- **Enable Rule**: `Enable-NetFirewallRule -DisplayName "Remote Desktop"`
- **Create Rule**: Create new firewall rule for RDP access
- **Check Profile**: Ensure rule applies to correct network profile

#### 3.2 RDP Service Status
**Tool**: Azure VM Guest Diagnostics, Run Command
**PowerShell Command**:
```powershell
Get-Service -Name "TermService" | 
Select-Object Name, Status, StartType
```

**Expected Results**:
- ✅ **Running**: RDP service is active and accepting connections
- ❌ **Stopped**: RDP service is not running
- ❌ **Disabled**: RDP service is disabled and won't start

**Resolution Actions**:
- **Start Service**: `Start-Service -Name "TermService"`
- **Set Auto-Start**: `Set-Service -Name "TermService" -StartupType Automatic`
- **Enable Service**: `Set-Service -Name "TermService" -StartupType Automatic`

#### 3.3 RDP Configuration
**Tool**: Azure VM Guest Diagnostics, Run Command
**Registry Check**:
```powershell
Get-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections"
```

**Expected Results**:
- ✅ **0**: RDP connections are allowed
- ❌ **1**: RDP connections are denied

**Resolution Actions**:
- **Enable RDP**: `Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0`

### 4. Network Connectivity Testing

#### 4.1 End-to-End Connectivity Test
**Tool**: Azure Network Watcher Connectivity Check
**API Call**:
```http
POST https://management.azure.com/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/networkWatchers/{networkWatcherName}/connectivityCheck?api-version=2021-05-01

{
  "source": {
    "resourceId": "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.Network/virtualNetworks/{vnetName}/subnets/{subnetName}"
  },
  "destination": {
    "address": "{vm_private_ip}",
    "port": 3389
  }
}
```

**Metrics Analyzed**:
- **Reachability**: Can the destination be reached?
- **Latency**: Round-trip time in milliseconds
- **Hops**: Network path analysis
- **Packet Loss**: Percentage of lost packets

#### 4.2 Port Accessibility Test
**Tool**: Azure VM Run Command
**PowerShell Command**:
```powershell
Test-NetConnection -ComputerName localhost -Port 3389 -InformationLevel Detailed
```

**Expected Results**:
- ✅ **TcpTestSucceeded: True**: Port 3389 is accessible
- ❌ **TcpTestSucceeded: False**: Port 3389 is not accessible

### 5. Authentication and Security Analysis

#### 5.1 Authentication Logs Analysis
**Tool**: Azure Monitor, Event Logs
**Query**:
```kusto
Event
| where TimeGenerated > ago(24h)
| where EventID in (4624, 4625, 4648)
| where Computer == "{vm_name}"
| summarize count() by EventID, Account, SourceNetworkAddress
| order by count_ desc
```

**Event IDs**:
- **4624**: Successful logon
- **4625**: Failed logon attempt
- **4648**: Logon attempt with explicit credentials

**Analysis Focus**:
- **Failed Logons**: Patterns in failed authentication attempts
- **Source IPs**: Geographic and network analysis of connection attempts
- **Account Names**: Brute force attack patterns
- **Time Patterns**: Unusual connection times or frequencies

#### 5.2 Account Status Check
**Tool**: Azure VM Run Command
**PowerShell Command**:
```powershell
Get-LocalUser | Where-Object {$_.Enabled -eq $true} | 
Select-Object Name, Enabled, LastLogon, PasswordRequired
```

**Critical Checks**:
- **Account Enabled**: User account is active
- **Password Required**: Account has password set
- **Account Lockout**: Account is not locked due to failed attempts
- **Group Membership**: User is in appropriate groups (Remote Desktop Users)

### 6. Performance and Resource Analysis

#### 6.1 System Resource Utilization
**Tool**: Azure Monitor, Performance Counters
**Query**:
```kusto
Perf
| where TimeGenerated > ago(1h)
| where Computer == "{vm_name}"
| where CounterName in ("% Processor Time", "% Committed Bytes In Use", "Available MBytes")
| summarize avg(CounterValue) by CounterName, bin(TimeGenerated, 5m)
```

**Thresholds**:
- **CPU Usage**: > 90% for extended periods
- **Memory Usage**: > 95% committed bytes
- **Available Memory**: < 100 MB

#### 6.2 Network Performance
**Tool**: Azure Monitor, Network Performance Counters
**Query**:
```kusto
Perf
| where TimeGenerated > ago(1h)
| where Computer == "{vm_name}"
| where CounterName contains "Network"
| summarize avg(CounterValue) by CounterName, bin(TimeGenerated, 5m)
```

**Metrics**:
- **Bytes Total/sec**: Network throughput
- **Packets/sec**: Packet rate
- **Current Bandwidth**: Available bandwidth

## Common Issue Patterns and Solutions

### Pattern 1: VM Stopped or Deallocated
**Symptoms**: Connection timeout, no response to ping
**Root Cause**: VM is not running
**Solution**: Start the VM using Azure portal or PowerShell
**Prevention**: Set up auto-start policies or alerts

### Pattern 2: NSG Blocking RDP
**Symptoms**: Connection timeout, port not accessible
**Root Cause**: NSG rules deny RDP access
**Solution**: Add NSG rule allowing TCP port 3389 from source IP
**Prevention**: Document and standardize NSG configurations

### Pattern 3: Windows Firewall Blocking
**Symptoms**: Connection established but immediately dropped
**Root Cause**: Windows Firewall blocks RDP traffic
**Solution**: Enable Remote Desktop firewall rule
**Prevention**: Use Group Policy to manage firewall rules

### Pattern 4: RDP Service Not Running
**Symptoms**: Connection refused, service unavailable
**Root Cause**: Terminal Services service is stopped
**Solution**: Start and enable Terminal Services service
**Prevention**: Monitor service health and set auto-start

### Pattern 5: Authentication Issues
**Symptoms**: Connection established but authentication fails
**Root Cause**: Invalid credentials, account lockout, or policy restrictions
**Solution**: Reset password, unlock account, or adjust policies
**Prevention**: Implement account lockout policies and monitoring

### Pattern 6: Network Connectivity Problems
**Symptoms**: Intermittent connectivity, high latency, packet loss
**Root Cause**: Network routing, bandwidth, or infrastructure issues
**Solution**: Optimize network configuration, increase bandwidth
**Prevention**: Monitor network performance and capacity

## Automated Resolution Procedures

### Resolution 1: Start Stopped VM
```powershell
Start-AzVM -ResourceGroupName "{resourceGroup}" -Name "{vmName}"
```

### Resolution 2: Add NSG Rule for RDP
```powershell
$nsg = Get-AzNetworkSecurityGroup -ResourceGroupName "{resourceGroup}" -Name "{nsgName}"
Add-AzNetworkSecurityRuleConfig -NetworkSecurityGroup $nsg -Name "AllowRDP" -Access Allow -Protocol Tcp -Direction Inbound -Priority 1000 -SourceAddressPrefix "*" -SourcePortRange "*" -DestinationAddressPrefix "*" -DestinationPortRange "3389"
Set-AzNetworkSecurityGroup -NetworkSecurityGroup $nsg
```

### Resolution 3: Enable RDP Firewall Rule
```powershell
Enable-NetFirewallRule -DisplayName "Remote Desktop"
```

### Resolution 4: Start RDP Service
```powershell
Start-Service -Name "TermService"
Set-Service -Name "TermService" -StartupType Automatic
```

### Resolution 5: Enable RDP in Registry
```powershell
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Terminal Server" -Name "fDenyTSConnections" -Value 0
```

## Validation and Testing

### Post-Resolution Validation
1. **Connectivity Test**: Verify RDP port accessibility
2. **Authentication Test**: Confirm successful login
3. **Performance Test**: Check system responsiveness
4. **Stability Test**: Monitor for recurring issues

### Success Criteria
- ✅ RDP connection established within 30 seconds
- ✅ Authentication successful with valid credentials
- ✅ Desktop loads completely without errors
- ✅ System performance within normal parameters
- ✅ No recurring connectivity issues for 24 hours

## Documentation and Knowledge Management

### Case Documentation
- **Issue Description**: Detailed problem statement
- **Diagnostic Results**: Complete diagnostic output
- **Root Cause Analysis**: Identified cause and contributing factors
- **Resolution Steps**: Actions taken to resolve the issue
- **Validation Results**: Confirmation of successful resolution
- **Lessons Learned**: Insights for future similar issues

### Knowledge Base Updates
- **New Patterns**: Previously unknown issue patterns
- **Solution Refinements**: Improved resolution procedures
- **Tool Enhancements**: Diagnostic tool improvements
- **Process Improvements**: Workflow optimizations

This troubleshooting playbook provides a comprehensive framework for systematically diagnosing and resolving Azure VM RDP connectivity issues while maintaining high standards of accuracy, efficiency, and customer satisfaction.
