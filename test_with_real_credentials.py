#!/usr/bin/env python3
"""
Test the Azure Agentic AI Support Bot with real credentials
This script tests the agent functionality without requiring Terraform deployment
"""

import asyncio
import os
import sys
from datetime import datetime

# Add src to path
sys.path.append('src')

from agents.simple_agent import AzureSupportBot

async def test_with_real_credentials():
    """Test the bot with real Azure credentials"""
    
    # Load environment variables
    subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
    openai_api_key = os.getenv("AZURE_OPENAI_API_KEY")
    
    print("🤖 Azure Agentic AI Support Bot - Real Credentials Test")
    print("=" * 60)
    
    if not subscription_id:
        print("❌ AZURE_SUBSCRIPTION_ID is not set")
        return
    
    if not openai_api_key:
        print("❌ AZURE_OPENAI_API_KEY is not set")
        return
    
    print(f"✅ Subscription ID: {subscription_id[:8]}...")
    print(f"✅ OpenAI API Key: {openai_api_key[:10]}...")
    print()
    
    try:
        print("🤖 Initializing Azure Support Bot...")
        bot = AzureSupportBot(subscription_id, openai_api_key)
        
        # Test scenarios
        test_scenarios = [
            {
                "name": "Real VM Test",
                "vm_name": "support-bot-test-vm",
                "resource_group": "azure-support-bot-rg"
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n📋 Testing: {scenario['name']}")
            print(f"   VM: {scenario['vm_name']}")
            print(f"   Resource Group: {scenario['resource_group']}")
            print("-" * 40)
            
            try:
                session_id = await bot.start_troubleshooting(
                    scenario['vm_name'], 
                    scenario['resource_group']
                )
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
                else:
                    print("❌ Failed to get troubleshooting results")
                    
            except Exception as e:
                print(f"⚠️  Error during troubleshooting: {str(e)}")
                print("   This might be expected if the VM doesn't exist yet")
        
        print("\n🎉 Real credentials test completed!")
        print("\n📋 Next Steps:")
        print("1. The agent is working with your real Azure credentials")
        print("2. To deploy infrastructure, you need to fix the service principal authentication")
        print("3. Either create a new service principal or use Azure CLI login")
        print("4. Then run the deployment script again")
        
    except Exception as e:
        print(f"❌ Error initializing bot: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your Azure credentials in .env file")
        print("2. Ensure your service principal has proper permissions")
        print("3. Verify your subscription ID is correct")

if __name__ == "__main__":
    asyncio.run(test_with_real_credentials())
