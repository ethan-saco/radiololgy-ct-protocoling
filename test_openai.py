#!/usr/bin/env python3
"""
Test script to verify OpenAI API is functioning correctly.
"""

import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables")
    exit(1)

print(f"API Key found: {api_key[:5]}...{api_key[-5:]} (length: {len(api_key)})")

# Initialize client
client = OpenAI(api_key=api_key)

try:
    # Test a simple API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, world!"}
        ],
        temperature=0,
        max_tokens=100
    )
    
    # Print response
    print("\nAPI Response:")
    print(f"Response content: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    print(f"Usage tokens: {response.usage}")
    
    print("\nAPI test successful!")
    
except Exception as e:
    print(f"\nAPI Error: {str(e)}")
    print("\nTroubleshooting tips:")
    print("1. Check your API key format and validity")
    print("2. Verify your OpenAI account status and payment method")
    print("3. Ensure you have access to the requested model")
    print("4. Check your network connection and proxy settings") 