"""
Flask API Server for AI Sports Analysis
Multi-Sport Support: Cricket & Tennis
Provides REST endpoints for video upload and analysis
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
from pathlib import Path
import anthropic
from sports_analyzer import SportsAnalyzer

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

Path(UPLOAD_FOLDER).mkdir(exist_ok=True)

analyzer = SportsAnalyzer()


def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'sports-analysis.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '2.0.0',
        'sports': ['cricket', 'tennis'],
        'modes': {
            'cricket': ['bowling', 'batting'],
            'tennis': ['injury', 'form']
        }
    })


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Handle video upload"""
    if 'video' not in request.files:
        return jsonify({'error': 'No video file provided'}), 400
    
    file = request.files['video']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': f'Invalid file type. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    return jsonify({
        'message': 'File uploaded successfully',
        'filename': filename,
        'filepath': filepath
    })


@app.route('/api/analyze/cricket/bowling', methods=['POST'])
def analyze_cricket_bowling():
    """Analyze cricket bowling video"""
    try:
        data = request.get_json()
        
        if not data or 'filepath' not in data:
            return jsonify({'error': 'No filepath provided'}), 400
        
        filepath = data['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Video file not found'}), 404
        
        results = analyzer.analyze_cricket_bowling(filepath)
        
        try:
            enhanced_results = enhance_with_ai(results, 'cricket-bowling')
            return jsonify(enhanced_results)
        except:
            return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/cricket/batting', methods=['POST'])
def analyze_cricket_batting():
    """Analyze cricket batting video"""
    try:
        data = request.get_json()
        
        if not data or 'filepath' not in data:
            return jsonify({'error': 'No filepath provided'}), 400
        
        filepath = data['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Video file not found'}), 404
        
        results = analyzer.analyze_cricket_batting(filepath)
        
        try:
            enhanced_results = enhance_with_ai(results, 'cricket-batting')
            return jsonify(enhanced_results)
        except:
            return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/tennis/injury', methods=['POST'])
def analyze_tennis_injury():
    """Analyze tennis injury risk"""
    try:
        data = request.get_json()
        
        if not data or 'filepath' not in data:
            return jsonify({'error': 'No filepath provided'}), 400
        
        filepath = data['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Video file not found'}), 404
        
        results = analyzer.analyze_tennis_injury(filepath)
        
        try:
            enhanced_results = enhance_with_ai(results, 'tennis-injury')
            return jsonify(enhanced_results)
        except:
            return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/tennis/form', methods=['POST'])
def analyze_tennis_form():
    """Analyze tennis player form"""
    try:
        data = request.get_json()
        
        if not data or 'filepath' not in data:
            return jsonify({'error': 'No filepath provided'}), 400
        
        filepath = data['filepath']
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Video file not found'}), 404
        
        results = analyzer.analyze_tennis_form(filepath)
        
        try:
            enhanced_results = enhance_with_ai(results, 'tennis-form')
            return jsonify(enhanced_results)
        except:
            return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/analyze/combined', methods=['POST'])
def analyze_combined():
    """
    Combined endpoint that:
    1. Accepts video upload
    2. Performs analysis based on mode
    3. Returns results
    """
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file provided'}), 400
        
        file = request.files['video']
        mode = request.form.get('mode', 'cricket-bowling')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Analyze based on mode
        if mode == 'cricket-bowling':
            results = analyzer.analyze_cricket_bowling(filepath)
        elif mode == 'cricket-batting':
            results = analyzer.analyze_cricket_batting(filepath)
        elif mode == 'tennis-injury':
            results = analyzer.analyze_tennis_injury(filepath)
        elif mode == 'tennis-form':
            results = analyzer.analyze_tennis_form(filepath)
        else:
            return jsonify({'error': 'Invalid analysis mode'}), 400
        
        # Enhance with AI
        try:
            enhanced_results = enhance_with_ai(results, mode)
            results = enhanced_results
        except:
            pass
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def enhance_with_ai(results, mode):
    """Enhance analysis results with Claude AI insights"""
    try:
        client = anthropic.Anthropic()
        
        mode_descriptions = {
            'cricket-bowling': 'cricket bowling action',
            'cricket-batting': 'cricket batting technique',
            'tennis-injury': 'tennis injury risk assessment',
            'tennis-form': 'tennis player form and performance'
        }
        
        prompt = f"""
        Given these {mode_descriptions.get(mode, 'sports')} analysis results:
        {json.dumps(results, indent=2)}
        
        Provide enhanced insights. Return ONLY valid JSON with:
        - All original fields preserved exactly
        - Enhanced detailedAnalysis with deeper coaching insights
        - Keep all numeric values unchanged
        
        Focus on actionable recommendations and technical improvements.
        """
        
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        response_text = message.content[0].text
        enhanced_data = json.loads(response_text.replace('```json', '').replace('```', '').strip())
        
        return enhanced_data
        
    except Exception as e:
        print(f"AI enhancement error: {e}")
        return results


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get analysis statistics"""
    upload_dir = Path(UPLOAD_FOLDER)
    video_files = list(upload_dir.glob('*'))
    
    return jsonify({
        'total_analyses': len(video_files),
        'storage_used_mb': sum(f.stat().st_size for f in video_files if f.is_file()) / (1024 * 1024),
        'supported_formats': list(ALLOWED_EXTENSIONS),
        'sports': ['cricket', 'tennis'],
        'modes': {
            'cricket': ['bowling', 'batting'],
            'tennis': ['injury', 'form']
        }
    })


@app.errorhandler(413)
def file_too_large(e):
    """Handle file too large error"""
    return jsonify({'error': 'File too large. Maximum size is 100MB'}), 413


@app.errorhandler(500)
def internal_error(e):
    """Handle internal server error"""
    return jsonify({'error': 'Internal server error. Please try again.'}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("AI SPORTS ANALYSIS API SERVER")
    print("=" * 70)
    print(f"\n🚀 Server starting on http://localhost:5000")
    print(f"\n📊 Supported Sports:")
    print(f"   🏏 Cricket (Bowling & Batting Analysis)")
    print(f"   🎾 Tennis (Injury Risk & Form Analysis)")
    print(f"\n🔗 Available Endpoints:")
    print(f"   GET  /                          - Main application")
    print(f"   GET  /api/health                - Health check")
    print(f"   POST /api/upload                - Upload video")
    print(f"   POST /api/analyze/cricket/bowling  - Analyze cricket bowling")
    print(f"   POST /api/analyze/cricket/batting  - Analyze cricket batting")
    print(f"   POST /api/analyze/tennis/injury    - Analyze tennis injury risk")
    print(f"   POST /api/analyze/tennis/form      - Analyze tennis form")
    print(f"   POST /api/analyze/combined      - Upload & analyze in one call")
    print(f"   GET  /api/stats                 - Get statistics")
    print(f"\n📁 Upload folder: {UPLOAD_FOLDER}")
    print(f"📏 Max file size: {MAX_FILE_SIZE / (1024*1024):.0f}MB")
    print(f"📹 Supported formats: {', '.join(ALLOWED_EXTENSIONS)}")
    print("\n" + "=" * 70 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
