#!/usr/bin/env python3
"""
Simplified Azure Agentic AI Support Bot
Demonstrates core functionality without Semantic Kernel dependencies
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import openai
from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.core.exceptions import AzureError

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

class AzureVMInspector:
    """Handles Azure VM diagnostics and operations"""
    
    def __init__(self, subscription_id: str):
        self.subscription_id = subscription_id
        self.credential = DefaultAzureCredential()
        self.compute_client = ComputeManagementClient(
            self.credential, subscription_id
        )
        self.network_client = NetworkManagementClient(
            self.credential, subscription_id
        )
        self.resource_client = ResourceManagementClient(
            self.credential, subscription_id
        )
        self.monitor_client = MonitorManagementClient(
            self.credential, subscription_id
        )

    async def check_vm_status(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check if VM is running"""
        try:
            vm = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.compute_client.virtual_machines.get(
                    resource_group, vm_name
                )
            )
            
            status = vm.instance_view.statuses[0].display_status if vm.instance_view.statuses else "Unknown"
            
            if "running" in status.lower():
                return DiagnosticResult(
                    check_name="VM Status",
                    status="pass",
                    message=f"VM is running: {status}",
                    details={"vm_status": status, "vm_id": vm.id}
                )
            else:
                return DiagnosticResult(
                    check_name="VM Status",
                    status="fail",
                    message=f"VM is not running: {status}",
                    details={"vm_status": status, "vm_id": vm.id}
                )
                
        except AzureError as e:
            return DiagnosticResult(
                check_name="VM Status",
                status="fail",
                message=f"Failed to check VM status: {str(e)}"
            )

    async def check_rdp_port(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check if RDP port 3389 is open"""
        try:
            # Get VM network interfaces
            vm = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.compute_client.virtual_machines.get(
                    resource_group, vm_name
                )
            )
            
            if not vm.network_profile.network_interfaces:
                return DiagnosticResult(
                    check_name="RDP Port",
                    status="fail",
                    message="No network interfaces found"
                )
            
            # Get the first NIC
            nic_name = vm.network_profile.network_interfaces[0].id.split('/')[-1]
            nic = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.network_client.network_interfaces.get(
                    resource_group, nic_name
                )
            )
            
            # Check NSG rules
            if nic.network_security_group:
                nsg_name = nic.network_security_group.id.split('/')[-1]
                nsg = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: self.network_client.network_security_groups.get(
                        resource_group, nsg_name
                    )
                )
                
                rdp_rule_found = False
                for rule in nsg.security_rules:
                    if (rule.destination_port_range == "3389" or 
                        (rule.destination_port_ranges and "3389" in rule.destination_port_ranges)):
                        if rule.access.lower() == "allow" and rule.direction.lower() == "inbound":
                            rdp_rule_found = True
                            break
                
                if rdp_rule_found:
                    return DiagnosticResult(
                        check_name="RDP Port",
                        status="pass",
                        message="RDP port 3389 is allowed in NSG",
                        details={"nsg_name": nsg_name}
                    )
                else:
                    return DiagnosticResult(
                        check_name="RDP Port",
                        status="fail",
                        message="RDP port 3389 is not allowed in NSG",
                        details={"nsg_name": nsg_name}
                    )
            else:
                return DiagnosticResult(
                    check_name="RDP Port",
                    status="warning",
                    message="No Network Security Group associated with VM"
                )
                
        except AzureError as e:
            return DiagnosticResult(
                check_name="RDP Port",
                status="fail",
                message=f"Failed to check RDP port: {str(e)}"
            )

    async def check_vm_connectivity(self, vm_name: str, resource_group: str) -> DiagnosticResult:
        """Check basic VM connectivity"""
        try:
            # Get VM public IP if available
            vm = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.compute_client.virtual_machines.get(
                    resource_group, vm_name
                )
            )
            
            # This is a simplified check - in reality you'd use Network Watcher
            # or other connectivity testing tools
            return DiagnosticResult(
                check_name="VM Connectivity",
                status="pass",
                message="VM connectivity check completed (simplified)",
                details={"vm_id": vm.id}
            )
            
        except AzureError as e:
            return DiagnosticResult(
                check_name="VM Connectivity",
                status="fail",
                message=f"Failed to check VM connectivity: {str(e)}"
            )

class AIAgent:
    """AI Agent for troubleshooting guidance"""
    
    def __init__(self, openai_api_key: str):
        self.client = openai.OpenAI(api_key=openai_api_key)
    
    async def analyze_diagnostics(self, diagnostics: List[DiagnosticResult]) -> str:
        """Analyze diagnostic results and provide recommendations"""
        
        diagnostic_summary = "\n".join([
            f"- {d.check_name}: {d.status.upper()} - {d.message}"
            for d in diagnostics
        ])
        
        prompt = f"""
        You are an Azure support specialist. Analyze these VM RDP connectivity diagnostics and provide specific recommendations:
        
        Diagnostic Results:
        {diagnostic_summary}
        
        Provide:
        1. Root cause analysis
        2. Specific remediation steps
        3. Prevention recommendations
        
        Keep response concise and actionable.
        """
        
        try:
            response = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Analysis unavailable due to API error: {str(e)}"

class AzureSupportBot:
    """Main Azure Support Bot orchestrator"""
    
    def __init__(self, subscription_id: str, openai_api_key: str):
        self.subscription_id = subscription_id
        self.inspector = AzureVMInspector(subscription_id)
        self.ai_agent = AIAgent(openai_api_key)
        self.active_sessions: Dict[str, TroubleshootingSession] = {}
    
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

async def main():
    """Demo function"""
    # Configuration
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID", "your-subscription-id")
    openai_api_key = os.getenv("OPENAI_API_KEY", "your-openai-key")
    
    if subscription_id == "your-subscription-id" or openai_api_key == "your-openai-key":
        print("Please set AZURE_SUBSCRIPTION_ID and OPENAI_API_KEY environment variables")
        return
    
    # Initialize bot
    bot = AzureSupportBot(subscription_id, openai_api_key)
    
    # Demo troubleshooting
    vm_name = "demo-vm"
    resource_group = "demo-rg"
    
    print(f"Starting troubleshooting for VM: {vm_name}")
    session_id = await bot.start_troubleshooting(vm_name, resource_group)
    
    # Get results
    results = bot.get_session_results(session_id)
    if results:
        print("\n=== TROUBLESHOOTING RESULTS ===")
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
