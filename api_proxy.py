#!/usr/bin/env python3
"""
Backend API proxy for business portfolio chatbot.
Proxies OpenAI API calls using the service's API key.
"""

import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend

# Get API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    print("WARNING: OPENAI_API_KEY environment variable not set!")
    print("Set it with: export OPENAI_API_KEY='sk-...'")

# Initialize OpenAI client
client = None
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)


@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Proxy endpoint for OpenAI chat completions.
    Uses the service's API key (from environment variable).
    """
    if not client:
        return jsonify({
            'error': {
                'message': 'OpenAI API key not configured. Please set OPENAI_API_KEY environment variable.'
            }
        }), 500
    
    try:
        data = request.json
        
        # Validate request
        if not data or 'messages' not in data:
            return jsonify({
                'error': {
                    'message': 'Invalid request: messages field required'
                }
            }), 400
        
        # Extract parameters
        model = data.get('model', 'gpt-4o-mini')
        messages = data.get('messages', [])
        temperature = data.get('temperature', 0.7)
        
        # Make request to OpenAI
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature
        )
        
        # Return response in OpenAI format
        return jsonify({
            'choices': [{
                'message': {
                    'role': response.choices[0].message.role,
                    'content': response.choices[0].message.content
                }
            }],
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            }
        })
        
    except Exception as e:
        error_msg = str(e)
        status_code = 500
        
        # Handle specific OpenAI errors
        if 'authentication' in error_msg.lower() or 'api key' in error_msg.lower():
            status_code = 401
            error_msg = 'Invalid API key. Please check OPENAI_API_KEY environment variable.'
        elif 'rate limit' in error_msg.lower():
            status_code = 429
            error_msg = 'Rate limit exceeded. Please try again later.'
        
        return jsonify({
            'error': {
                'message': f'Error: {error_msg}'
            }
        }), status_code


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'api_key_configured': bool(OPENAI_API_KEY)
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print(f"Starting API proxy server on port {port}")
    print(f"API key configured: {bool(OPENAI_API_KEY)}")
    print(f"Health check: http://localhost:{port}/health")
    print(f"Chat endpoint: http://localhost:{port}/api/chat")
    app.run(host='0.0.0.0', port=port, debug=True)






