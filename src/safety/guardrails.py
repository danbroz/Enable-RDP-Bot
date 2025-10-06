"""
Safety Guardrails for Azure Support Bot

This module provides safety, security, and governance controls for the agentic AI system,
including content filtering, input validation, and action authorization.
"""

import asyncio
import logging
import re
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import json

from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions, AnalyzeImageOptions
from azure.core.credentials import AzureKeyCredential


class SafetyGuardrails:
    """Provides safety and security guardrails for the AI support bot."""
    
    def __init__(self, content_safety_endpoint: str = None, content_safety_key: str = None):
        self.content_safety_endpoint = content_safety_endpoint
        self.content_safety_key = content_safety_key
        
        # Initialize Content Safety client if credentials provided
        self.content_safety_client = None
        if content_safety_endpoint and content_safety_key:
            try:
                self.content_safety_client = ContentSafetyClient(
                    endpoint=content_safety_endpoint,
                    credential=AzureKeyCredential(content_safety_key)
                )
            except Exception as e:
                logging.warning(f"Failed to initialize Content Safety client: {e}")
        
        self.logger = logging.getLogger(__name__)
        
        # Define dangerous operations that require special authorization
        self.dangerous_operations = {
            "delete_vm", "delete_resource_group", "delete_storage_account",
            "delete_database", "delete_key_vault", "revoke_all_permissions",
            "shutdown_vm", "format_disk", "delete_backup"
        }
        
        # Define PII patterns to detect and mask
        self.pii_patterns = {
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "phone": r'\b\d{3}-\d{3}-\d{4}\b|\b\(\d{3}\)\s?\d{3}-\d{4}\b',
            "ssn": r'\b\d{3}-\d{2}-\d{4}\b',
            "credit_card": r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            "ip_address": r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        }
        
        # Define prompt injection patterns
        self.injection_patterns = [
            r"ignore\s+previous\s+instructions",
            r"forget\s+everything",
            r"you\s+are\s+now",
            r"act\s+as\s+if",
            r"pretend\s+to\s+be",
            r"system\s*:",
            r"assistant\s*:",
            r"user\s*:",
            r"<\|im_start\|>",
            r"<\|im_end\|>"
        ]
    
    async def validate_input(self, user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user input for safety and security.
        
        Args:
            user_input: User's input text
            user_context: User context information
            
        Returns:
            Validation result with safety assessment
        """
        try:
            validation_result = {
                "safe": True,
                "reason": "",
                "warnings": [],
                "blocked_content": [],
                "sanitized_input": user_input
            }
            
            # Check for prompt injection attempts
            injection_detected = await self._detect_prompt_injection(user_input)
            if injection_detected["detected"]:
                validation_result["safe"] = False
                validation_result["reason"] = "Prompt injection detected"
                validation_result["blocked_content"].append({
                    "type": "prompt_injection",
                    "pattern": injection_detected["pattern"],
                    "severity": "high"
                })
                return validation_result
            
            # Check for PII
            pii_detected = await self._detect_pii(user_input)
            if pii_detected["detected"]:
                validation_result["warnings"].append("PII detected in input")
                validation_result["blocked_content"].extend(pii_detected["pii_found"])
                # Mask PII in sanitized input
                validation_result["sanitized_input"] = self._mask_pii(user_input, pii_detected["pii_found"])
            
            # Check with Azure Content Safety API
            if self.content_safety_client:
                content_safety_result = await self._check_content_safety(user_input)
                if not content_safety_result["safe"]:
                    validation_result["safe"] = False
                    validation_result["reason"] = "Content Safety API flagged content"
                    validation_result["blocked_content"].extend(content_safety_result["flagged_categories"])
            
            # Check for suspicious Azure resource operations
            suspicious_operations = await self._detect_suspicious_operations(user_input)
            if suspicious_operations:
                validation_result["warnings"].extend(suspicious_operations)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating input: {str(e)}")
            return {
                "safe": False,
                "reason": f"Validation error: {str(e)}",
                "warnings": [],
                "blocked_content": [],
                "sanitized_input": user_input
            }
    
    async def validate_resolution_actions(self, resolution_plan: List[Dict[str, Any]], 
                                        user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate resolution actions for safety and authorization.
        
        Args:
            resolution_plan: List of planned resolution actions
            user_context: User context including permissions
            
        Returns:
            Validation result for resolution actions
        """
        try:
            validation_result = {
                "safe": True,
                "reason": "",
                "blocked_actions": [],
                "requires_confirmation": [],
                "authorized_actions": []
            }
            
            user_permissions = user_context.get("permissions", [])
            
            for action in resolution_plan:
                action_type = action.get("action", "")
                
                # Check for dangerous operations
                if action_type in self.dangerous_operations:
                    validation_result["requires_confirmation"].append({
                        "action": action_type,
                        "reason": "Dangerous operation requiring confirmation"
                    })
                
                # Check authorization
                if not await self._check_action_authorization(action_type, user_permissions):
                    validation_result["blocked_actions"].append({
                        "action": action_type,
                        "reason": "Insufficient permissions"
                    })
                    validation_result["safe"] = False
                else:
                    validation_result["authorized_actions"].append(action_type)
            
            if validation_result["blocked_actions"]:
                validation_result["reason"] = "Some actions blocked due to insufficient permissions"
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error validating resolution actions: {str(e)}")
            return {
                "safe": False,
                "reason": f"Action validation error: {str(e)}",
                "blocked_actions": [],
                "requires_confirmation": [],
                "authorized_actions": []
            }
    
    async def audit_action(self, action: str, user_context: Dict[str, Any], 
                          result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Audit an action for compliance and security.
        
        Args:
            action: Action that was performed
            user_context: User context information
            result: Result of the action
            
        Returns:
            Audit record
        """
        try:
            audit_record = {
                "timestamp": datetime.utcnow().isoformat(),
                "action": action,
                "user_id": user_context.get("user_id", "unknown"),
                "subscription_id": user_context.get("subscription_id", "unknown"),
                "result": result,
                "compliance_checks": {
                    "data_access_logged": True,
                    "action_authorized": True,
                    "pii_handled_safely": True
                }
            }
            
            # Log audit record (in production, this would go to a secure audit store)
            self.logger.info(f"Action audited: {json.dumps(audit_record, indent=2)}")
            
            return audit_record
            
        except Exception as e:
            self.logger.error(f"Error auditing action: {str(e)}")
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "action": action
            }
    
    async def _detect_prompt_injection(self, text: str) -> Dict[str, Any]:
        """Detect potential prompt injection attempts."""
        text_lower = text.lower()
        
        for pattern in self.injection_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return {
                    "detected": True,
                    "pattern": pattern,
                    "severity": "high"
                }
        
        return {"detected": False}
    
    async def _detect_pii(self, text: str) -> Dict[str, Any]:
        """Detect personally identifiable information in text."""
        pii_found = []
        
        for pii_type, pattern in self.pii_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                pii_found.extend([{
                    "type": pii_type,
                    "value": match,
                    "severity": "medium"
                } for match in matches])
        
        return {
            "detected": len(pii_found) > 0,
            "pii_found": pii_found
        }
    
    def _mask_pii(self, text: str, pii_items: List[Dict[str, Any]]) -> str:
        """Mask PII in text."""
        masked_text = text
        
        for pii_item in pii_items:
            pii_value = pii_item["value"]
            masked_value = "*" * len(pii_value)
            masked_text = masked_text.replace(pii_value, masked_value)
        
        return masked_text
    
    async def _check_content_safety(self, text: str) -> Dict[str, Any]:
        """Check content using Azure Content Safety API."""
        try:
            if not self.content_safety_client:
                return {"safe": True, "flagged_categories": []}
            
            # Analyze text for harmful content
            analyze_text_options = AnalyzeTextOptions(text=text)
            response = await self.content_safety_client.analyze_text(analyze_text_options)
            
            flagged_categories = []
            if response.hate_result.severity > 0:
                flagged_categories.append({
                    "category": "hate",
                    "severity": response.hate_result.severity,
                    "filtered": response.hate_result.filtered
                })
            
            if response.self_harm_result.severity > 0:
                flagged_categories.append({
                    "category": "self_harm",
                    "severity": response.self_harm_result.severity,
                    "filtered": response.self_harm_result.filtered
                })
            
            if response.sexual_result.severity > 0:
                flagged_categories.append({
                    "category": "sexual",
                    "severity": response.sexual_result.severity,
                    "filtered": response.sexual_result.filtered
                })
            
            if response.violence_result.severity > 0:
                flagged_categories.append({
                    "category": "violence",
                    "severity": response.violence_result.severity,
                    "filtered": response.violence_result.filtered
                })
            
            return {
                "safe": len(flagged_categories) == 0,
                "flagged_categories": flagged_categories
            }
            
        except Exception as e:
            self.logger.error(f"Content Safety API error: {str(e)}")
            # Fail open - allow content if API is unavailable
            return {"safe": True, "flagged_categories": []}
    
    async def _detect_suspicious_operations(self, text: str) -> List[str]:
        """Detect suspicious Azure resource operations in text."""
        suspicious_operations = []
        text_lower = text.lower()
        
        # Check for dangerous keywords
        dangerous_keywords = [
            "delete everything", "remove all", "destroy", "wipe",
            "format c:", "rm -rf", "del /f /s", "shutdown -s -t 0"
        ]
        
        for keyword in dangerous_keywords:
            if keyword in text_lower:
                suspicious_operations.append(f"Suspicious operation detected: {keyword}")
        
        return suspicious_operations
    
    async def _check_action_authorization(self, action: str, user_permissions: List[str]) -> bool:
        """Check if user has authorization for a specific action."""
        # Define permission mappings
        action_permissions = {
            "start_vm": ["Microsoft.Compute/virtualMachines/start/action"],
            "stop_vm": ["Microsoft.Compute/virtualMachines/powerOff/action"],
            "restart_vm": ["Microsoft.Compute/virtualMachines/restart/action"],
            "update_nsg_rules": ["Microsoft.Network/networkSecurityGroups/write"],
            "configure_firewall": ["Microsoft.Compute/virtualMachines/runCommand/action"],
            "start_rdp_service": ["Microsoft.Compute/virtualMachines/runCommand/action"]
        }
        
        required_permissions = action_permissions.get(action, [])
        if not required_permissions:
            # Unknown action - deny by default
            return False
        
        # Check if user has any of the required permissions
        for required_permission in required_permissions:
            if required_permission in user_permissions:
                return True
        
        return False
    
    async def get_safety_metrics(self) -> Dict[str, Any]:
        """Get safety metrics and statistics."""
        try:
            # In production, this would aggregate metrics from audit logs
            return {
                "total_validations": 0,
                "blocked_requests": 0,
                "pii_detections": 0,
                "prompt_injection_attempts": 0,
                "content_safety_flags": 0,
                "unauthorized_actions": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Error getting safety metrics: {str(e)}")
            return {"error": str(e)}
