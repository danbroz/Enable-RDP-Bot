#!/usr/bin/env python3
"""
Test script to verify OpenAI model availability and GPT-5 access
"""

import os
import sys
from dotenv import load_dotenv
import openai

def test_openai_models():
    """Test OpenAI API and check available models"""
    load_dotenv()
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key in the .env file")
        return False
    
    try:
        # Initialize OpenAI client
        client = openai.OpenAI(api_key=api_key)
        
        print("🔍 Testing OpenAI API connection...")
        
        # Fetch available models
        models = client.models.list()
        available_models = [model.id for model in models.data]
        
        print(f"✅ Successfully connected to OpenAI API")
        print(f"📊 Total models available: {len(available_models)}")
        
        # Check for GPT models
        gpt_models = [model for model in available_models if 'gpt' in model.lower()]
        
        print(f"\n🤖 GPT Models Available:")
        for model in sorted(gpt_models):
            status = "🎯 GPT-5" if model == 'gpt-5' else "  "
            print(f"  {status} {model}")
        
        # Check specifically for GPT-5
        if 'gpt-5' in available_models:
            print(f"\n✅ GPT-5 is available! The tool will use GPT-5 for analysis.")
        else:
            print(f"\n⚠️  GPT-5 is not available. The tool will use the best available model.")
            if gpt_models:
                print(f"   Best available GPT model: {gpt_models[0]}")
        
        # Test a simple API call
        print(f"\n🧪 Testing API call with selected model...")
        
        # Select best model
        preferred_models = ["gpt-5", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        selected_model = None
        
        for model in preferred_models:
            if model in available_models:
                selected_model = model
                break
        
        if not selected_model and gpt_models:
            selected_model = gpt_models[0]
        
        if selected_model:
            print(f"   Using model: {selected_model}")
            
            # Test API call
            response = client.chat.completions.create(
                model=selected_model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Say 'Hello, GPT-5 is working!' if you are GPT-5, or 'Hello, I am working!' if you are another model."}
                ],
                max_tokens=50
            )
            
            print(f"   ✅ API call successful!")
            print(f"   Response: {response.choices[0].message.content}")
            
        else:
            print(f"   ❌ No suitable GPT models found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI API: {e}")
        return False

def main():
    print("🚀 OpenAI Model Availability Test")
    print("=" * 50)
    
    success = test_openai_models()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed! The Enable RDP Bot is ready to use.")
        print("\nNext steps:")
        print("1. Run: python enable_rdp.py --list-models")
        print("2. Run: python enable_rdp.py --resource-group <rg> --vm <vm>")
    else:
        print("❌ Tests failed. Please check your OpenAI API key and try again.")
        sys.exit(1)

if __name__ == '__main__':
    main()
