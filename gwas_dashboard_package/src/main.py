"""
Main entry point for the GWAS Variant Analyzer Dashboard Flask application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # DON'T CHANGE THIS !!!

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS  # Added
import logging

# Import blueprints
from src.routes.api import api_bp

# Create Flask app
app = Flask(__name__, static_folder='static', template_folder='static')
CORS(app)  # Added: Enable CORS

# Set file size limit (300MB)
app.config['MAX_CONTENT_LENGTH'] = 300 * 1024 * 1024  # 300MB in bytes

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

# Register blueprints
app.register_blueprint(api_bp, url_prefix='/api')

# Serve static files
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return {"error": "Not found", "message": str(e)}, 404

@app.errorhandler(500)
def internal_server_error(e):
    return {"error": "Internal server error", "message": str(e)}, 500

# Run the app
if __name__ == '__main__':
    # Ensure the GWAS Variant Analyzer package is in the path
    gwas_package_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'gwas_variant_analyzer'))
    if os.path.exists(gwas_package_path):
        sys.path.append(os.path.dirname(gwas_package_path))
        app.logger.info(f"Added GWAS Variant Analyzer package to path: {gwas_package_path}")
    
    # Create config directory if it doesn't exist
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    # Copy config files from GWAS Variant Analyzer package if they don't exist
    src_config_dir = os.path.join(gwas_package_path, 'config')
    if os.path.exists(src_config_dir):
        for config_file in os.listdir(src_config_dir):
            src_file = os.path.join(src_config_dir, config_file)
            dst_file = os.path.join(config_dir, config_file)
            if not os.path.exists(dst_file) and os.path.isfile(src_file):
                import shutil
                shutil.copy2(src_file, dst_file)
                app.logger.info(f"Copied config file: {config_file}")
    
    # Run the app
    app.run(host='0.0.0.0', port=1111, debug=True)