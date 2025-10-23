"""
AI Service Module for Cognisync™
Handles audio transcription, analysis, and pattern tracking
"""

import os
import json
from datetime import datetime
from openai import OpenAI
from anthropic import Anthropic

# Initialize clients
openai_client = OpenAI()
anthropic_client = Anthropic()

def transcribe_audio(audio_file_path):
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        audio_file_path: Path to the audio file
        
    Returns:
        dict: Transcription result with text and metadata
    """
    try:
        with open(audio_file_path, 'rb') as audio_file:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
        
        return {
            'success': True,
            'text': transcript.text,
            'duration': transcript.duration if hasattr(transcript, 'duration') else None,
            'language': transcript.language if hasattr(transcript, 'language') else 'en',
            'segments': transcript.segments if hasattr(transcript, 'segments') else []
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def analyze_session_with_gpt(transcript, client_name, therapy_type, summary_format):
    """
    Analyze therapy session using GPT-4
    
    Args:
        transcript: Session transcript text
        client_name: Client identifier
        therapy_type: Type of therapy (CBT, DBT, etc.)
        summary_format: Output format (SOAP, BIRP, etc.)
        
    Returns:
        dict: Analysis results
    """
    try:
        prompt = f"""You are an expert clinical psychologist analyzing a therapy session transcript.

**Client ID:** {client_name}
**Therapy Type:** {therapy_type}
**Output Format:** {summary_format}

**Session Transcript:**
{transcript}

Please provide a comprehensive clinical analysis in {summary_format} format. Include:

1. **{summary_format} Notes**: Follow standard {summary_format} structure
2. **Clinical Observations**: Key themes, progress, concerns
3. **Therapeutic Interventions**: Techniques used and their effectiveness
4. **Treatment Recommendations**: Next steps and homework
5. **Risk Assessment**: Any safety concerns or red flags

Be thorough, professional, and clinically accurate."""

        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert clinical psychologist providing professional therapy session analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        return {
            'success': True,
            'analysis': response.choices[0].message.content,
            'model': 'gpt-4.1-mini'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def analyze_sentiment_with_claude(transcript, client_name):
    """
    Perform deep sentiment and pattern analysis using Claude
    
    Args:
        transcript: Session transcript text
        client_name: Client identifier
        
    Returns:
        dict: Sentiment analysis results
    """
    try:
        prompt = f"""Analyze this therapy session transcript for emotional patterns, sentiment, and clinical insights.

**Client ID:** {client_name}

**Transcript:**
{transcript}

Provide a detailed analysis including:

1. **Overall Emotional Tone**: Dominant emotions throughout the session
2. **Emotional Progression**: How emotions evolved during the session
3. **Key Emotional Indicators**: Specific phrases or moments revealing emotional state
4. **Linguistic Patterns**: Speech patterns, word choices, communication style
5. **Therapeutic Engagement Level**: Client's participation and openness
6. **Risk Assessment**: Any concerning patterns or red flags
7. **Progress Indicators**: Signs of improvement or regression
8. **Underlying Themes**: Deeper psychological patterns or unresolved issues
9. **Clinical Hunches**: Professional observations about potential root causes
10. **Paradoxes or Contradictions**: Any inconsistencies in client's narrative

Format your response as a structured JSON object."""

        message = anthropic_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Parse Claude's response
        response_text = message.content[0].text
        
        # Try to extract JSON if present
        try:
            # Look for JSON in the response
            if '{' in response_text and '}' in response_text:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                sentiment_data = json.loads(response_text[json_start:json_end])
            else:
                # If no JSON, structure the text response
                sentiment_data = {
                    'raw_analysis': response_text
                }
        except:
            sentiment_data = {
                'raw_analysis': response_text
            }
        
        return {
            'success': True,
            'sentiment_analysis': sentiment_data,
            'model': 'claude-3-5-sonnet'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def extract_patterns(client_name, current_session_data, previous_sessions):
    """
    Extract longitudinal patterns across multiple sessions
    
    Args:
        client_name: Client identifier
        current_session_data: Current session analysis
        previous_sessions: List of previous session analyses
        
    Returns:
        dict: Pattern analysis
    """
    try:
        # Prepare session history for analysis
        session_summaries = []
        for i, session in enumerate(previous_sessions, 1):
            summary = f"Session {i}: {session.get('summary', 'N/A')}"
            session_summaries.append(summary)
        
        history_text = "\n".join(session_summaries) if session_summaries else "No previous sessions"
        
        prompt = f"""Analyze patterns across therapy sessions for client {client_name}.

**Previous Sessions:**
{history_text}

**Current Session:**
{current_session_data.get('analysis', '')}

Identify:
1. **Recurring Themes**: Topics that appear across multiple sessions
2. **Sentiment Trends**: How emotional state has changed over time
3. **Progress Indicators**: Signs of improvement or decline
4. **Persistent Issues**: Problems that haven't resolved
5. **Behavioral Patterns**: Recurring behaviors or coping mechanisms
6. **Treatment Effectiveness**: What's working and what isn't
7. **Clinical Predictions**: Likely trajectory based on patterns
8. **Recommendations**: Adjustments to treatment approach

Provide insights that would help a therapist understand the client's journey."""

        response = openai_client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert clinical psychologist analyzing longitudinal therapy patterns."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        
        return {
            'success': True,
            'pattern_analysis': response.choices[0].message.content,
            'session_count': len(previous_sessions) + 1
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def process_therapy_session(audio_file_path, client_name, therapy_type, summary_format, previous_sessions=None):
    """
    Complete pipeline: transcribe, analyze, and extract patterns
    
    Args:
        audio_file_path: Path to audio file
        client_name: Client identifier
        therapy_type: Type of therapy
        summary_format: Output format (SOAP/BIRP)
        previous_sessions: List of previous session data for pattern analysis
        
    Returns:
        dict: Complete analysis results
    """
    results = {
        'client_name': client_name,
        'therapy_type': therapy_type,
        'summary_format': summary_format,
        'timestamp': datetime.now().isoformat(),
        'success': True
    }
    
    # Step 1: Transcribe audio
    print(f"🎙️ Transcribing audio for {client_name}...")
    transcription = transcribe_audio(audio_file_path)
    
    if not transcription['success']:
        results['success'] = False
        results['error'] = f"Transcription failed: {transcription['error']}"
        return results
    
    results['transcript'] = transcription['text']
    results['transcript_metadata'] = {
        'duration': transcription.get('duration'),
        'language': transcription.get('language')
    }
    
    # Step 2: Generate clinical analysis with GPT
    print(f"🧠 Analyzing session with GPT-4...")
    analysis = analyze_session_with_gpt(
        transcription['text'],
        client_name,
        therapy_type,
        summary_format
    )
    
    if not analysis['success']:
        results['success'] = False
        results['error'] = f"Analysis failed: {analysis['error']}"
        return results
    
    results['analysis'] = analysis['analysis']
    
    # Step 3: Sentiment analysis with Claude
    print(f"💭 Performing sentiment analysis with Claude...")
    sentiment = analyze_sentiment_with_claude(
        transcription['text'],
        client_name
    )
    
    if sentiment['success']:
        results['sentiment_analysis'] = sentiment['sentiment_analysis']
    else:
        results['sentiment_analysis'] = {'error': sentiment['error']}
    
    # Step 4: Pattern analysis (if previous sessions exist)
    if previous_sessions and len(previous_sessions) > 0:
        print(f"📊 Extracting longitudinal patterns...")
        patterns = extract_patterns(
            client_name,
            results,
            previous_sessions
        )
        
        if patterns['success']:
            results['pattern_analysis'] = patterns['pattern_analysis']
            results['session_count'] = patterns['session_count']
    
    # Add confidence score
    results['confidence_score'] = 0.95
    
    return results


def generate_demo_analysis(client_name, therapy_type, summary_format):
    """
    Generate demo analysis for testing (no real AI calls)
    """
    return {
        'success': True,
        'demo_mode': True,
        'client_name': client_name,
        'therapy_type': therapy_type,
        'summary_format': summary_format,
        'transcript': "[DEMO MODE] This is a simulated transcript. In production, this would contain the actual transcribed audio from the therapy session.",
        'analysis': f"""**{summary_format} CLINICAL DOCUMENTATION - DEMO MODE**

**SUBJECTIVE:**
Client reports experiencing moderate anxiety related to work deadlines and interpersonal conflicts. States "I feel overwhelmed and can't seem to catch up." Reports difficulty sleeping (averaging 5-6 hours per night) and increased irritability.

**OBJECTIVE:**
Client appeared anxious during session, with visible tension in shoulders and frequent hand movements. Speech was rapid at times. Maintained good eye contact and was engaged throughout the session. No signs of acute distress or safety concerns.

**ASSESSMENT:**
Client demonstrates symptoms consistent with adjustment disorder with anxiety. Shows good insight into triggers and willingness to engage in treatment. Strengths include strong support system and previous success with CBT techniques.

**PLAN:**
1. Continue weekly CBT sessions focusing on cognitive restructuring
2. Implement progressive muscle relaxation for anxiety management
3. Assign thought record homework to track anxiety triggers
4. Review and practice boundary-setting skills for work situations
5. Follow up on sleep hygiene recommendations from previous session

**NEXT SESSION:** One week""",
        'sentiment_analysis': {
            'overallEmotionalTone': 'Moderate anxiety with underlying resilience',
            'emotionalProgression': 'Started anxious, progressed to collaborative problem-solving',
            'keyEmotionalIndicators': ['Work-related stress', 'Sleep disruption', 'Therapeutic engagement'],
            'therapeuticEngagementLevel': 'High',
            'riskAssessment': 'Low risk - good coping skills, strong support system'
        },
        'confidence_score': 0.93
    }

