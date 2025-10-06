# Enable RDP Bot - Test Cases

This directory contains comprehensive test cases for evaluating the Enable RDP Bot's auto-fix capabilities. Each test case creates a specific RDP connectivity problem that the bot should be able to diagnose and fix automatically.

## Test Cases Overview

| Test Case | Issue Type | Resource Group | VM Name | Key Problem |
|-----------|------------|----------------|---------|-------------|
| 1 | VM Stopped + RDP Blocked | `test1-resource-group` | `test1-vm` | VM deallocated, NSG blocks RDP |
| 2 | Conflicting NSG Rules | `test2-resource-group` | `test2-vm` | DenyRDP outranks AllowRDP |
| 3 | No RDP Rules | `test3-resource-group` | `test3-vm` | Default deny, no RDP rules |
| 4 | Wrong Port | `test4-resource-group` | `test4-vm` | RDP rule uses port 3388 instead of 3389 |
| 5 | Wrong Protocol | `test5-resource-group` | `test5-vm` | RDP rule uses UDP instead of TCP |
| 6 | Wrong Direction | `test6-resource-group` | `test6-vm` | RDP rule uses Outbound instead of Inbound |
| 7 | Restricted Source IP | `test7-resource-group` | `test7-vm` | RDP rule only allows specific IP |
| 8 | Complex NSG Conflicts | `test8-resource-group` | `test8-vm` | Multiple conflicting rules |
| 9 | Wrong Destination | `test9-resource-group` | `test9-vm` | RDP rule has specific destination IP |
| 10 | Wrong Source Port Range | `test10-resource-group` | `test10-vm` | RDP rule has restricted source ports |

## Detailed Test Cases

### Test Case 1: RDP Blocked + VM Stopped
**Files:** `create_test1.sh`, `cleanup_test1.sh`
**Resource Group:** `test1-resource-group`
**VM Name:** `test1-vm`

**Problems Created:**
- RDP port 3389 is blocked by a `DenyRDP` rule in the NSG
- VM is stopped (deallocated)

**Expected Bot Behavior:**
- Start the VM
- Add an `AllowRDP` rule with higher priority than the `DenyRDP` rule

### Test Case 2: Conflicting NSG Rules
**Files:** `create_test2.sh`, `cleanup_test2.sh`
**Resource Group:** `test2-resource-group`
**VM Name:** `test2-vm`

**Problems Created:**
- `DenyRDP` rule with priority 100 (higher precedence)
- `AllowRDP` rule with priority 200 (lower precedence)
- VM is running but RDP is effectively blocked due to rule conflict

**Expected Bot Behavior:**
- Detect the rule priority conflict
- Resolve conflicts by deleting conflicting deny rules or adjusting priorities

### Test Case 3: No RDP Rules
**Files:** `create_test3.sh`, `cleanup_test3.sh`
**Resource Group:** `test3-resource-group`
**VM Name:** `test3-vm`

**Problems Created:**
- No RDP rules exist in the NSG
- Azure NSG defaults to deny all traffic
- VM is running but RDP is blocked by default deny

**Expected Bot Behavior:**
- Detect missing RDP rules
- Create an `AllowRDP` rule to enable RDP access

### Test Case 4: Wrong Port Configuration
**Files:** `create_test4.sh`, `cleanup_test4.sh`
**Resource Group:** `test4-resource-group`
**VM Name:** `test4-vm`

**Problems Created:**
- RDP rule exists but uses port 3388 instead of 3389
- RDP traffic on correct port 3389 is blocked

**Expected Bot Behavior:**
- Detect wrong port configuration
- Update rule to use correct port 3389

### Test Case 5: Wrong Protocol Configuration
**Files:** `create_test5.sh`, `cleanup_test5.sh`
**Resource Group:** `test5-resource-group`
**VM Name:** `test5-vm`

**Problems Created:**
- RDP rule exists but uses UDP instead of TCP
- RDP traffic on TCP port 3389 is blocked

**Expected Bot Behavior:**
- Detect wrong protocol configuration
- Update rule to use TCP protocol

### Test Case 6: Wrong Direction Configuration
**Files:** `create_test6.sh`, `cleanup_test6.sh`
**Resource Group:** `test6-resource-group`
**VM Name:** `test6-vm`

**Problems Created:**
- RDP rule exists but uses Outbound instead of Inbound
- RDP traffic inbound to port 3389 is blocked

**Expected Bot Behavior:**
- Detect wrong direction configuration
- Update rule to use Inbound direction

### Test Case 7: Restricted Source IP
**Files:** `create_test7.sh`, `cleanup_test7.sh`
**Resource Group:** `test7-resource-group`
**VM Name:** `test7-vm`

**Problems Created:**
- RDP rule exists but only allows access from 192.168.1.100
- RDP traffic from other IP addresses is blocked

**Expected Bot Behavior:**
- Detect restricted source IP configuration
- Update rule to allow access from any IP (*)

### Test Case 8: Complex NSG Conflicts
**Files:** `create_test8.sh`, `cleanup_test8.sh`
**Resource Group:** `test8-resource-group`
**VM Name:** `test8-vm`

**Problems Created:**
- Multiple conflicting NSG rules with different priorities
- `DenyAllRDP` (priority 100) blocks all RDP traffic
- `AllowRDPFromOffice` (priority 200) and `AllowRDPAny` (priority 300) are blocked
- `DenyRDPFromSuspicious` (priority 150) adds complexity

**Expected Bot Behavior:**
- Detect complex rule conflicts
- Resolve conflicts and enable RDP access

### Test Case 9: Wrong Destination Configuration
**Files:** `create_test9.sh`, `cleanup_test9.sh`
**Resource Group:** `test9-resource-group`
**VM Name:** `test9-vm`

**Problems Created:**
- RDP rule exists but has destination 10.0.1.5 instead of *
- RDP traffic to the VM's actual IP is blocked

**Expected Bot Behavior:**
- Detect wrong destination configuration
- Update rule to use * for destination

### Test Case 10: Wrong Source Port Range
**Files:** `create_test10.sh`, `cleanup_test10.sh`
**Resource Group:** `test10-resource-group`
**VM Name:** `test10-vm`

**Problems Created:**
- RDP rule exists but has restricted source port range (1024-65535)
- RDP traffic from source ports 1-1023 may be blocked

**Expected Bot Behavior:**
- Detect restricted source port range
- Update rule to use * for source ports

## Usage

### Running a Single Test Case

1. **Create the test environment:**
   ```bash
   ./create_test1.sh
   ```

2. **Test the bot:**
   ```bash
   python3 enable_rdp_bot.py --rg test1-resource-group --vm test1-vm
   ```

3. **Clean up:**
   ```bash
   ./cleanup_test1.sh
   ```

### Running All Test Cases

```bash
# Create all test cases
for i in {1..10}; do ./create_test${i}.sh; done

# Test all cases with the bot
for i in {1..10}; do 
    echo "Testing Case $i..."
    python3 enable_rdp_bot.py --rg test${i}-resource-group --vm test${i}-vm
    echo "Case $i completed. Press Enter to continue..."
    read
done

# Clean up all test cases
for i in {1..10}; do ./cleanup_test${i}.sh; done
```

### Running Specific Test Cases

```bash
# Test Case 1: VM Stopped + RDP Blocked
./create_test1.sh
python3 enable_rdp_bot.py --rg test1-resource-group --vm test1-vm
./cleanup_test1.sh

# Test Case 2: Conflicting NSG Rules
./create_test2.sh
python3 enable_rdp_bot.py --rg test2-resource-group --vm test2-vm
./cleanup_test2.sh

# Test Case 3: No RDP Rules
./create_test3.sh
python3 enable_rdp_bot.py --rg test3-resource-group --vm test3-vm
./cleanup_test3.sh

# Test Case 4: Wrong Port
./create_test4.sh
python3 enable_rdp_bot.py --rg test4-resource-group --vm test4-vm
./cleanup_test4.sh

# Test Case 5: Wrong Protocol
./create_test5.sh
python3 enable_rdp_bot.py --rg test5-resource-group --vm test5-vm
./cleanup_test5.sh

# Test Case 6: Wrong Direction
./create_test6.sh
python3 enable_rdp_bot.py --rg test6-resource-group --vm test6-vm
./cleanup_test6.sh

# Test Case 7: Restricted Source IP
./create_test7.sh
python3 enable_rdp_bot.py --rg test7-resource-group --vm test7-vm
./cleanup_test7.sh

# Test Case 8: Complex NSG Conflicts
./create_test8.sh
python3 enable_rdp_bot.py --rg test8-resource-group --vm test8-vm
./cleanup_test8.sh

# Test Case 9: Wrong Destination
./create_test9.sh
python3 enable_rdp_bot.py --rg test9-resource-group --vm test9-vm
./cleanup_test9.sh

# Test Case 10: Wrong Source Port Range
./create_test10.sh
python3 enable_rdp_bot.py --rg test10-resource-group --vm test10-vm
./cleanup_test10.sh
```

## Prerequisites

- Azure CLI installed and configured
- Logged in with `az login`
- Appropriate Azure permissions to create/delete resources
- Python environment with required dependencies

## Test Case Categories

The test cases are designed to evaluate different aspects of the bot's capabilities:

### Basic Functionality
- **VM Power State Management:** Test Case 1 tests the bot's ability to start stopped VMs
- **NSG Rule Creation:** Test Case 3 tests the bot's ability to create missing rules
- **Rule Conflict Resolution:** Test Case 2 tests intelligent priority handling

### Configuration Issues
- **Port Configuration:** Test Case 4 tests detection and fixing of wrong ports
- **Protocol Configuration:** Test Case 5 tests detection and fixing of wrong protocols
- **Direction Configuration:** Test Case 6 tests detection and fixing of wrong directions

### Access Control Issues
- **Source IP Restrictions:** Test Case 7 tests detection and fixing of restricted source IPs
- **Destination Configuration:** Test Case 9 tests detection and fixing of wrong destinations
- **Source Port Restrictions:** Test Case 10 tests detection and fixing of restricted source ports

### Complex Scenarios
- **Multiple Rule Conflicts:** Test Case 8 tests resolution of complex NSG rule conflicts

The bot should successfully diagnose and auto-fix all ten scenarios, demonstrating comprehensive RDP troubleshooting capabilities across various configuration issues and edge cases.