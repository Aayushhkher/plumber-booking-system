#!/usr/bin/env python3
"""
Script to convert README.md to PDF with proper formatting
"""

import markdown
import weasyprint
from pathlib import Path
import re

def create_pdf_from_readme():
    """Convert README.md to PDF with proper styling"""
    
    # Read the README file
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("❌ README.md not found!")
        return False
    
    print("📖 Reading README.md...")
    with open(readme_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Convert markdown to HTML
    print("🔄 Converting markdown to HTML...")
    html_content = markdown.markdown(markdown_content, extensions=['toc', 'tables', 'fenced_code', 'codehilite'])
    
    # Create styled HTML document
    html_document = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advanced Plumber Booking System - Complete Architecture Documentation</title>
        <style>
            @page {{
                margin: 2cm;
                size: A4;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
                margin: 0;
                padding: 20px;
            }}
            
            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 2.5em;
                margin-top: 0;
            }}
            
            h2 {{
                color: #34495e;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 8px;
                font-size: 1.8em;
                margin-top: 30px;
            }}
            
            h3 {{
                color: #2c3e50;
                font-size: 1.4em;
                margin-top: 25px;
            }}
            
            h4 {{
                color: #34495e;
                font-size: 1.2em;
                margin-top: 20px;
            }}
            
            h5, h6 {{
                color: #7f8c8d;
                font-size: 1.1em;
                margin-top: 15px;
            }}
            
            p {{
                margin-bottom: 15px;
                text-align: justify;
            }}
            
            code {{
                background-color: #f8f9fa;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #e74c3c;
            }}
            
            pre {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                margin: 20px 0;
            }}
            
            pre code {{
                background-color: transparent;
                padding: 0;
                color: #333;
            }}
            
            blockquote {{
                border-left: 4px solid #3498db;
                margin: 20px 0;
                padding: 10px 20px;
                background-color: #f8f9fa;
                font-style: italic;
            }}
            
            ul, ol {{
                margin-bottom: 15px;
                padding-left: 30px;
            }}
            
            li {{
                margin-bottom: 5px;
            }}
            
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                font-size: 0.9em;
            }}
            
            th, td {{
                border: 1px solid #ddd;
                padding: 12px;
                text-align: left;
            }}
            
            th {{
                background-color: #f2f2f2;
                font-weight: bold;
            }}
            
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            
            .highlight {{
                background-color: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 15px 0;
            }}
            
            .success {{
                background-color: #d4edda;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #28a745;
                margin: 15px 0;
            }}
            
            .info {{
                background-color: #d1ecf1;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #17a2b8;
                margin: 15px 0;
            }}
            
            .warning {{
                background-color: #fff3cd;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #ffc107;
                margin: 15px 0;
            }}
            
            .danger {{
                background-color: #f8d7da;
                padding: 10px;
                border-radius: 5px;
                border-left: 4px solid #dc3545;
                margin: 15px 0;
            }}
            
            .toc {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 20px;
                margin: 20px 0;
            }}
            
            .toc h2 {{
                margin-top: 0;
                border-bottom: none;
            }}
            
            .toc ul {{
                list-style-type: none;
                padding-left: 0;
            }}
            
            .toc li {{
                margin-bottom: 8px;
            }}
            
            .toc a {{
                text-decoration: none;
                color: #007bff;
            }}
            
            .toc a:hover {{
                text-decoration: underline;
            }}
            
            .architecture-diagram {{
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 0.8em;
                white-space: pre-wrap;
                overflow-x: auto;
            }}
            
            .page-break {{
                page-break-before: always;
            }}
            
            @media print {{
                .page-break {{
                    page-break-before: always;
                }}
            }}
        </style>
    </head>
    <body>
        <h1>🛠️ Advanced Plumber Booking System</h1>
        <p><strong>A comprehensive web application for connecting customers with qualified plumbers in Gujarat, India. Features intelligent matching, dynamic attribute selection, and a modern user interface with enhanced admin dashboard for complete attribute system management.</strong></p>
        
        <div class="toc">
            <h2>📋 Table of Contents</h2>
            <ul>
                <li><a href="#system-architecture">🏗️ System Architecture</a></li>
                <li><a href="#features">✨ Features</a></li>
                <li><a href="#quick-start">🚀 Quick Start</a></li>
                <li><a href="#user-interface">🎨 User Interface</a></li>
                <li><a href="#advanced-features">🔧 Advanced Features</a></li>
                <li><a href="#technical-stack">🛠️ Technical Stack</a></li>
                <li><a href="#enhanced-admin-dashboard">🏗️ Enhanced Admin Dashboard Architecture</a></li>
                <li><a href="#deployment">🚀 Deployment Architecture</a></li>
                <li><a href="#monitoring">📊 Monitoring & Analytics</a></li>
            </ul>
        </div>
        
        {html_content}
        
        <div class="page-break"></div>
        <div class="highlight">
            <h2>📄 Document Information</h2>
            <p><strong>Generated:</strong> {Path.cwd().name}</p>
            <p><strong>Version:</strong> 1.0</p>
            <p><strong>Last Updated:</strong> {Path.cwd().stat().st_mtime}</p>
        </div>
    </body>
    </html>
    """
    
    # Save HTML file temporarily
    html_file = "temp_readme.html"
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_document)
    
    try:
        # Convert HTML to PDF
        print("📄 Converting HTML to PDF...")
        pdf_file = "Advanced_Plumber_Booking_System_Architecture.pdf"
        
        # Create PDF using weasyprint
        weasyprint.HTML(string=html_document).write_pdf(pdf_file)
        
        print(f"✅ PDF created successfully: {pdf_file}")
        
        # Clean up temporary HTML file
        Path(html_file).unlink()
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating PDF: {str(e)}")
        print("💡 Trying alternative method...")
        
        try:
            # Try using pandoc as fallback
            import subprocess
            result = subprocess.run([
                'pandoc', 'README.md', 
                '-o', 'Advanced_Plumber_Booking_System_Architecture.pdf',
                '--pdf-engine=wkhtmltopdf',
                '--toc'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ PDF created successfully using pandoc!")
                return True
            else:
                print(f"❌ Pandoc error: {result.stderr}")
                return False
                
        except Exception as e2:
            print(f"❌ Alternative method also failed: {str(e2)}")
            return False

if __name__ == "__main__":
    print("🚀 Starting PDF generation...")
    success = create_pdf_from_readme()
    
    if success:
        print("🎉 PDF generation completed successfully!")
        print("📁 Check the current directory for: Advanced_Plumber_Booking_System_Architecture.pdf")
    else:
        print("❌ PDF generation failed. Please check the error messages above.") 