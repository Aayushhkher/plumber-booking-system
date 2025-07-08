#!/usr/bin/env python3
"""
Simple script to start the Flask application
"""

from app import app

if __name__ == '__main__':
    print("🚀 Starting Plumber App with Enhanced Admin Dashboard...")
    print("📍 Server will be available at: http://localhost:5001")
    print("👤 Admin login: admin@example.com / admin123")
    print("📊 Admin Dashboard: http://localhost:5001/admin_dashboard")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5001) 