"""
AI service for OpenAI integration
"""
import openai
from flask import current_app
from app.extensions import db
from app.models.ai import AIMessage, AIGeneratedContent
from datetime import datetime


class AIService:
    """AI service for chat and content generation"""
    
    def __init__(self):
        self.api_key = current_app.config.get('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.model = current_app.config.get('OPENAI_MODEL', 'gpt-4')
    
    def chat_completion(self, messages, conversation_id=None, temperature=0.7):
        """Get chat completion from OpenAI"""
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=messages,
                temperature=temperature
            )
            
            assistant_message = response['choices'][0]['message']['content']
            tokens_used = response['usage']['total_tokens']
            
            # Save message if conversation_id provided
            if conversation_id:
                ai_message = AIMessage(
                    conversation_id=conversation_id,
                    role='assistant',
                    content=assistant_message,
                    tokens_used=tokens_used
                )
                db.session.add(ai_message)
                db.session.commit()
            
            return {
                'success': True,
                'content': assistant_message,
                'tokens_used': tokens_used
            }
        except Exception as e:
            current_app.logger.error(f"OpenAI error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_text(self, prompt, user_id, max_tokens=1000):
        """Generate text content"""
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=prompt,
                max_tokens=max_tokens
            )
            
            generated_text = response['choices'][0]['text'].strip()
            tokens_used = response['usage']['total_tokens']
            
            # Save generated content
            content = AIGeneratedContent(
                user_id=user_id,
                content_type='text',
                prompt=prompt,
                result=generated_text,
                service='openai',
                model='text-davinci-003',
                tokens_used=tokens_used,
                status='completed',
                completed_at=datetime.utcnow()
            )
            db.session.add(content)
            db.session.commit()
            
            return {
                'success': True,
                'content': generated_text,
                'tokens_used': tokens_used
            }
        except Exception as e:
            current_app.logger.error(f"Text generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_image(self, prompt, user_id, size="1024x1024"):
        """Generate image using DALL-E"""
        try:
            response = openai.Image.create(
                prompt=prompt,
                n=1,
                size=size
            )
            
            image_url = response['data'][0]['url']
            
            # Save generated content
            content = AIGeneratedContent(
                user_id=user_id,
                content_type='image',
                prompt=prompt,
                file_url=image_url,
                service='openai',
                model='dall-e-2',
                status='completed',
                completed_at=datetime.utcnow()
            )
            db.session.add(content)
            db.session.commit()
            
            return {
                'success': True,
                'image_url': image_url
            }
        except Exception as e:
            current_app.logger.error(f"Image generation error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_document(self, document_text, analysis_type='grammar'):
        """Analyze document for grammar, plagiarism, etc."""
        prompts = {
            'grammar': f"Analyze the following text for grammar and spelling errors:\n\n{document_text}",
            'clarity': f"Analyze the following text for clarity and readability:\n\n{document_text}",
            'summary': f"Provide a concise summary of the following text:\n\n{document_text}"
        }
        
        prompt = prompts.get(analysis_type, prompts['grammar'])
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful writing assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            analysis = response['choices'][0]['message']['content']
            
            return {
                'success': True,
                'analysis': analysis
            }
        except Exception as e:
            current_app.logger.error(f"Document analysis error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }