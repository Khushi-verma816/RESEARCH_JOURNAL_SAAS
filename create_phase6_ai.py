"""
Phase 6: AI Chat Assistant
"""
import os

def create_file(path, content):
    """Create a file with content"""
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Created: {path}")

files = {
    'app/routes/ai.py': '''"""
AI Chat Assistant routes
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import AIConversation, AIMessage
from datetime import datetime
import openai
import os

ai_bp = Blueprint('ai', __name__)

# Get OpenAI API key from environment
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

@ai_bp.route('/')
@login_required
def index():
    """AI Chat home - list conversations"""
    conversations = AIConversation.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(AIConversation.created_at.desc()).all()
    
    return render_template('ai/index.html', conversations=conversations)

@ai_bp.route('/chat/<int:conversation_id>')
@login_required
def chat(conversation_id):
    """Chat interface for a conversation"""
    conversation = AIConversation.query.get_or_404(conversation_id)
    
    # Check ownership
    if conversation.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('ai.index'))
    
    # Get messages
    messages = AIMessage.query.filter_by(
        conversation_id=conversation_id
    ).order_by(AIMessage.created_at.asc()).all()
    
    return render_template('ai/chat.html', 
                         conversation=conversation,
                         messages=messages,
                         has_api_key=bool(OPENAI_API_KEY))

@ai_bp.route('/new', methods=['POST'])
@login_required
def new_conversation():
    """Create a new conversation"""
    title = request.form.get('title', 'New Conversation')
    
    conversation = AIConversation(
        user_id=current_user.id,
        title=title,
        is_active=True
    )
    
    db.session.add(conversation)
    db.session.commit()
    
    return redirect(url_for('ai.chat', conversation_id=conversation.id))

@ai_bp.route('/send/<int:conversation_id>', methods=['POST'])
@login_required
def send_message(conversation_id):
    """Send a message and get AI response"""
    conversation = AIConversation.query.get_or_404(conversation_id)
    
    # Check ownership
    if conversation.user_id != current_user.id:
        return jsonify({'error': 'Access denied'}), 403
    
    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Save user message
    user_msg = AIMessage(
        conversation_id=conversation_id,
        role='user',
        content=user_message
    )
    db.session.add(user_msg)
    db.session.commit()
    
    # Get AI response
    try:
        if not OPENAI_API_KEY:
            ai_response = "⚠️ OpenAI API key not configured. Please add OPENAI_API_KEY to your .env file to enable AI responses.\\n\\nFor demo purposes, I'm a simulated response! In production, I would use GPT-4 to provide intelligent assistance with:\\n\\n• Research methodology\\n• Literature review\\n• Academic writing\\n• Data analysis\\n• Citation formatting\\n• Manuscript preparation"
        else:
            # Get conversation history
            history = AIMessage.query.filter_by(
                conversation_id=conversation_id
            ).order_by(AIMessage.created_at.asc()).limit(20).all()
            
            # Build messages for OpenAI
            openai_messages = [
                {
                    "role": "system",
                    "content": "You are a helpful research assistant specialized in academic writing, research methodology, and scientific communication. Provide clear, accurate, and helpful responses to support researchers and academics."
                }
            ]
            
            for msg in history:
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Call OpenAI API
            import openai
            openai.api_key = OPENAI_API_KEY
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=openai_messages,
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
        
        # Save AI response
        ai_msg = AIMessage(
            conversation_id=conversation_id,
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_msg)
        
        # Update conversation title if it's the first message
        if not conversation.title or conversation.title == 'New Conversation':
            # Use first few words of user message as title
            conversation.title = user_message[:50] + ('...' if len(user_message) > 50 else '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'user_message': {
                'id': user_msg.id,
                'content': user_msg.content,
                'created_at': user_msg.created_at.strftime('%H:%M')
            },
            'ai_message': {
                'id': ai_msg.id,
                'content': ai_msg.content,
                'created_at': ai_msg.created_at.strftime('%H:%M')
            }
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting AI response: {str(e)}'
        }), 500

@ai_bp.route('/delete/<int:conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation"""
    conversation = AIConversation.query.get_or_404(conversation_id)
    
    # Check ownership
    if conversation.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('ai.index'))
    
    conversation.is_active = False
    db.session.commit()
    
    flash('Conversation deleted', 'success')
    return redirect(url_for('ai.index'))
''',

    'app/templates/ai/index.html': '''{% extends "base.html" %}

{% block title %}AI Assistant - Research Journal SaaS{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px;">
        <h1 style="color: #007bff; margin: 0;">🤖 AI Research Assistant</h1>
        <form method="POST" action="{{ url_for('ai.new_conversation') }}">
            <button type="submit" 
                    style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                ➕ New Conversation
            </button>
        </form>
    </div>
    
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 8px; color: white; margin-bottom: 30px;">
        <h3 style="margin: 0 0 10px 0;">Your AI Research Companion</h3>
        <p style="margin: 0; opacity: 0.9;">
            Get help with research methodology, literature review, academic writing, data analysis, and more!
        </p>
    </div>
    
    {% if conversations %}
        <h2 style="color: #333; margin-bottom: 15px;">Your Conversations</h2>
        <div style="display: grid; gap: 15px;">
            {% for conversation in conversations %}
            <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                <div style="flex: 1;">
                    <h3 style="margin: 0 0 8px 0; color: #333;">{{ conversation.title }}</h3>
                    <p style="margin: 0; color: #666; font-size: 14px;">
                        Started {{ conversation.created_at.strftime('%B %d, %Y at %I:%M %p') }}
                    </p>
                </div>
                <div style="display: flex; gap: 10px;">
                    <a href="{{ url_for('ai.chat', conversation_id=conversation.id) }}" 
                       style="padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px;">
                        💬 Open Chat
                    </a>
                    <form method="POST" action="{{ url_for('ai.delete_conversation', conversation_id=conversation.id) }}"
                          onsubmit="return confirm('Delete this conversation?');"
                          style="display: inline;">
                        <button type="submit" 
                                style="padding: 8px 16px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer;">
                            🗑️ Delete
                        </button>
                    </form>
                </div>
            </div>
            {% endfor %}
        </div>
    {% else %}
        <div style="text-align: center; padding: 60px; background: #f8f9fa; border-radius: 8px;">
            <h3 style="color: #666; margin-bottom: 15px;">No conversations yet</h3>
            <p style="color: #999; margin-bottom: 25px;">Start a conversation with your AI research assistant!</p>
            <form method="POST" action="{{ url_for('ai.new_conversation') }}">
                <button type="submit" 
                        style="padding: 12px 24px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px;">
                    Start Your First Conversation
                </button>
            </form>
        </div>
    {% endif %}
</div>
{% endblock %}
''',

    'app/templates/ai/chat.html': '''{% extends "base.html" %}

{% block title %}AI Chat - Research Journal SaaS{% endblock %}

{% block extra_css %}
<style>
    .chat-container {
        height: 500px;
        overflow-y: auto;
        padding: 20px;
        background: #f8f9fa;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .message {
        margin-bottom: 15px;
        display: flex;
        gap: 10px;
    }
    .message.user {
        justify-content: flex-end;
    }
    .message-bubble {
        max-width: 70%;
        padding: 12px 16px;
        border-radius: 12px;
        word-wrap: break-word;
        white-space: pre-wrap;
    }
    .message.user .message-bubble {
        background: #007bff;
        color: white;
        border-bottom-right-radius: 4px;
    }
    .message.assistant .message-bubble {
        background: white;
        color: #333;
        border: 1px solid #ddd;
        border-bottom-left-radius: 4px;
    }
    .message-time {
        font-size: 11px;
        opacity: 0.7;
        margin-top: 4px;
    }
    .typing-indicator {
        display: none;
        padding: 12px 16px;
        background: white;
        border: 1px solid #ddd;
        border-radius: 12px;
        width: fit-content;
    }
    .typing-indicator.active {
        display: block;
    }
    .typing-indicator span {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #007bff;
        margin: 0 2px;
        animation: typing 1.4s infinite;
    }
    .typing-indicator span:nth-child(2) {
        animation-delay: 0.2s;
    }
    .typing-indicator span:nth-child(3) {
        animation-delay: 0.4s;
    }
    @keyframes typing {
        0%, 60%, 100% { transform: translateY(0); }
        30% { transform: translateY(-10px); }
    }
</style>
{% endblock %}

{% block content %}
<div style="background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <div>
            <h1 style="color: #007bff; margin: 0 0 5px 0;">{{ conversation.title }}</h1>
            <p style="color: #666; margin: 0; font-size: 14px;">
                AI Research Assistant • Started {{ conversation.created_at.strftime('%B %d, %Y') }}
            </p>
        </div>
        <a href="{{ url_for('ai.index') }}" 
           style="padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px;">
            ← Back
        </a>
    </div>
    
    {% if not has_api_key %}
    <div style="background: #fff3cd; padding: 15px; border-radius: 6px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
        <strong>⚠️ Demo Mode:</strong> OpenAI API key not configured. Add OPENAI_API_KEY to your .env file to enable real AI responses.
    </div>
    {% endif %}
    
    <!-- Chat Messages -->
    <div class="chat-container" id="chatContainer">
        {% for message in messages %}
        <div class="message {{ message.role }}">
            <div class="message-bubble">
                <div>{{ message.content }}</div>
                <div class="message-time">{{ message.created_at.strftime('%H:%M') }}</div>
            </div>
        </div>
        {% endfor %}
        
        <div class="typing-indicator" id="typingIndicator">
            <span></span><span></span><span></span>
        </div>
    </div>
    
    <!-- Message Input -->
    <form id="chatForm" style="display: flex; gap: 10px;">
        <input type="text" 
               id="messageInput"
               placeholder="Ask about research methodology, writing tips, analysis..." 
               required
               style="flex: 1; padding: 12px; border: 2px solid #ddd; border-radius: 6px; font-size: 16px;">
        <button type="submit" 
                id="sendButton"
                style="padding: 12px 24px; background: #007bff; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; white-space: nowrap;">
            Send 📤
        </button>
    </form>
    
    <!-- Suggested Prompts -->
    {% if not messages %}
    <div style="margin-top: 20px; padding: 20px; background: #f8f9fa; border-radius: 6px;">
        <h3 style="color: #333; margin: 0 0 15px 0; font-size: 16px;">💡 Try asking:</h3>
        <div style="display: grid; gap: 10px;">
            <button onclick="usePrompt(this)" data-prompt="Help me structure a literature review for my research on machine learning in healthcare" 
                    style="padding: 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: left; transition: background 0.3s;"
                    onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='white'">
                Help me structure a literature review
            </button>
            <button onclick="usePrompt(this)" data-prompt="What are the best practices for data visualization in scientific papers?" 
                    style="padding: 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: left; transition: background 0.3s;"
                    onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='white'">
                Best practices for data visualization
            </button>
            <button onclick="usePrompt(this)" data-prompt="How do I write an effective research methodology section?" 
                    style="padding: 10px; background: white; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; text-align: left; transition: background 0.3s;"
                    onmouseover="this.style.background='#e9ecef'" onmouseout="this.style.background='white'">
                Writing a research methodology section
            </button>
        </div>
    </div>
    {% endif %}
</div>

<script>
const chatForm = document.getElementById('chatForm');
const messageInput = document.getElementById('messageInput');
const sendButton = document.getElementById('sendButton');
const chatContainer = document.getElementById('chatContainer');
const typingIndicator = document.getElementById('typingIndicator');

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function addMessage(content, role, time) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message ' + role;
    messageDiv.innerHTML = `
        <div class="message-bubble">
            <div>${content}</div>
            <div class="message-time">${time}</div>
        </div>
    `;
    chatContainer.insertBefore(messageDiv, typingIndicator);
    scrollToBottom();
}

function usePrompt(button) {
    const prompt = button.getAttribute('data-prompt');
    messageInput.value = prompt;
    messageInput.focus();
}

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const message = messageInput.value.trim();
    if (!message) return;
    
    // Disable input
    messageInput.disabled = true;
    sendButton.disabled = true;
    sendButton.textContent = 'Sending...';
    
    try {
        const response = await fetch('{{ url_for("ai.send_message", conversation_id=conversation.id) }}', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add user message
            addMessage(data.user_message.content, 'user', data.user_message.created_at);
            
            // Show typing indicator
            typingIndicator.classList.add('active');
            scrollToBottom();
            
            // Simulate typing delay
            setTimeout(() => {
                typingIndicator.classList.remove('active');
                // Add AI message
                addMessage(data.ai_message.content, 'assistant', data.ai_message.created_at);
            }, 1000);
            
            messageInput.value = '';
        } else {
            alert('Error: ' + data.error);
        }
    } catch (error) {
        alert('Error sending message: ' + error);
    } finally {
        messageInput.disabled = false;
        sendButton.disabled = false;
        sendButton.textContent = 'Send 📤';
        messageInput.focus();
    }
});

// Scroll to bottom on load
scrollToBottom();
</script>
{% endblock %}
''',
}

print("Creating Phase 6 files...\n")
for filepath, content in files.items():
    create_file(filepath, content)

print("\n" + "="*60)
print("✅ PHASE 6 FILES CREATED SUCCESSFULLY!")
print("="*60)
print("\nNext steps:")
print("1. Update app/__init__.py to register ai blueprint")
print("2. Add AI Assistant link to navigation")
print("3. (Optional) Add OPENAI_API_KEY to .env file")
print("4. Restart Flask")
print("5. Test the AI chat assistant!")