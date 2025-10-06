"""
Main Orchestrator Agent for Azure Support Bot

This agent coordinates the entire troubleshooting process, manages conversation flow,
and routes requests to specialized diagnostic and resolution agents.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json

from semantic_kernel import Kernel
from semantic_kernel.contents import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.planners import SequentialPlanner
from azure.core.credentials import AzureCliCredential
from azure.identity.aio import DefaultAzureCredential

from ..memory.conversation_store import ConversationStore
from ..safety.guardrails import SafetyGuardrails
from .diagnostic_agent import DiagnosticAgent
from .resolution_agent import ResolutionAgent


class MainAgent:
    """Main orchestrator agent for Azure VM RDP troubleshooting."""
    
    def __init__(self, kernel: Kernel, conversation_store: ConversationStore):
        self.kernel = kernel
        self.conversation_store = conversation_store
        self.safety_guardrails = SafetyGuardrails()
        self.diagnostic_agent = DiagnosticAgent(kernel)
        self.resolution_agent = ResolutionAgent(kernel)
        
        # Initialize semantic kernel functions
        self._setup_kernel_functions()
        
        self.logger = logging.getLogger(__name__)
        
    def _setup_kernel_functions(self):
        """Setup semantic kernel functions for the main agent."""
        # Add conversation management function
        self.kernel.add_function(
            plugin_name="conversation",
            function_name="manage_context",
            function=self._manage_conversation_context
        )
        
        # Add routing function
        self.kernel.add_function(
            plugin_name="routing",
            function_name="route_to_specialist",
            function=self._route_to_specialist
        )
        
        # Add escalation function
        self.kernel.add_function(
            plugin_name="escalation",
            function_name="escalate_case",
            function=self._escalate_case
        )
    
    async def process_request(self, user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for processing user requests.
        
        Args:
            user_input: User's message or request
            user_context: User context including subscription, tenant, etc.
            
        Returns:
            Response dictionary with agent actions and results
        """
        try:
            # Safety check first
            safety_result = await self.safety_guardrails.validate_input(user_input, user_context)
            if not safety_result["safe"]:
                return {
                    "status": "blocked",
                    "reason": safety_result["reason"],
                    "message": "Request blocked for safety reasons"
                }
            
            # Get conversation history
            conversation_id = user_context.get("conversation_id")
            chat_history = await self.conversation_store.get_conversation(conversation_id)
            
            # Add user message to history
            chat_history.add_user_message(user_input)
            
            # Determine if this is a new RDP issue or continuation
            issue_type = await self._classify_issue(user_input, chat_history)
            
            # Route to appropriate specialist
            if issue_type == "rdp_troubleshooting":
                result = await self._handle_rdp_troubleshooting(user_input, user_context, chat_history)
            elif issue_type == "resolution_confirmation":
                result = await self._handle_resolution_confirmation(user_input, user_context, chat_history)
            elif issue_type == "general_support":
                result = await self._handle_general_support(user_input, user_context, chat_history)
            else:
                result = await self._handle_unknown_request(user_input, user_context, chat_history)
            
            # Save conversation state
            await self.conversation_store.save_conversation(conversation_id, chat_history)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing request: {str(e)}")
            return {
                "status": "error",
                "message": "An error occurred while processing your request. Please try again.",
                "error_details": str(e)
            }
    
    async def _classify_issue(self, user_input: str, chat_history: ChatHistory) -> str:
        """Classify the type of issue based on user input and conversation history."""
        
        classification_prompt = """
        Analyze the user's request and conversation history to classify the issue type:
        
        Options:
        - rdp_troubleshooting: User is experiencing RDP connectivity issues
        - resolution_confirmation: User is confirming or questioning a proposed resolution
        - general_support: General Azure support question not related to RDP
        - unknown_request: Cannot determine the issue type
        
        User input: {user_input}
        Recent conversation: {conversation_context}
        
        Respond with just the classification type.
        """
        
        # Get recent conversation context
        recent_messages = chat_history.messages[-6:] if len(chat_history.messages) > 6 else chat_history.messages
        conversation_context = "\n".join([f"{msg.role}: {msg.content}" for msg in recent_messages])
        
        # Use semantic kernel to classify
        classification_args = KernelArguments(
            user_input=user_input,
            conversation_context=conversation_context
        )
        
        classification_result = await self.kernel.invoke_prompt(
            prompt=classification_prompt,
            arguments=classification_args,
            execution_settings=self.kernel.get_service("openai").get_prompt_execution_settings_class()(
                max_tokens=50,
                temperature=0.1
            )
        )
        
        classification = str(classification_result).strip().lower()
        
        # Validate classification
        valid_types = ["rdp_troubleshooting", "resolution_confirmation", "general_support", "unknown_request"]
        if classification in valid_types:
            return classification
        else:
            return "unknown_request"
    
    async def _handle_rdp_troubleshooting(self, user_input: str, user_context: Dict[str, Any], 
                                        chat_history: ChatHistory) -> Dict[str, Any]:
        """Handle RDP troubleshooting requests by routing to diagnostic agent."""
        
        self.logger.info("Routing RDP troubleshooting request to diagnostic agent")
        
        # Route to diagnostic agent
        diagnostic_result = await self.diagnostic_agent.analyze_rdp_issue(
            user_input=user_input,
            user_context=user_context,
            conversation_history=chat_history
        )
        
        # Add agent response to conversation
        chat_history.add_assistant_message(diagnostic_result["message"])
        
        return {
            "status": "diagnostic_complete",
            "agent": "diagnostic",
            "message": diagnostic_result["message"],
            "diagnostics": diagnostic_result.get("diagnostics", []),
            "recommended_actions": diagnostic_result.get("recommended_actions", []),
            "requires_resolution": diagnostic_result.get("requires_resolution", False),
            "escalation_needed": diagnostic_result.get("escalation_needed", False)
        }
    
    async def _handle_resolution_confirmation(self, user_input: str, user_context: Dict[str, Any],
                                            chat_history: ChatHistory) -> Dict[str, Any]:
        """Handle resolution confirmation requests by routing to resolution agent."""
        
        self.logger.info("Routing resolution confirmation to resolution agent")
        
        # Route to resolution agent
        resolution_result = await self.resolution_agent.execute_resolution(
            user_input=user_input,
            user_context=user_context,
            conversation_history=chat_history
        )
        
        # Add agent response to conversation
        chat_history.add_assistant_message(resolution_result["message"])
        
        return {
            "status": "resolution_complete",
            "agent": "resolution",
            "message": resolution_result["message"],
            "actions_taken": resolution_result.get("actions_taken", []),
            "verification_results": resolution_result.get("verification_results", []),
            "success": resolution_result.get("success", False)
        }
    
    async def _handle_general_support(self, user_input: str, user_context: Dict[str, Any],
                                    chat_history: ChatHistory) -> Dict[str, Any]:
        """Handle general support requests."""
        
        general_response = await self._provide_general_support(user_input, user_context)
        chat_history.add_assistant_message(general_response["message"])
        
        return {
            "status": "general_support",
            "message": general_response["message"],
            "suggestions": general_response.get("suggestions", [])
        }
    
    async def _handle_unknown_request(self, user_input: str, user_context: Dict[str, Any],
                                    chat_history: ChatHistory) -> Dict[str, Any]:
        """Handle requests that couldn't be classified."""
        
        clarification_message = """
        I'm not sure how to help with your request. Could you please provide more details about:
        
        1. What specific issue are you experiencing?
        2. What error messages are you seeing?
        3. What were you trying to do when the problem occurred?
        
        If you're having trouble connecting to your Windows VM via RDP, I can help troubleshoot that specifically.
        """
        
        chat_history.add_assistant_message(clarification_message)
        
        return {
            "status": "clarification_needed",
            "message": clarification_message
        }
    
    async def _provide_general_support(self, user_input: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide general Azure support information."""
        
        support_prompt = """
        Provide helpful general Azure support information for the user's request.
        Keep it concise and actionable.
        
        User request: {user_input}
        """
        
        args = KernelArguments(user_input=user_input)
        result = await self.kernel.invoke_prompt(
            prompt=support_prompt,
            arguments=args
        )
        
        return {
            "message": str(result),
            "suggestions": [
                "Check Azure Service Health for known issues",
                "Review Azure documentation for your service",
                "Contact Azure Support for complex issues"
            ]
        }
    
    async def _manage_conversation_context(self, **kwargs) -> str:
        """Manage conversation context and history."""
        # Implementation for context management
        return "Context managed successfully"
    
    async def _route_to_specialist(self, **kwargs) -> str:
        """Route requests to appropriate specialist agents."""
        # Implementation for routing logic
        return "Request routed to specialist"
    
    async def _escalate_case(self, **kwargs) -> str:
        """Escalate case to human support."""
        # Implementation for escalation
        return "Case escalated to human support"
