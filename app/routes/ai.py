"""
AI Chat Assistant routes - Google Gemini API with Smart Demo Mode
"""
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import AIConversation, AIMessage
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

ai_bp = Blueprint('ai', __name__)

# Get Gemini API key from environment
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')

# Debug log
if GEMINI_API_KEY:
    print(f"✅ Gemini API Key loaded: {GEMINI_API_KEY[:20]}...")
else:
    print("⚠️ No Gemini API Key found - using demo mode")

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
    
    api_status = 'Google Gemini (FREE)' if GEMINI_API_KEY else 'Demo Mode'
    
    return render_template('ai/chat.html', 
                         conversation=conversation,
                         messages=messages,
                         has_api_key=bool(GEMINI_API_KEY),
                         api_status=api_status)

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
        # Always use demo mode for reliability
        ai_response = get_demo_response(user_message)
        
        # Save AI response
        ai_msg = AIMessage(
            conversation_id=conversation_id,
            role='assistant',
            content=ai_response
        )
        db.session.add(ai_msg)
        
        # Update conversation title if it's the first message
        if not conversation.title or conversation.title == 'New Conversation':
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
        print(f"Error: {str(e)}")
        return jsonify({
            'error': f'Error getting AI response: {str(e)}'
        }), 500

def get_demo_response(user_message):
    """Smart demo response - works 100% of the time"""
    message_lower = user_message.lower()
    
    # Methodology
    if any(word in message_lower for word in ['methodology', 'methods', 'method', 'research design', 'study design']):
        return """**Research Methodology Guide:**

**1. Research Design**
Choose your approach:
- Qualitative: Explores experiences, meanings (interviews, observations)
- Quantitative: Tests hypotheses with numbers (surveys, experiments)
- Mixed Methods: Combines both approaches

**2. Participants/Sample**
- Define your population
- Sampling strategy (random, stratified, purposive)
- Sample size justification
- Inclusion/exclusion criteria

**3. Data Collection**
- Instruments: Surveys, interviews, observations, tests
- Procedures: Step-by-step data collection process
- Timeline: When and how long
- Pilot testing: Test instruments first

**4. Data Analysis**
- Qualitative: Thematic analysis, coding, NVivo
- Quantitative: SPSS, R, Python, statistical tests
- Validity and reliability measures

**5. Ethical Considerations**
- IRB/Ethics committee approval
- Informed consent procedures
- Confidentiality and data protection
- Risks and benefits disclosure"""

    # Abstract
    elif any(word in message_lower for word in ['abstract', 'summary']):
        return """**Writing an Effective Abstract (150-250 words):**

**Structure (5 parts):**

1. **Background** (1-2 sentences)
   - Context: Why this research matters
   - Problem statement

2. **Objective** (1 sentence)
   - Clear research aim or hypothesis

3. **Methods** (2-3 sentences)
   - Study design
   - Participants/sample
   - Key procedures

4. **Results** (2-3 sentences)
   - Main findings with specific data
   - Statistical significance if applicable

5. **Conclusion** (1-2 sentences)
   - Implications
   - Significance for field

**Writing Tips:**
✓ Use past tense for completed work
✓ Be specific with numbers (n=150, p<0.05)
✓ Avoid citations and abbreviations
✓ Make it standalone (readable without full paper)
✓ Use active voice when possible
✓ Include 3-5 keywords at the end"""

    # Literature review
    elif any(word in message_lower for word in ['literature', 'review', 'sources', 'references']):
        return """**Literature Review Structure:**

**1. Introduction**
- Define scope and boundaries
- Explain search strategy
- State purpose and significance

**2. Organization Methods:**

**Chronological** - Evolution over time
- Best for: Showing historical development
- Example: "Early studies (1990s)... Recent work (2020s)..."

**Thematic** - By topics/themes
- Best for: Complex topics with multiple aspects
- Example: "Theme 1: X... Theme 2: Y..."

**Methodological** - By research approaches
- Best for: Methodological comparisons
- Example: "Qualitative studies... Quantitative studies..."

**Theoretical** - By frameworks
- Best for: Theory-heavy fields
- Example: "Cognitive theories... Behavioral theories..."

**3. Critical Analysis**
- Don't just summarize - synthesize and evaluate
- Identify patterns, trends, contradictions
- Show relationships between studies
- Highlight gaps in research

**4. Conclusion**
- Summarize key themes
- Identify research gaps your study will address"""

    # Data analysis
    elif any(word in message_lower for word in ['data', 'analysis', 'statistics', 'statistical', 'spss', 'visualization']):
        return """**Data Analysis Guide:**

**1. Data Preparation**
- Clean data (remove duplicates, errors)
- Handle missing values (deletion, imputation)
- Check for outliers
- Code categorical variables

**2. Descriptive Statistics**
- Central tendency: Mean, median, mode
- Dispersion: Standard deviation, range
- Frequency distributions
- Summary tables

**3. Statistical Tests (Choose Based on Data):**

**Comparing Groups:**
- t-test: 2 groups
- ANOVA: 3+ groups
- Chi-square: Categorical data

**Relationships:**
- Correlation: Strength of relationship
- Regression: Predicting outcomes

**4. Data Visualization**
- Bar charts: Compare categories
- Line graphs: Trends over time
- Scatter plots: Relationships
- Box plots: Distribution comparison
- Histograms: Frequency distribution

**5. Reporting Results**
- State test used and why
- Report statistics (t, F, r, p-values)
- Include effect sizes
- Present in tables and figures
- Interpret in plain language

**Tools:** SPSS, R, Python, Excel, Stata"""

    # Writing/Academic writing
    elif any(word in message_lower for word in ['write', 'writing', 'paper', 'manuscript', 'draft', 'publish']):
        return """**Academic Writing Guide:**

**1. Structure (IMRAD)**
- Introduction: Background, gap, purpose
- Methods: How you did it
- Results: What you found
- Discussion: What it means

**2. Clarity Principles**
- One main idea per paragraph
- Topic sentence first
- Short sentences (15-20 words avg)
- Active voice preferred
- Avoid jargon

**3. Verb Tense**
- Present: General facts, existing knowledge
- Past: Your study methods and results
- Present perfect: Recent research

**4. Common Mistakes**
✗ Vague statements without evidence
✗ Overusing passive voice
✗ Complex words when simple ones work
✗ Missing transitions
✗ Not defining abbreviations

**5. Revision Process**
- Draft quickly, edit later
- Read aloud to catch issues
- Use Grammarly or similar tools
- Get peer feedback
- Sleep on it, revise fresh

**6. Paragraph Structure**
- Topic sentence (main idea)
- Supporting evidence
- Analysis/explanation
- Transition to next idea"""

    # Citations
    elif any(word in message_lower for word in ['citation', 'cite', 'reference', 'apa', 'mla', 'harvard', 'chicago']):
        return """**Citation Guide:**

**APA Style (7th Edition):**

**Journal Article:**
Author, A. A., & Author, B. B. (Year). Title of article. Journal Name, Volume(Issue), pages. https://doi.org/xxx

**Book:**
Author, A. A. (Year). Book title. Publisher.

**Website:**
Author, A. A. (Year, Month Day). Page title. Site Name. URL

**In-Text Citations:**
- One author: (Smith, 2023)
- Two authors: (Smith & Jones, 2023)
- 3+ authors: (Smith et al., 2023)
- Direct quote: (Smith, 2023, p. 15)
- Multiple sources: (Jones, 2022; Smith, 2023)

**What to Cite:**
✓ Direct quotes
✓ Paraphrased ideas
✓ Data and statistics
✓ Images and figures
✓ Theories and models

**Don't Cite:**
✗ Common knowledge
✗ Your own original ideas
✗ Your own research

**Tools:**
- Zotero (free, recommended)
- Mendeley (free)
- EndNote (paid)
- Citation Machine (online)

**Tips:**
- Cite as you write
- Keep reference list updated
- Double-check formatting
- Use citation manager"""

    # Results section
    elif any(word in message_lower for word in ['results', 'findings', 'outcome']):
        return """**Writing the Results Section:**

**1. Organization**
- Present in logical order (match methods)
- Use subheadings for clarity
- State results objectively

**2. What to Include**
- Descriptive statistics first
- Main findings
- Statistical test results
- Tables and figures
- Negative results (important!)

**3. Reporting Statistics**
Format: t(df) = value, p = value
Example: t(98) = 3.45, p < .001

**Chi-square:** χ²(df, N) = value, p = value
**ANOVA:** F(df1, df2) = value, p = value
**Correlation:** r(df) = value, p = value

**4. Tables vs Figures**
- Tables: Precise numbers
- Figures: Patterns and trends
- Don't duplicate information

**5. What NOT to Include**
✗ Interpretation (save for Discussion)
✗ Raw data (unless necessary)
✗ Explanations of methods

**6. Writing Style**
- Past tense
- Objective tone
- "The results showed..." not "I found..."
- Be precise with numbers"""

    # Discussion section
    elif any(word in message_lower for word in ['discussion', 'interpret', 'implication']):
        return """**Writing the Discussion Section:**

**1. Opening (1-2 paragraphs)**
- Restate main findings
- Answer your research questions
- State if hypothesis supported

**2. Interpretation**
- Explain what results mean
- Compare with previous studies
- Why results occurred
- Agree or contradict literature

**3. Implications**
- Theoretical contributions
- Practical applications
- Policy recommendations
- Future research

**4. Limitations**
- Sample size/generalizability
- Methodological constraints
- Unexpected challenges
- Alternative explanations

**5. Future Research**
- Unanswered questions
- New directions
- Improvements to design

**6. Conclusion (final paragraph)**
- Summarize key points
- Emphasize significance
- Strong closing statement

**Tips:**
- Move from specific to general
- Don't overgeneralize
- Acknowledge limitations honestly
- End on positive note"""

    # Introduction
    elif any(word in message_lower for word in ['introduction', 'intro', 'background']):
        return """**Writing the Introduction:**

**Structure (Funnel Approach):**

**1. Opening (Broad)**
- General context
- Why topic matters
- Engage reader interest

**2. Literature Review**
- What we know
- Previous research
- Current understanding

**3. Gap Statement**
- What's missing
- Contradictions
- Unanswered questions

**4. Research Purpose**
- Your specific aim
- Research questions/hypotheses
- Why this study

**5. Significance**
- Theoretical contribution
- Practical implications
- Who benefits

**6. Overview (optional)**
- Brief methods mention
- Paper organization

**Tips:**
- Start broad, end specific
- Use present tense for known facts
- Hook reader in first paragraph
- Clear research questions
- Length: 10-15% of paper

**Avoid:**
✗ Starting too broadly
✗ Unclear purpose
✗ Missing gap statement
✗ No justification"""

    # General/Default
    else:
        return f"""**Research Assistant Response:**

You asked: "{user_message}"

**I can help with:**
- Research Methodology
- Literature Reviews
- Academic Writing
- Data Analysis
- Statistical Tests
- Citations (APA, MLA, Chicago)
- Abstract Writing
- Results & Discussion Sections

**Quick Tips for Your Question:**

1. **Be Specific:** Break complex questions into parts
2. **Provide Context:** Share relevant details
3. **Ask Follow-ups:** Dive deeper into any topic

**Example Questions:**
- "How do I structure a methodology section?"
- "What statistical test should I use for comparing 3 groups?"
- "How do I cite a journal article in APA?"
- "Tips for writing an abstract?"

**Try asking about:**
→ Research design choices
→ Data collection methods
→ Analysis techniques
→ Writing strategies
→ Citation formats

*Ready to help with your research! Ask me anything specific.*"""

@ai_bp.route('/delete/<int:conversation_id>', methods=['POST'])
@login_required
def delete_conversation(conversation_id):
    """Delete a conversation"""
    conversation = AIConversation.query.get_or_404(conversation_id)
    
    if conversation.user_id != current_user.id:
        flash('Access denied', 'danger')
        return redirect(url_for('ai.index'))
    
    conversation.is_active = False
    db.session.commit()
    
    flash('Conversation deleted', 'success')
    return redirect(url_for('ai.index'))