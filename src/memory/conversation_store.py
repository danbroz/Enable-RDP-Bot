"""
Conversation Store for Azure Support Bot

This module provides conversation memory management using Azure Cosmos DB
to store and retrieve conversation history for the agentic AI system.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import uuid

from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosResourceExistsError
from semantic_kernel.contents import ChatHistory, ChatMessageContent
from semantic_kernel.contents.author_role import AuthorRole


class ConversationStore:
    """Manages conversation history using Azure Cosmos DB."""
    
    def __init__(self, cosmos_endpoint: str, cosmos_key: str, 
                 database_name: str = "ai-support-bot",
                 container_name: str = "conversations"):
        self.cosmos_endpoint = cosmos_endpoint
        self.cosmos_key = cosmos_key
        self.database_name = database_name
        self.container_name = container_name
        
        # Initialize Cosmos DB client
        self.client = CosmosClient(cosmos_endpoint, cosmos_key)
        self.database = None
        self.container = None
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize database and container
        asyncio.create_task(self._initialize_cosmos())
    
    async def _initialize_cosmos(self):
        """Initialize Cosmos DB database and container."""
        try:
            # Create database if it doesn't exist
            try:
                self.database = await self.client.create_database_if_not_exists(
                    id=self.database_name
                )
            except CosmosResourceExistsError:
                self.database = self.client.get_database_client(database=self.database_name)
            
            # Create container if it doesn't exist
            try:
                self.container = await self.database.create_container_if_not_exists(
                    id=self.container_name,
                    partition_key=PartitionKey(path="/conversation_id"),
                    offer_throughput=400
                )
            except CosmosResourceExistsError:
                self.container = self.database.get_container_client(container=self.container_name)
            
            self.logger.info("Cosmos DB initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Cosmos DB: {str(e)}")
            raise
    
    async def get_conversation(self, conversation_id: str = None) -> ChatHistory:
        """
        Get conversation history for a given conversation ID.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            ChatHistory object with conversation messages
        """
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            # Query for conversation
            query = "SELECT * FROM c WHERE c.conversation_id = @conversation_id ORDER BY c.timestamp"
            parameters = [{"name": "@conversation_id", "value": conversation_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            
            # Create ChatHistory object
            chat_history = ChatHistory()
            
            if items:
                # Sort by timestamp and add messages
                items.sort(key=lambda x: x["timestamp"])
                for item in items:
                    role = AuthorRole.USER if item["role"] == "user" else AuthorRole.ASSISTANT
                    message = ChatMessageContent(
                        role=role,
                        content=item["content"],
                        metadata={"timestamp": item["timestamp"]}
                    )
                    chat_history.add_message(message)
            
            return chat_history
            
        except Exception as e:
            self.logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
            # Return empty conversation on error
            return ChatHistory()
    
    async def save_conversation(self, conversation_id: str, chat_history: ChatHistory) -> bool:
        """
        Save conversation history to Cosmos DB.
        
        Args:
            conversation_id: Unique conversation identifier
            chat_history: ChatHistory object to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            # Get existing conversation to avoid duplicates
            existing_items = list(self.container.query_items(
                query="SELECT * FROM c WHERE c.conversation_id = @conversation_id",
                parameters=[{"name": "@conversation_id", "value": conversation_id}],
                enable_cross_partition_query=False
            ))
            
            existing_timestamps = {item["timestamp"] for item in existing_items}
            
            # Save new messages only
            for i, message in enumerate(chat_history.messages):
                timestamp = datetime.utcnow().isoformat()
                
                # Skip if message already exists
                if timestamp in existing_timestamps:
                    continue
                
                message_item = {
                    "id": f"{conversation_id}-{i}-{timestamp}",
                    "conversation_id": conversation_id,
                    "role": "user" if message.role == AuthorRole.USER else "assistant",
                    "content": str(message.content),
                    "timestamp": timestamp,
                    "metadata": dict(message.metadata) if message.metadata else {}
                }
                
                await self.container.create_item(body=message_item)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving conversation {conversation_id}: {str(e)}")
            return False
    
    async def add_message(self, conversation_id: str, role: str, content: str,
                         metadata: Dict[str, Any] = None) -> bool:
        """
        Add a single message to conversation history.
        
        Args:
            conversation_id: Unique conversation identifier
            role: Message role (user or assistant)
            content: Message content
            metadata: Additional message metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            timestamp = datetime.utcnow().isoformat()
            message_id = f"{conversation_id}-{timestamp}"
            
            message_item = {
                "id": message_id,
                "conversation_id": conversation_id,
                "role": role,
                "content": content,
                "timestamp": timestamp,
                "metadata": metadata or {}
            }
            
            await self.container.create_item(body=message_item)
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            return False
    
    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get a summary of the conversation.
        
        Args:
            conversation_id: Unique conversation identifier
            
        Returns:
            Conversation summary with metadata
        """
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            # Query for conversation messages
            query = "SELECT * FROM c WHERE c.conversation_id = @conversation_id ORDER BY c.timestamp"
            parameters = [{"name": "@conversation_id", "value": conversation_id}]
            
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=False
            ))
            
            if not items:
                return {
                    "conversation_id": conversation_id,
                    "message_count": 0,
                    "duration": 0,
                    "start_time": None,
                    "end_time": None,
                    "summary": "No conversation found"
                }
            
            # Calculate summary statistics
            start_time = items[0]["timestamp"]
            end_time = items[-1]["timestamp"]
            message_count = len(items)
            
            # Calculate duration
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            duration_seconds = (end_dt - start_dt).total_seconds()
            
            # Generate basic summary
            user_messages = [item for item in items if item["role"] == "user"]
            assistant_messages = [item for item in items if item["role"] == "assistant"]
            
            summary = f"Conversation with {message_count} messages ({len(user_messages)} user, {len(assistant_messages)} assistant) over {duration_seconds:.0f} seconds"
            
            return {
                "conversation_id": conversation_id,
                "message_count": message_count,
                "user_messages": len(user_messages),
                "assistant_messages": len(assistant_messages),
                "duration_seconds": duration_seconds,
                "start_time": start_time,
                "end_time": end_time,
                "summary": summary
            }
            
        except Exception as e:
            self.logger.error(f"Error getting conversation summary {conversation_id}: {str(e)}")
            return {
                "conversation_id": conversation_id,
                "error": str(e),
                "summary": "Error retrieving conversation summary"
            }
    
    async def cleanup_old_conversations(self, days_old: int = 30) -> int:
        """
        Clean up conversations older than specified days.
        
        Args:
            days_old: Number of days to keep conversations
            
        Returns:
            Number of conversations deleted
        """
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            cutoff_iso = cutoff_date.isoformat()
            
            # Query for old conversations
            query = "SELECT c.conversation_id FROM c WHERE c.timestamp < @cutoff_date"
            parameters = [{"name": "@cutoff_date", "value": cutoff_iso}]
            
            old_conversations = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            
            # Get unique conversation IDs
            conversation_ids = set(item["conversation_id"] for item in old_conversations)
            
            deleted_count = 0
            for conversation_id in conversation_ids:
                # Delete all messages for this conversation
                messages_query = "SELECT c.id FROM c WHERE c.conversation_id = @conversation_id"
                message_parameters = [{"name": "@conversation_id", "value": conversation_id}]
                
                messages = list(self.container.query_items(
                    query=messages_query,
                    parameters=message_parameters,
                    enable_cross_partition_query=False
                ))
                
                for message in messages:
                    await self.container.delete_item(
                        item=message["id"],
                        partition_key=conversation_id
                    )
                    deleted_count += 1
            
            self.logger.info(f"Cleaned up {deleted_count} messages from {len(conversation_ids)} old conversations")
            return deleted_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old conversations: {str(e)}")
            return 0
    
    async def search_conversations(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search conversations by content.
        
        Args:
            query_text: Text to search for
            limit: Maximum number of results
            
        Returns:
            List of matching conversations
        """
        try:
            if not self.container:
                await self._initialize_cosmos()
            
            # Search for conversations containing the query text
            query = "SELECT DISTINCT c.conversation_id FROM c WHERE CONTAINS(c.content, @query_text)"
            parameters = [{"name": "@query_text", "value": query_text}]
            
            results = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
                max_item_count=limit
            ))
            
            # Get summaries for matching conversations
            conversation_summaries = []
            for result in results:
                summary = await self.get_conversation_summary(result["conversation_id"])
                conversation_summaries.append(summary)
            
            return conversation_summaries
            
        except Exception as e:
            self.logger.error(f"Error searching conversations: {str(e)}")
            return []
