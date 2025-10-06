"""
Azure Bot Service Integration

This module provides the main bot service implementation for the Azure Agentic AI Support Bot,
handling user interactions, authentication, and integration with the agent system.
"""

import asyncio
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from botbuilder.core import ActivityHandler, MessageFactory, TurnContext
from botbuilder.core.conversation_state import ConversationState
from botbuilder.core.user_state import UserState
from botbuilder.schema import ChannelAccount, Activity, ActivityTypes
from botbuilder.core.teams import TeamsActivityHandler
from azure.identity.aio import DefaultAzureCredential
from azure.core.credentials import AccessToken

from ..agents.main_agent import MainAgent
from ..memory.conversation_store import ConversationStore
from ..safety.guardrails import SafetyGuardrails
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletionService


class AzureSupportBot(ActivityHandler):
    """Main bot implementation for Azure VM RDP troubleshooting support."""
    
    def __init__(self, conversation_state: ConversationState, user_state: UserState,
                 kernel: Kernel, conversation_store: ConversationStore):
        super().__init__()
        
        self.conversation_state = conversation_state
        self.user_state = user_state
        self.kernel = kernel
        self.conversation_store = conversation_store
        self.safety_guardrails = SafetyGuardrails()
        
        # Initialize the main agent
        self.main_agent = MainAgent(kernel, conversation_store)
        
        # Bot state accessors
        self.conversation_state_accessor = conversation_state.create_property("ConversationData")
        self.user_state_accessor = user_state.create_property("UserData")
        
        self.logger = logging.getLogger(__name__)
        
        # Azure credential for authentication
        self.credential = DefaultAzureCredential()
    
    async def on_members_added_activity(
        self, members_added: list[ChannelAccount], turn_context: TurnContext
    ):
        """Handle new members added to the conversation."""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                welcome_message = MessageFactory.text(
                    "Welcome to the Azure VM RDP Troubleshooting Assistant! "
                    "I'm here to help you diagnose and resolve RDP connectivity issues with your Windows VMs. "
                    "Please describe your RDP problem, and I'll guide you through the troubleshooting process."
                )
                await turn_context.send_activity(welcome_message)
    
    async def on_message_activity(self, turn_context: TurnContext):
        """Handle incoming messages from users."""
        try:
            # Get user input
            user_input = turn_context.activity.text.strip()
            
            if not user_input:
                await turn_context.send_activity("Please provide a description of your RDP connectivity issue.")
                return
            
            # Get conversation data
            conversation_data = await self.conversation_state_accessor.get(
                turn_context, lambda: {}
            )
            
            # Get or create conversation ID
            conversation_id = conversation_data.get("conversation_id")
            if not conversation_id:
                conversation_id = str(uuid.uuid4())
                conversation_data["conversation_id"] = conversation_id
                conversation_data["start_time"] = datetime.utcnow().isoformat()
            
            # Get user data
            user_data = await self.user_state_accessor.get(turn_context, lambda: {})
            
            # Authenticate user and get context
            user_context = await self._authenticate_user(turn_context, user_data)
            if not user_context:
                await turn_context.send_activity(
                    "I need to authenticate you to access your Azure resources. "
                    "Please sign in using your Azure credentials."
                )
                return
            
            # Add conversation context
            user_context["conversation_id"] = conversation_id
            user_context["user_id"] = turn_context.activity.from_property.id
            user_context["channel_id"] = turn_context.activity.channel_id
            
            # Show typing indicator
            await turn_context.send_activity({
                "type": "typing"
            })
            
            # Process the request through the main agent
            response = await self.main_agent.process_request(user_input, user_context)
            
            # Send response to user
            await self._send_response(turn_context, response)
            
            # Save conversation state
            conversation_data["last_activity"] = datetime.utcnow().isoformat()
            conversation_data["message_count"] = conversation_data.get("message_count", 0) + 1
            
            await self.conversation_state.save_changes(turn_context)
            await self.user_state.save_changes(turn_context)
            
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            await turn_context.send_activity(
                "I encountered an error while processing your request. "
                "Please try again or contact support if the issue persists."
            )
    
    async def _authenticate_user(self, turn_context: TurnContext, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Authenticate user and retrieve Azure context."""
        try:
            # Check if user is already authenticated
            if user_data.get("authenticated") and user_data.get("access_token"):
                # Validate existing token
                token_expiry = datetime.fromisoformat(user_data["token_expiry"])
                if token_expiry > datetime.utcnow():
                    return {
                        "subscription_id": user_data["subscription_id"],
                        "tenant_id": user_data["tenant_id"],
                        "user_id": user_data["user_id"],
                        "permissions": user_data.get("permissions", []),
                        "authenticated": True
                    }
            
            # For demo purposes, use default Azure credentials
            # In production, implement proper OAuth flow
            token = await self.credential.get_token("https://management.azure.com/.default")
            
            # Get Azure subscription information
            subscription_info = await self._get_subscription_info(token)
            
            # Update user data
            user_data.update({
                "authenticated": True,
                "access_token": token.token,
                "token_expiry": datetime.utcnow().timestamp() + 3600,  # 1 hour
                "subscription_id": subscription_info["subscription_id"],
                "tenant_id": subscription_info["tenant_id"],
                "user_id": turn_context.activity.from_property.id,
                "permissions": subscription_info.get("permissions", [])
            })
            
            return {
                "subscription_id": subscription_info["subscription_id"],
                "tenant_id": subscription_info["tenant_id"],
                "user_id": turn_context.activity.from_property.id,
                "permissions": subscription_info.get("permissions", []),
                "authenticated": True
            }
            
        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            return None
    
    async def _get_subscription_info(self, token: AccessToken) -> Dict[str, Any]:
        """Get Azure subscription information."""
        # In production, make actual API calls to get subscription info
        # For demo purposes, return mock data
        return {
            "subscription_id": "your-subscription-id-here",
            "tenant_id": "your-tenant-id-here",
            "permissions": [
                "Microsoft.Compute/virtualMachines/read",
                "Microsoft.Compute/virtualMachines/start/action",
                "Microsoft.Compute/virtualMachines/restart/action",
                "Microsoft.Network/networkSecurityGroups/read",
                "Microsoft.Network/networkSecurityGroups/write",
                "Microsoft.Monitor/read"
            ]
        }
    
    async def _send_response(self, turn_context: TurnContext, response: Dict[str, Any]):
        """Send formatted response to user."""
        try:
            message_text = response.get("message", "I've processed your request.")
            
            # Create adaptive card for rich response
            if response.get("status") in ["diagnostic_complete", "resolution_complete"]:
                card = self._create_diagnostic_card(response)
                await turn_context.send_activity(MessageFactory.attachment(card))
            else:
                await turn_context.send_activity(MessageFactory.text(message_text))
            
            # Send additional information if available
            if response.get("recommended_actions"):
                actions_text = "\n".join([f"• {action}" for action in response["recommended_actions"]])
                await turn_context.send_activity(
                    MessageFactory.text(f"**Recommended Actions:**\n{actions_text}")
                )
            
            if response.get("requires_resolution"):
                await turn_context.send_activity(
                    MessageFactory.text(
                        "I can help you implement these fixes. Would you like me to proceed with the recommended actions?"
                    )
                )
            
        except Exception as e:
            self.logger.error(f"Error sending response: {str(e)}")
            await turn_context.send_activity(
                MessageFactory.text("I encountered an error while sending the response.")
            )
    
    def _create_diagnostic_card(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Create an adaptive card for diagnostic results."""
        diagnostics = response.get("diagnostics", {})
        status = response.get("status", "unknown")
        
        # Create card body
        body = []
        
        # Add title
        body.append({
            "type": "TextBlock",
            "text": "🔍 **Diagnostic Results**",
            "weight": "Bolder",
            "size": "Medium"
        })
        
        # Add diagnostic results
        for check_name, result in diagnostics.items():
            if isinstance(result, dict) and result.get("success") is not None:
                status_icon = "✅" if result.get("success") else "❌"
                message = result.get("message", "Check completed")
                
                body.append({
                    "type": "TextBlock",
                    "text": f"{status_icon} **{check_name.replace('_', ' ').title()}**: {message}",
                    "wrap": True
                })
        
        # Add recommendations
        if response.get("recommended_actions"):
            body.append({
                "type": "TextBlock",
                "text": "📋 **Recommended Actions**",
                "weight": "Bolder",
                "size": "Medium"
            })
            
            for action in response["recommended_actions"]:
                body.append({
                    "type": "TextBlock",
                    "text": f"• {action}",
                    "wrap": True
                })
        
        # Create adaptive card
        card = {
            "type": "AdaptiveCard",
            "version": "1.4",
            "body": body,
            "actions": []
        }
        
        # Add action buttons
        if response.get("requires_resolution"):
            card["actions"].append({
                "type": "Action.Submit",
                "title": "Apply Fixes",
                "data": {"action": "apply_fixes"}
            })
        
        card["actions"].append({
            "type": "Action.Submit",
            "title": "Run Additional Tests",
            "data": {"action": "run_tests"}
        })
        
        return {
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": card
        }


class BotServiceFactory:
    """Factory class for creating bot service instances."""
    
    @staticmethod
    async def create_bot(conversation_state: ConversationState, user_state: UserState) -> AzureSupportBot:
        """Create and configure a bot service instance."""
        
        # Initialize Semantic Kernel
        kernel = Kernel()
        
        # Add Azure OpenAI service
        openai_service = AzureChatCompletionService(
            deployment_name="gpt-4-turbo",
            endpoint="https://your-openai-resource.openai.azure.com/",
            api_key="your-api-key",
            api_version="2024-02-15-preview"
        )
        kernel.add_service(openai_service)
        
        # Initialize conversation store
        conversation_store = ConversationStore(
            cosmos_endpoint="https://your-cosmosdb.documents.azure.com:443/",
            cosmos_key="your-cosmos-key",
            database_name="ai-support-bot",
            container_name="conversations"
        )
        
        # Create and return bot instance
        return AzureSupportBot(
            conversation_state=conversation_state,
            user_state=user_state,
            kernel=kernel,
            conversation_store=conversation_store
        )


# Bot service configuration
BOT_CONFIGURATION = {
    "app_id": "your-bot-app-id",
    "app_password": "your-bot-app-password",
    "openai_endpoint": "https://your-openai-resource.openai.azure.com/",
    "openai_api_key": "your-openai-api-key",
    "cosmos_endpoint": "https://your-cosmosdb.documents.azure.com:443/",
    "cosmos_key": "your-cosmos-key",
    "application_insights_key": "your-app-insights-key"
}
