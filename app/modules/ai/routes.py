# app/modules/ai/routes.py

from flask import request, jsonify, render_template
from flask_login import login_required, current_user
from app.modules.ai import ai_bp
from app.modules.ai import mock_ai
import os
import re
import requests

GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyBragQglok_Nre-S_zJmUMMVgZg4aafBTE')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent'
WORD_RE = re.compile(r"\b[\w'-]+\b")

def _count_words(text):
    return len(WORD_RE.findall(text or ''))

def _word_range(target_words):
    tolerance = max(12, int(target_words * 0.08))
    return max(1, target_words - tolerance), target_words + tolerance

def _trim_to_words(text, max_words):
    words = re.findall(r'\S+', text or '')
    if len(words) <= max_words:
        return text
    return ' '.join(words[:max_words]).strip()

def _expand_to_words(text, target_words, topic):
    current = _count_words(text)
    if current >= target_words:
        return text
    filler = (
        f' This discussion remains focused on {topic} and highlights practical implications, '
        f'methodological considerations, and evidence-based interpretation for real-world use.'
    )
    expanded = (text or '').strip()
    while _count_words(expanded) < target_words:
        expanded += filler
    return expanded

def _enforce_word_target(result, *, target_words, content_type, tone, topic):
    low, high = _word_range(target_words)
    current = _count_words(result)
    if low <= current <= high:
        return result, current
    try:
        revision_prompt = (
            f'Rewrite the following content to match a strict target length.\n\n'
            f'Topic: {topic}\n'
            f'Content type: {content_type}\n'
            f'Tone: {tone}\n'
            f'Target words: {target_words}\n'
            f'Allowed range: {low}-{high} words\n'
            f'Current words: {current}\n\n'
            'Rules:\n'
            '1. Keep the same meaning and structure as much as possible.\n'
            '2. Keep markdown headings if present.\n'
            '3. Do not add placeholder text.\n'
            '4. Output only the revised final content.\n\n'
            f'CONTENT TO REWRITE:\n{result}'
        )
        revised = call_gemini(
            revision_prompt,
            system=(
                'You are an expert editor who rewrites text to meet strict word limits while preserving quality. '
                'Return only revised content.'
            ),
            content_type=content_type,
            use_fallback=False,
        )
        revised_count = _count_words(revised)
        if low <= revised_count <= high:
            return revised, revised_count
        result = revised
        current = revised_count
    except Exception:
        pass
    if current > high:
        result = _trim_to_words(result, target_words)
    else:
        result = _expand_to_words(result, target_words, topic)
        result = _trim_to_words(result, target_words)
    return result, _count_words(result)

def call_gemini(prompt, system=None, content_type='section', use_fallback=True, history=None):
    if not GEMINI_API_KEY:
        if use_fallback:
            return mock_ai.chat_response(prompt)
        raise Exception('AI service not configured.')

    contents = []
    if history:
        for turn in history[-10:]:
            role = turn.get('role', 'user')
            content_text = turn.get('content', '').strip()
            if content_text:
                gemini_role = 'model' if role == 'assistant' else 'user'
                contents.append({'role': gemini_role, 'parts': [{'text': content_text}]})

    full_prompt = f'{system}\n\n{prompt}' if system and not contents else prompt
    contents.append({'role': 'user', 'parts': [{'text': full_prompt}]})

    payload = {
        'contents': contents,
        'generationConfig': {
            'temperature': 0.8,
            'topK': 40,
            'topP': 0.95,
            'maxOutputTokens': 8192,
        },
        'safetySettings': [
            {'category': 'HARM_CATEGORY_HARASSMENT', 'threshold': 'BLOCK_NONE'},
            {'category': 'HARM_CATEGORY_HATE_SPEECH', 'threshold': 'BLOCK_NONE'},
            {'category': 'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'threshold': 'BLOCK_MEDIUM_AND_ABOVE'},
            {'category': 'HARM_CATEGORY_DANGEROUS_CONTENT', 'threshold': 'BLOCK_NONE'},
        ]
    }

    try:
        resp = requests.post(
            f'{GEMINI_API_URL}?key={GEMINI_API_KEY}',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        if resp.status_code == 429:
            if use_fallback:
                return mock_ai.chat_response(prompt)
            raise Exception('API quota exceeded.')
        if resp.status_code in (401, 403):
            if use_fallback:
                return mock_ai.chat_response(prompt)
            raise Exception('Invalid API key.')
        if resp.status_code >= 500:
            if use_fallback:
                return mock_ai.chat_response(prompt)
            raise Exception(f'Server error {resp.status_code}.')
        resp.raise_for_status()
        return resp.json()['candidates'][0]['content']['parts'][0]['text']
    except requests.exceptions.Timeout:
        if use_fallback:
            return mock_ai.chat_response(prompt)
        raise Exception('Request timed out.')
    except requests.exceptions.ConnectionError:
        if use_fallback:
            return mock_ai.chat_response(prompt)
        raise Exception('Connection failed.')
    except Exception:
        if use_fallback:
            return mock_ai.chat_response(prompt)
        raise

# AI ASSISTANT PAGE

@ai_bp.route('/')
@login_required
def assistant():
    return render_template('ai/assistant.html', user=current_user)

@ai_bp.route('/content-creation')
@login_required
def content_creation():
    return render_template('ai/content_creation.html', user=current_user)

@ai_bp.route('/generate-content', methods=['POST'])
@login_required
def generate_content():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '').strip()
    content_type = data.get('content_type', 'section').strip().lower()
    tone = data.get('tone', 'academic').strip().lower()
    try:
        word_count = int(data.get('word_count', 700))
    except (TypeError, ValueError):
        word_count = 700
    word_count = max(20, min(word_count, 5000))

    if not prompt:
        return jsonify({'error': 'Prompt is required.'}), 400

    # ── Extract clean topic from user prompt ──────────────────────────────────
    user_topic = prompt.strip()
    # Strip common action prefixes so mock AI gets just the topic
    _topic_prefixes = [
        'write a comprehensive research paper on', 'write a research paper on',
        'write a paper on', 'write an article on', 'write an essay on',
        'generate a paper on', 'create a paper on', 'draft a paper on',
        'write a section on', 'write about', 'write on', 'generate content about',
        'create content on', 'write a research article on', 'paper on', 'article on',
    ]
    _lower_prompt = prompt.lower()
    for _prefix in _topic_prefixes:
        if _lower_prompt.startswith(_prefix):
            user_topic = prompt[len(_prefix):].strip()
            break
        elif _prefix in _lower_prompt:
            _idx = _lower_prompt.find(_prefix) + len(_prefix)
            _candidate = prompt[_idx:].strip()
            if len(_candidate) >= 3:
                user_topic = _candidate
                break
    # Remove trailing instructions like "in 500 words", "with academic tone"
    import re as _re2
    user_topic = _re2.sub(
        r'(?i)\s*(in \d+ words?|with \w+ tone|target:.*|approximately.*|around.*)\s*$',
        '', user_topic
    ).strip()
    if not user_topic or len(user_topic) < 3:
        user_topic = prompt.strip()
    # ─────────────────────────────────────────────────────────────────────────

    low_words, high_words = _word_range(word_count)

    if content_type == 'section':
        if word_count < 280:
            section_mode = 'Keep each section concise (1 short paragraph each). Use only 3 key findings due to the small word limit.'
        else:
            section_mode = 'Develop each section with evidence while staying within target length.'

        generation_prompt = (
            f'Write a complete academic research article about: {user_topic}\n\n'
            'Your article must have exactly five sections in this order. '
            'Start each section with its header in bold markdown.\n\n'
            f'**TITLE:**\n'
            f'Create a concise formal academic title about {user_topic}. Keep title under 14 words.\n\n'
            f'**ABSTRACT**\n'
            f'Describe background, objective, method, findings, and conclusion for {user_topic}.\n\n'
            f'**INTRODUCTION**\n'
            f'Explain context, current research, key gap, and paper objectives related to {user_topic}.\n\n'
            f'**KEY FINDINGS**\n'
            f'List evidence-based findings specifically about {user_topic}. Use numbered points.\n\n'
            f'**CONCLUSION**\n'
            f'Summarize implications, limitations, and future research on {user_topic}.\n\n'
            f'{section_mode}\n'
            f'CRITICAL RULES: Write every sentence specifically about {user_topic}. '
            f'Never write placeholder text like {{topic}} or {{Topic}}. '
            f'For tone use: {tone}. '
            f'Target total length: {word_count} words (acceptable range: {low_words}-{high_words}).'
        )
        system_prompt = (
            'You are a world-class academic researcher. You write detailed, factual, specific research articles. '
            'You always write the actual topic name in your articles and never use placeholders. '
            'Every sentence must be about the specific subject the user asked about. '
            'Respect requested word limits.'
        )
    else:
        section_labels = {
            'abstract': 'ABSTRACT',
            'introduction': 'INTRODUCTION',
            'literature_review': 'LITERATURE REVIEW',
            'methodology': 'METHODOLOGY',
            'results_discussion': 'RESULTS & DISCUSSION',
            'conclusion': 'CONCLUSION',
        }
        label = section_labels.get(content_type, content_type.replace('_', ' ').upper())

        section_instructions = {
            'abstract': (
                f'Write a professional academic abstract about {user_topic}. '
                f'Cover: why {user_topic} matters (background), objective, methodology, results, and conclusion. '
                'Write in third person and avoid placeholder text.'
            ),
            'introduction': (
                f'Write a strong research paper introduction about {user_topic}. '
                f'Cover: historical background, current research landscape, key gap, and study objectives on {user_topic}.'
            ),
            'literature_review': (
                f'Write a literature review about {user_topic}. '
                f'Cover: foundational theories, key studies, major themes, research gaps, and your contribution context.'
            ),
            'methodology': (
                f'Write a methodology section for a study on {user_topic}. '
                'Cover: design, data sources/participants, instruments, data collection process, and analysis approach.'
            ),
            'results_discussion': (
                f'Write a results and discussion section for {user_topic}. '
                'Cover: key findings, interpretation, comparison with prior research, and practical/theoretical implications.'
            ),
            'conclusion': (
                f'Write a conclusion for a research paper on {user_topic}. '
                'Cover: key insights, implications, limitations, and future research directions.'
            ),
        }

        instruction = section_instructions.get(
            content_type,
            f'Write the {label} section of a research paper about {user_topic} in {word_count} words with {tone} tone.'
        )

        generation_prompt = (
            f'{instruction}\n\n'
            f'Start your response with the section header in bold: **{label}**\n'
            f'Tone: {tone}. Target length: {word_count} words (acceptable range: {low_words}-{high_words}).\n'
            f'CRITICAL: Every sentence must be specifically about {user_topic}. '
            f'Never write placeholder text. '
            f'Do not exceed {high_words} words and do not go below {low_words} words.'
        )
        system_prompt = (
            'You are an expert academic research writer. '
            'You write specific, factual content about the topic you are given. '
            'You always write the actual topic name and never use placeholders. '
            'Respect requested word limits.'
        )

    try:
        raw_result = call_gemini(generation_prompt, system=system_prompt, content_type=content_type, use_fallback=False)
        result, actual_word_count = _enforce_word_target(raw_result, target_words=word_count, content_type=content_type, tone=tone, topic=user_topic)
    except Exception:
        # Pass the clean topic (not the full prompt) to mock AI
        if content_type == 'section':
            fallback_result = mock_ai.generate_full_article(user_topic)
        else:
            fallback_result = mock_ai.generate_content(content_type, user_topic, tone, word_count)
        result, actual_word_count = _enforce_word_target(fallback_result, target_words=word_count, content_type=content_type, tone=tone, topic=user_topic)

    return jsonify({'result': result, 'target_words': word_count, 'actual_word_count': actual_word_count, 'within_target': _word_range(word_count)[0] <= actual_word_count <= _word_range(word_count)[1]})

    if content_type == 'section':
        if word_count < 280:
            section_mode = 'Keep each section concise (1 short paragraph each). Use only 3 key findings due to the small word limit.'
        else:
            section_mode = 'Develop each section with evidence while staying within target length.'

        generation_prompt = (
            f'Write a complete academic research article about: {user_topic}\n\n'
            'Your article must have exactly five sections in this order. '
            'Start each section with its header in bold markdown.\n\n'
            f'**TITLE:**\n'
            f'Create a concise formal academic title about {user_topic}. Keep title under 14 words.\n\n'
            f'**ABSTRACT**\n'
            f'Describe background, objective, method, findings, and conclusion for {user_topic}.\n\n'
            f'**INTRODUCTION**\n'
            f'Explain context, current research, key gap, and paper objectives related to {user_topic}.\n\n'
            f'**KEY FINDINGS**\n'
            f'List evidence-based findings specifically about {user_topic}. Use numbered points.\n\n'
            f'**CONCLUSION**\n'
            f'Summarize implications, limitations, and future research on {user_topic}.\n\n'
            f'{section_mode}\n'
            f'CRITICAL RULES: Write every sentence specifically about {user_topic}. '
            f'Never write placeholder text like {{topic}} or {{Topic}}. '
            f'For tone use: {tone}. '
            f'Target total length: {word_count} words (acceptable range: {low_words}-{high_words}).'
        )
        system_prompt = (
            'You are a world-class academic researcher. You write detailed, factual, specific research articles. '
            'You always write the actual topic name in your articles and never use placeholders. '
            'Every sentence must be about the specific subject the user asked about. '
            'Respect requested word limits.'
        )
    else:
        section_labels = {
            'abstract': 'ABSTRACT',
            'introduction': 'INTRODUCTION',
            'literature_review': 'LITERATURE REVIEW',
            'methodology': 'METHODOLOGY',
            'results_discussion': 'RESULTS & DISCUSSION',
            'conclusion': 'CONCLUSION',
        }
        label = section_labels.get(content_type, content_type.replace('_', ' ').upper())

        section_instructions = {
            'abstract': (
                f'Write a professional academic abstract about {user_topic}. '
                f'Cover: why {user_topic} matters (background), objective, methodology, results, and conclusion. '
                'Write in third person and avoid placeholder text.'
            ),
            'introduction': (
                f'Write a strong research paper introduction about {user_topic}. '
                f'Cover: historical background, current research landscape, key gap, and study objectives on {user_topic}.'
            ),
            'literature_review': (
                f'Write a literature review about {user_topic}. '
                f'Cover: foundational theories, key studies, major themes, research gaps, and your contribution context.'
            ),
            'methodology': (
                f'Write a methodology section for a study on {user_topic}. '
                'Cover: design, data sources/participants, instruments, data collection process, and analysis approach.'
            ),
            'results_discussion': (
                f'Write a results and discussion section for {user_topic}. '
                'Cover: key findings, interpretation, comparison with prior research, and practical/theoretical implications.'
            ),
            'conclusion': (
                f'Write a conclusion for a research paper on {user_topic}. '
                'Cover: key insights, implications, limitations, and future research directions.'
            ),
        }

        instruction = section_instructions.get(
            content_type,
            f'Write the {label} section of a research paper about {user_topic} in {word_count} words with {tone} tone.'
        )

        generation_prompt = (
            f'{instruction}\n\n'
            f'Start your response with the section header in bold: **{label}**\n'
            f'Tone: {tone}. Target length: {word_count} words (acceptable range: {low_words}-{high_words}).\n'
            f'CRITICAL: Every sentence must be specifically about {user_topic}. '
            f'Never write placeholder text. '
            f'Do not exceed {high_words} words and do not go below {low_words} words.'
        )
        system_prompt = (
            'You are an expert academic research writer. '
            'You write specific, factual content about the topic you are given. '
            'You always write the actual topic name and never use placeholders. '
            'Respect requested word limits.'
        )

    try:
        raw_result = call_gemini(generation_prompt, system=system_prompt, content_type=content_type, use_fallback=False)
        result, actual_word_count = _enforce_word_target(raw_result, target_words=word_count, content_type=content_type, tone=tone, topic=user_topic)
    except Exception:
        if content_type == 'section':
            fallback_result = mock_ai.generate_full_article(prompt)
        else:
            fallback_result = mock_ai.generate_content(content_type, prompt, tone, word_count)
        result, actual_word_count = _enforce_word_target(fallback_result, target_words=word_count, content_type=content_type, tone=tone, topic=user_topic)

    return jsonify({'result': result, 'target_words': word_count, 'actual_word_count': actual_word_count, 'within_target': _word_range(word_count)[0] <= actual_word_count <= _word_range(word_count)[1]})

@ai_bp.route('/generate-abstract', methods=['POST'])
@login_required
def generate_abstract():
    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    category = data.get('category', '').strip()
    keywords = data.get('keywords', '').strip()

    if not title:
        return jsonify({'error': 'Article title is required.'}), 400

    prompt = (
        f'Write a professional academic abstract for the following research article.\n\n'
        f'Title: {title}\n'
        + (f'Category: {category}\n' if category else '')
        + (f'Keywords: {keywords}\n' if keywords else '')
        + '\nThe abstract should be 150-250 words, written in third person, covering: background/motivation, '
        'objective, methodology, results, and conclusion. Output only the abstract text, no extra commentary.'
    )
    try:
        result = call_gemini(prompt, system='You are an expert academic writer specializing in research abstracts.', content_type='abstract', use_fallback=False)
        return jsonify({'result': result})
    except Exception:
        result = mock_ai.generate_abstract(title, category, keywords)
        return jsonify({'result': result})

# KEYWORD EXTRACTOR

@ai_bp.route('/extract-keywords', methods=['POST'])
@login_required
def extract_keywords():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Article text is required.'}), 400

    prompt = (
        f'Extract 8-12 relevant academic keywords from the following research text.\n\n'
        f'Text:\n{content}\n\n'
        'Return only the keywords as a numbered list, one per line. No explanations.'
    )
    try:
        result = call_gemini(prompt, system='You are an expert in academic publishing and keyword extraction.', use_fallback=False)
        return jsonify({'result': result})
    except Exception:
        result = mock_ai.extract_keywords(content)
        return jsonify({'result': result})

# CITATION FORMATTER

@ai_bp.route('/format-citation', methods=['POST'])
@login_required
def format_citation():
    data = request.get_json(silent=True) or {}
    info = data.get('info', '').strip()
    style = data.get('style', 'APA').strip()

    if not info:
        return jsonify({'error': 'Reference information is required.'}), 400

    prompt = (
        f'Format the following reference information as a {style} citation.\n\n'
        f'Reference details:\n{info}\n\n'
        'Return only the correctly formatted citation. No explanation or extra text.'
    )
    try:
        result = call_gemini(prompt, system='You are an expert in academic citation styles including APA, MLA, Chicago, BibTeX, and Vancouver.', use_fallback=False)
        return jsonify({'result': result})
    except Exception:
        result = mock_ai.format_citation(info, style)
        return jsonify({'result': result})

# GRAMMAR & STYLE CHECK

@ai_bp.route('/grammar-check', methods=['POST'])
@login_required
def grammar_check():
    data = request.get_json(silent=True) or {}
    content = data.get('content', '').strip()

    if not content:
        return jsonify({'error': 'Text is required.'}), 400

    prompt = (
        f'Review the following academic text for grammar, clarity, and writing style.\n\n'
        f'Text:\n{content}\n\n'
        'Provide:\n'
        '1. Overall assessment (1-2 sentences)\n'
        '2. Grammar issues found (list each with correction)\n'
        '3. Style/clarity suggestions\n'
        '4. Improved version of the text\n\n'
        'Be concise and constructive.'
    )
    try:
        result = call_gemini(prompt, system='You are an expert academic editor specializing in grammar, style, and clarity.', use_fallback=False)
        return jsonify({'result': result})
    except Exception:
        result = mock_ai.grammar_check(content)
        return jsonify({'result': result})

# AI CHAT — ChatGPT-like multi-turn conversation

@ai_bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    history = data.get('history', [])  # [{role: 'user'/'assistant', content: '...'}]

    if not message:
        return jsonify({'error': 'Message is required.'}), 400

    msg_lower = message.lower()

    SYSTEM_PROMPT = (
        'You are ResearchHub AI — a highly intelligent, versatile assistant trained across all domains '
        'of human knowledge, similar to ChatGPT. You can:\n'
        '- Answer ANY question on ANY topic: science, math, history, coding, law, medicine, economics, '
        'arts, philosophy, culture, sports, technology, and more\n'
        '- Write professional research papers with full academic structure (Title, Abstract, Introduction, '
        'Literature Review, Methodology, Key Findings, Conclusion, References)\n'
        '- Help with research methodology, literature reviews, citations, statistics\n'
        '- Assist with coding, debugging, algorithms, and software engineering\n'
        '- Explain complex concepts clearly at any level (beginner to expert)\n'
        '- Translate, summarize, proofread, and improve writing in any language\n'
        '- Engage in natural, helpful, multi-turn conversations\n\n'
        'Guidelines:\n'
        '- Be thorough, accurate, and helpful\n'
        '- Match your style to the question: casual for casual, technical for technical, formal for academic\n'
        '- For research papers: use full academic structure with proper headings and references\n'
        '- Always give complete, substantive answers\n'
        '- Use markdown formatting to organize responses clearly\n'
        '- If asked in Hindi or any other language, respond in that language\n'
        '- Remember context from conversation history'
    )

    is_research_paper = any(kw in msg_lower for kw in [
        'write a paper', 'write an article', 'research paper', 'research article',
        'write a research', 'generate a paper', 'create a paper', 'draft a paper',
        'write paper on', 'paper on', 'article on', 'essay on', 'write an essay',
    ])

    if is_research_paper:
        topic = message
        for phrase in [
            'write a research paper on', 'write a paper on', 'write an article on',
            'write a research article on', 'generate a paper on', 'create a paper on',
            'draft a paper on', 'paper on', 'article on', 'essay on',
            'write a paper about', 'write about', 'write an article about', 'write an essay on',
        ]:
            if phrase in msg_lower:
                idx = msg_lower.find(phrase) + len(phrase)
                topic = message[idx:].strip()
                break
        if not topic or len(topic) < 3:
            topic = message

        gemini_prompt = (
            f'{SYSTEM_PROMPT}\n\n'
            f'Write a comprehensive, professional research paper on: {topic}\n\n'
            f'Follow this exact academic structure:\n\n'
            f'# [Create a formal academic title about {topic}]\n\n'
            f'## Abstract\n'
            f'Write 200-250 words covering: background and significance of {topic}, research objectives, '
            f'methodology, key findings, and conclusion. Use third-person academic English.\n\n'
            f'## 1. Introduction\n'
            f'Write 5 detailed paragraphs: (1) Historical background of {topic}, '
            f'(2) Current relevance and state of {topic}, '
            f'(3) Key challenges related to {topic}, '
            f'(4) Existing research and gaps on {topic}, '
            f'(5) Objectives and contribution of this paper on {topic}.\n\n'
            f'## 2. Literature Review\n'
            f'Synthesize existing research on {topic}. Cover foundational theories, landmark studies, '
            f'major themes, contradictions, and research gaps.\n\n'
            f'## 3. Methodology\n'
            f'Describe appropriate research methodology for studying {topic}: '
            f'research design, data sources, collection methods, analytical framework.\n\n'
            f'## 4. Key Findings & Discussion\n'
            f'Present 8-10 detailed, evidence-based findings about {topic}. Each finding: '
            f'3-4 sentences with specific data or statistics. Number each finding clearly.\n\n'
            f'## 5. Conclusion\n'
            f'4 paragraphs: key insights, implications, limitations, future research directions for {topic}.\n\n'
            f'## References\n'
            f'List 8-10 realistic academic references in APA format related to {topic}.\n\n'
            f'RULES: Every sentence must specifically discuss {topic}. '
            f'Use formal academic English. Minimum 1500 words. Never use placeholder variables.'
        )
    else:
        gemini_prompt = f'{SYSTEM_PROMPT}\n\nUser: {message}'

    try:
        result = call_gemini(
            gemini_prompt,
            history=history,
            use_fallback=False
        )
        return jsonify({'result': result})
    except Exception:
        result = mock_ai.chat_response(message)
        return jsonify({'result': result})
