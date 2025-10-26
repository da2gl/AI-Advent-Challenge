"""Flask web application for Gemini Terminal Chat."""

import os
import sys
from pathlib import Path
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# Add parent directory to path to import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.gemini_client import GeminiApiClient, GeminiModel
from core.conversation import ConversationHistory
from core.storage import SQLiteStorage

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max request size

# Initialize Gemini client
API_KEY = os.getenv('GEMINI_API_KEY')
if not API_KEY:
    print("WARNING: GEMINI_API_KEY not found in environment variables")
    print("Chat functionality will not work without API key")

# Global storage and client (will be initialized per session in production)
gemini_client = GeminiApiClient(API_KEY) if API_KEY else None
storage = SQLiteStorage("data/web_conversations.db")

# Deployment pipeline (will be initialized when needed)
deployment_pipeline = None
deployment_status = {
    'status': 'idle',
    'stages': []
}


@app.route('/')
def index():
    """Render main chat interface."""
    return render_template('index.html')


@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages."""
    if not gemini_client:
        return jsonify({
            'error': 'Gemini API key not configured. Please set GEMINI_API_KEY environment variable.'
        }), 500

    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        # Convert history to Gemini format
        conversation_history = []
        for msg in history:
            conversation_history.append({
                'role': msg['role'],
                'parts': [{'text': msg['content']}]
            })

        # Generate response
        response = gemini_client.generate_content(
            prompt=message,
            model=GeminiModel.GEMINI_2_5_FLASH,
            conversation_history=conversation_history,
            temperature=0.7,
            max_output_tokens=2048
        )

        assistant_text = gemini_client.extract_text(response)

        # Update history
        history.append({'role': 'user', 'content': message})
        history.append({'role': 'model', 'content': assistant_text})

        return jsonify({
            'response': assistant_text,
            'history': history
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/deploy', methods=['POST'])
def deploy():
    """Trigger deployment pipeline."""
    global deployment_status, deployment_pipeline

    try:
        # Get platform from request (default to railway)
        data = request.json or {}
        platform = data.get('platform', 'railway')

        # Import deployment pipeline
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from pipeline.deploy_pipeline import DeploymentPipeline

        # Initialize pipeline if needed
        if deployment_pipeline is None:
            deployment_pipeline = DeploymentPipeline(gemini_client)

        # Reset status
        deployment_status = {
            'status': 'running',
            'stages': [
                {'name': 'Validation', 'status': 'running', 'message': 'Validating project...'},
                {'name': 'Build Preparation', 'status': 'pending', 'message': 'Waiting...'},
                {'name': 'AI Analysis', 'status': 'pending', 'message': 'Waiting...'},
                {'name': 'Deployment', 'status': 'pending', 'message': 'Waiting...'}
            ]
        }

        # Run deployment (in production, this would be async)
        try:
            result = deployment_pipeline.deploy(platform=platform)

            # Update status based on result
            results = result.get('results', {})
            ai_recommendations = results.get('ai_recommendations', '')
            deployment_result = results.get('deployment_result')

            # Add deployment logs to response
            deployment_logs = []
            if deployment_result:
                deployment_logs = deployment_result.logs if hasattr(deployment_result, 'logs') else []

            deployment_status = {
                'status': result.get('status', 'success'),
                'stages': result.get('stages', []),
                'ai_recommendations': ai_recommendations,
                'deployment_logs': deployment_logs
            }

            return jsonify(deployment_status)

        except Exception as e:
            deployment_status = {
                'status': 'error',
                'stages': [
                    {'name': 'Deployment', 'status': 'error', 'message': str(e)}
                ]
            }
            return jsonify(deployment_status), 500

    except Exception as e:
        return jsonify({
            'error': f'Failed to initialize deployment: {str(e)}',
            'status': 'error'
        }), 500


@app.route('/api/deploy/status', methods=['GET'])
def deploy_status():
    """Get deployment status."""
    return jsonify(deployment_status)


@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'api_key_configured': API_KEY is not None,
        'version': '1.0.0'
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'error': 'Not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Ensure data directory exists
    Path('data').mkdir(exist_ok=True)

    # Run server
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"""
    ╔═══════════════════════════════════════════════════════════════╗
    ║              Gemini Terminal Chat Server                     ║
    ║                      Starting...                             ║
    ╚═══════════════════════════════════════════════════════════════╝

    Server running on: http://localhost:{port}
    API Key configured: {API_KEY is not None}
    Debug mode: {debug}

    Press CTRL+C to stop
    """)

    app.run(host='0.0.0.0', port=port, debug=debug)
