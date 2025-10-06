# Enable RDP Bot - Test Cases

This directory contains test cases for evaluating the Enable RDP Bot's auto-fix capabilities. Each test case creates a specific RDP connectivity problem that the bot should be able to diagnose and fix automatically.

## Test Cases

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
- Adjust `AllowRDP` priority to be higher precedence than `DenyRDP`

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

## Usage

### Running a Test Case

1. **Create the test environment:**
   ```bash
   ./evals/create_test1.sh
   ```

2. **Test the bot:**
   ```bash
   python enable_rdp_bot.py --rg test1-resource-group --vm test1-vm
   ```

3. **Clean up:**
   ```bash
   ./evals/cleanup_test1.sh
   ```

### Running All Test Cases

```bash
# Test Case 1
./evals/create_test1.sh
python enable_rdp_bot.py --rg test1-resource-group --vm test1-vm
./evals/cleanup_test1.sh

# Test Case 2
./evals/create_test2.sh
python enable_rdp_bot.py --rg test2-resource-group --vm test2-vm
./evals/cleanup_test2.sh

# Test Case 3
./evals/create_test3.sh
python enable_rdp_bot.py --rg test3-resource-group --vm test3-vm
./evals/cleanup_test3.sh
```

## Prerequisites

- Azure CLI installed and configured
- Logged in with `az login`
- Appropriate Azure permissions to create/delete resources
- Python environment with required dependencies

## Test Case Details

Each test case is designed to evaluate different aspects of the bot's capabilities:

- **VM Power State Management:** Test Case 1 tests the bot's ability to start stopped VMs
- **NSG Rule Conflict Resolution:** Test Case 2 tests intelligent priority handling
- **Rule Creation:** Test Case 3 tests the bot's ability to create missing rules

The bot should successfully diagnose and auto-fix all three scenarios, demonstrating comprehensive RDP troubleshooting capabilities.
