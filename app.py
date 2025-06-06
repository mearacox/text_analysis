# app.py
from flask import Flask, request, jsonify, render_template_string, redirect, url_for
from flask_cors import CORS
import nltk
import string
import re
import json
from nltk import word_tokenize
from nltk.probability import FreqDist
from nltk.corpus import stopwords
from collections import Counter

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend-backend communication

# Download required NLTK data (run once)
try:
    nltk.download("punkt_tab", quiet=True)
    nltk.download("stopwords", quiet=True)
except:
    pass

def clean_text(text):
    """Remove punctuation and convert to lowercase"""
    if not text:
        return ""
    
    text = text.lower()
    # Remove punctuation
    for x in string.punctuation: 
        text = text.replace(x, " ")
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def analyze_text_content(text):
    """Analyze text and return comprehensive results"""
    if not text or not text.strip():
        return {
            'error': 'No text provided for analysis'
        }
    
    try:
        # Basic statistics
        original_text = text
        word_count = len(text.split())
        char_count = len(text)
        char_count_no_spaces = len(text.replace(' ', ''))
        sentence_count = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
        paragraph_count = len([p for p in text.split('\n\n') if p.strip()])
        
        # Clean text for analysis
        cleaned_text = clean_text(text)
        
        # Tokenize
        tokens = word_tokenize(cleaned_text) if cleaned_text else []
        
        # Remove stopwords and short words
        try:
            stop_words = set(stopwords.words('english'))
        except:
            stop_words = set()
        
        filtered_tokens = [
            word for word in tokens 
            if word not in stop_words and len(word) > 2
        ]
        
        # Calculate frequency distribution
        word_freq = Counter(tokens)
        filtered_word_freq = Counter(filtered_tokens)
        
        # Get top words
        top_words_all = word_freq.most_common(20)
        top_words_filtered = filtered_word_freq.most_common(15)
        
        # Calculate reading metrics
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0
        avg_chars_per_word = char_count_no_spaces / word_count if word_count > 0 else 0
        
        # Unique word count
        unique_words = len(set(tokens))
        lexical_diversity = unique_words / len(tokens) if tokens else 0
        
        return {
            'success': True,
            'basic_stats': {
                'word_count': word_count,
                'character_count': char_count,
                'character_count_no_spaces': char_count_no_spaces,
                'sentence_count': sentence_count,
                'paragraph_count': paragraph_count,
                'unique_words': unique_words,
                'lexical_diversity': round(lexical_diversity, 3)
            },
            'reading_metrics': {
                'avg_words_per_sentence': round(avg_words_per_sentence, 1),
                'avg_chars_per_word': round(avg_chars_per_word, 1)
            },
            'word_frequency': {
                'all_words': [{'word': word, 'count': count} for word, count in top_words_all],
                'filtered_words': [{'word': word, 'count': count} for word, count in top_words_filtered]
            },
            'processed_tokens': len(tokens),
            'filtered_tokens': len(filtered_tokens)
        }
    
    except Exception as e:
        return {
            'error': f'Analysis failed: {str(e)}'
        }

@app.route('/')
def index():
    """Serve the text input HTML frontend"""
    try:
        with open('text_analysis.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return """
        <h1>Error: Frontend file not found</h1>
        <p>Please make sure 'text_analysis.html' is in the same directory as this Python file.</p>
        <p>The file should contain your text input form.</p>
        """

@app.route('/results.html')
def results_page():
    """Serve the results HTML file"""
    try:
        with open('results.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        return html_content
    except FileNotFoundError:
        return """
        <h1>Error: Results file not found</h1>
        <p>Please make sure 'results.html' is in the same directory as this Python file.</p>
        """

@app.route('/analyze', methods=['POST'])
def analyze_text_form():
    """Handle form submission from text_analysis.html and redirect to results"""
    try:
        # Get text from form data (if submitted via form)
        if request.form:
            text = request.form.get('text', '').strip()
        else:
            # Handle JSON data (if submitted via JavaScript)
            data = request.get_json()
            text = data.get('text', '').strip() if data else ''
        
        if not text:
            return jsonify({
                'error': 'No text was provided for analysis.'
            }), 400
        
        # Perform analysis
        results = analyze_text_content(text)
        
        if 'error' in results:
            return jsonify(results), 400
        
        # Since your frontend expects to open results.html in a new window
        # and load data from localStorage, we'll return the results as JSON
        # Your frontend JavaScript will handle storing it in localStorage
        return jsonify(results)
    
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/analyze', methods=['POST'])
def analyze_endpoint():
    """API endpoint for text analysis (JSON) - used by your frontend"""
    try:
        # Get JSON data from request
        data = request.get_json()
        
        if not data or 'text' not in data:
            return jsonify({
                'error': 'No text provided in request'
            }), 400
        
        text = data['text']
        
        # Perform analysis
        results = analyze_text_content(text)
        
        if 'error' in results:
            return jsonify(results), 400
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({
            'error': f'Server error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Text Analysis API is running'
    })

if __name__ == '__main__':
    print("Starting Text Analysis Server...")
    print("Frontend will be available at: http://localhost:5000")
    print("Text input form: http://localhost:5000/")
    print("Results page: http://localhost:5000/results.html")
    print("API endpoint: http://localhost:5000/api/analyze")
    print("Health check: http://localhost:5000/api/health")
    print("\nMake sure you have these files in the same directory:")
    print("- text_analysis.html (for text input)")
    print("- results.html (for displaying results)")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)