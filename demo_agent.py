#!/usr/bin/env python3
"""
Azure Agentic AI Support Bot - Demo Version
Demonstrates the solution architecture and functionality without requiring Azure credentials
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class DiagnosticResult:
    """Result of a diagnostic check"""
    check_name: str
    status: str  # "pass", "fail", "warning"
    message: str
    details: Optional[Dict[str, Any]] = None

@dataclass
class TroubleshootingSession:
    """Represents a troubleshooting session"""
    session_id: str
    vm_name: str
    resource_group: str
    start_time: datetime
    status: str = "active"
    diagnostics: List[DiagnosticResult] = None
    resolution: Optional[str] = None
    
    def __post_init__(self):
        if self.diagnostics is None:
            self.diagnostics = []

class MockAzureVMInspector:
    """Mock Azure VM inspector for demo purposes"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        logger.info(f"Initialized Azure VM Inspector for subscription: {subscription_id}")

    async def check_vm_status(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check if VM is running (mock)"""
        await asyncio.sleep(1)  # Simulate API call
        
        # Simulate different scenarios
        if "stopped" in vm_name.lower():
            return DiagnosticResult(
                check_name="VM Status",
                status="fail",
                message="VM is stopped - not responding to RDP",
                details={
                    "vm_status": "VM deallocated",
                    "power_state": "stopped",
                    "vm_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}"
                }
            )
        else:
            return DiagnosticResult(
                check_name="VM Status",
                status="pass",
                message="VM is running and healthy",
                details={
                    "vm_status": "VM running",
                    "power_state": "running",
                    "vm_id": f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Compute/virtualMachines/{vm_name}"
                }
            )

    async def check_rdp_port(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check if RDP port 3389 is open (mock)"""
        await asyncio.sleep(1)  # Simulate API call
        
        # Simulate NSG check
        if "blocked" in vm_name.lower():
            return DiagnosticResult(
                check_name="RDP Port",
                status="fail",
                message="RDP port 3389 is blocked by Network Security Group",
                details={
                    "nsg_name": "default-nsg",
                    "blocking_rule": "DenyAllInbound",
                    "port": 3389,
                    "protocol": "TCP"
                }
            )
        else:
            return DiagnosticResult(
                check_name="RDP Port",
                status="pass",
                message="RDP port 3389 is allowed in Network Security Group",
                details={
                    "nsg_name": "default-nsg",
                    "allowing_rule": "AllowRDP",
                    "port": 3389,
                    "protocol": "TCP"
                }
            )

    async def check_vm_connectivity(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check basic VM connectivity (mock)"""
        await asyncio.sleep(1)  # Simulate API call
        
        if "network" in vm_name.lower():
            return DiagnosticResult(
                check_name="VM Connectivity",
                status="fail",
                message="Network connectivity issues detected",
                details={
                    "connectivity_test": "failed",
                    "ping_test": "timeout",
                    "dns_resolution": "failed"
                }
            )
        else:
            return DiagnosticResult(
                check_name="VM Connectivity",
                status="pass",
                message="VM network connectivity is working",
                details={
                    "connectivity_test": "passed",
                    "ping_test": "successful",
                    "dns_resolution": "working"
                }
            )

class MockAIAgent:
    """Mock AI Agent for demo purposes"""
    
    def __init__(self, openai_api_key: str):
        self.api_key = openai_api_key
        logger.info("Initialized AI Agent with OpenAI API")

    async def analyze_diagnostics(self, diagnostics: List[DiagnosticResult]) -> str:
        """Analyze diagnostic results and provide recommendations (mock)"""
        await asyncio.sleep(2)  # Simulate AI processing
        
        failed_checks = [d for d in diagnostics if d.status == "fail"]
        warning_checks = [d for d in diagnostics if d.status == "warning"]
        
        if not failed_checks:
            return """✅ **Root Cause Analysis**: No critical issues found.

🔧 **Recommendations**:
1. VM is running normally
2. RDP port is properly configured
3. Network connectivity is working

💡 **Prevention**:
- Monitor VM health regularly
- Set up automated backups
- Configure alerting for VM status changes"""
        
        analysis = "🔍 **Root Cause Analysis**:\n"
        
        if any("VM Status" in d.check_name for d in failed_checks):
            analysis += "- VM is not running or has stopped unexpectedly\n"
        
        if any("RDP Port" in d.check_name for d in failed_checks):
            analysis += "- RDP port 3389 is blocked by Network Security Group\n"
        
        if any("VM Connectivity" in d.check_name for d in failed_checks):
            analysis += "- Network connectivity issues detected\n"
        
        analysis += "\n🔧 **Remediation Steps**:\n"
        
        if any("VM Status" in d.check_name for d in failed_checks):
            analysis += "1. Start the VM using Azure Portal or Azure CLI\n"
            analysis += "2. Check VM boot diagnostics for startup issues\n"
        
        if any("RDP Port" in d.check_name for d in failed_checks):
            analysis += "1. Update Network Security Group to allow RDP (port 3389)\n"
            analysis += "2. Verify firewall rules on the VM\n"
        
        if any("VM Connectivity" in d.check_name for d in failed_checks):
            analysis += "1. Check network interface configuration\n"
            analysis += "2. Verify DNS settings and routing tables\n"
        
        analysis += "\n💡 **Prevention Recommendations**:\n"
        analysis += "- Set up automated monitoring and alerting\n"
        analysis += "- Configure VM auto-shutdown schedules\n"
        analysis += "- Implement network security best practices\n"
        analysis += "- Regular security group reviews"
        
        return analysis

class AzureSupportBot:
    """Main Azure Support Bot orchestrator (Demo Version)"""
    
    def __init__(self, subscription_id: str, openai_api_key: str):
        self.subscription_id = subscription_id
        self.inspector = MockAzureVMInspector(subscription_id)
        self.ai_agent = MockAIAgent(openai_api_key)
        self.active_sessions: Dict[str, TroubleshootingSession] = {}
        logger.info("Azure Support Bot initialized")
    
    async def start_troubleshooting(self, vm_name: str, resource_group: str) -> str:
        """Start a new troubleshooting session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = TroubleshootingSession(
            session_id=session_id,
            vm_name=vm_name,
            resource_group=resource_group,
            start_time=datetime.now()
        )
        
        self.active_sessions[session_id] = session
        
        logger.info(f"Started troubleshooting session {session_id} for VM {vm_name}")
        
        # Run diagnostics
        await self._run_diagnostics(session)
        
        # Get AI analysis
        if session.diagnostics:
            session.resolution = await self.ai_agent.analyze_diagnostics(session.diagnostics)
        
        session.status = "completed"
        
        return session_id
    
    async def _run_diagnostics(self, session: TroubleshootingSession):
        """Run all diagnostic checks"""
        logger.info(f"Running diagnostics for session {session.session_id}")
        
        # Run diagnostic checks
        checks = [
            self.inspector.check_vm_status(session.vm_name, session.resource_group),
            self.inspector.check_rdp_port(session.vm_name, session.resource_group),
            self.inspector.check_vm_connectivity(session.vm_name, session.resource_group)
        ]
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, DiagnosticResult):
                session.diagnostics.append(result)
            elif isinstance(result, Exception):
                session.diagnostics.append(DiagnosticResult(
                    check_name="System Error",
                    status="fail",
                    message=f"Diagnostic failed: {str(result)}"
                ))
    
    def get_session_results(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get troubleshooting session results"""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session.session_id,
            "vm_name": session.vm_name,
            "resource_group": session.resource_group,
            "start_time": session.start_time.isoformat(),
            "status": session.status,
            "diagnostics": [
                {
                    "check_name": d.check_name,
                    "status": d.status,
                    "message": d.message,
                    "details": d.details
                }
                for d in session.diagnostics
            ],
            "resolution": session.resolution
        }

async def demo_scenarios():
    """Demonstrate different troubleshooting scenarios"""
    
    # Initialize bot with demo credentials
    bot = AzureSupportBot("demo-subscription-123", "demo-openai-key")
    
    scenarios = [
        {
            "name": "Healthy VM",
            "vm_name": "healthy-vm-01",
            "resource_group": "production-rg",
            "description": "A normally functioning VM with RDP working"
        },
        {
            "name": "Stopped VM",
            "vm_name": "stopped-vm-02", 
            "resource_group": "development-rg",
            "description": "A VM that has been stopped/deallocated"
        },
        {
            "name": "Blocked RDP",
            "vm_name": "blocked-vm-03",
            "resource_group": "test-rg", 
            "description": "A running VM with RDP blocked by NSG"
        },
        {
            "name": "Network Issues",
            "vm_name": "network-vm-04",
            "resource_group": "staging-rg",
            "description": "A VM with network connectivity problems"
        }
    ]
    
    print("🤖 Azure Agentic AI Support Bot - Demo Scenarios")
    print("=" * 60)
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n📋 Scenario {i}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   VM: {scenario['vm_name']}")
        print(f"   Resource Group: {scenario['resource_group']}")
        print("-" * 40)
        
        # Start troubleshooting
        session_id = await bot.start_troubleshooting(
            scenario['vm_name'], 
            scenario['resource_group']
        )
        
        # Get and display results
        results = bot.get_session_results(session_id)
        if results:
            print(f"✅ Session {session_id} completed")
            
            # Show diagnostic results
            print("\n🔍 Diagnostic Results:")
            for diagnostic in results['diagnostics']:
                status_emoji = "✅" if diagnostic['status'] == "pass" else "❌" if diagnostic['status'] == "fail" else "⚠️"
                print(f"   {status_emoji} {diagnostic['check_name']}: {diagnostic['message']}")
            
            # Show AI analysis
            if results['resolution']:
                print(f"\n🤖 AI Analysis:\n{results['resolution']}")
        
        print("\n" + "=" * 60)
        
        # Pause between scenarios
        if i < len(scenarios):
            await asyncio.sleep(1)

async def main():
    """Main demo function"""
    print("🚀 Starting Azure Agentic AI Support Bot Demo")
    print("This demo shows the solution architecture and capabilities")
    print("without requiring real Azure credentials.\n")
    
    await demo_scenarios()
    
    print("\n🎉 Demo completed!")
    print("\n📚 Key Features Demonstrated:")
    print("✅ Multi-step diagnostic workflow")
    print("✅ Azure VM status checking")
    print("✅ Network Security Group analysis")
    print("✅ AI-powered root cause analysis")
    print("✅ Automated remediation recommendations")
    print("✅ Session management and tracking")
    
    print("\n🏗️  Architecture Components:")
    print("• Azure VM Inspector - Handles Azure API calls")
    print("• AI Agent - Provides intelligent analysis")
    print("• Support Bot Orchestrator - Manages the workflow")
    print("• Diagnostic Engine - Runs automated checks")
    print("• Session Management - Tracks troubleshooting sessions")

if __name__ == "__main__":
    asyncio.run(main())
