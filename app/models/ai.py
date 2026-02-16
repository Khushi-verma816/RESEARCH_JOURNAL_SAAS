"""
AI-related models
"""
from datetime import datetime
from app.extensions import db

class AIConversation(db.Model):
    """AI chat conversation model"""
    
    __tablename__ = 'ai_conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Details
    title = db.Column(db.String(255), nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='ai_conversations')
    messages = db.relationship('AIMessage', backref='conversation', lazy='dynamic')
    
    def __repr__(self):
        return f'<AIConversation {self.id}>'

class AIMessage(db.Model):
    """AI chat message model"""
    
    __tablename__ = 'ai_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('ai_conversations.id'), nullable=False)
    
    # Message
    role = db.Column(db.String(20), nullable=False)  # user, assistant
    content = db.Column(db.Text, nullable=False)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AIMessage {self.id}>'
