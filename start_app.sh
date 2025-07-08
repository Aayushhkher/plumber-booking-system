#!/bin/bash

cd "/Users/aayushkher/Desktop/project plumber"

echo "Starting Flask App..."
echo "===================="

# Check if required files exist
if [ ! -f "app.py" ]; then
    echo "❌ app.py not found!"
    exit 1
fi

if [ ! -f "enhanced_plumbers_dataset.csv" ]; then
    echo "❌ enhanced_plumbers_dataset.csv not found!"
    exit 1
fi

if [ ! -f "attribute_system.py" ]; then
    echo "❌ attribute_system.py not found!"
    exit 1
fi

echo "✅ All required files found"

# Test the attribute system
echo "Testing attribute system..."
python3 -c "
from attribute_system import DynamicAttributeSystem
system = DynamicAttributeSystem()
system.load_dataset('enhanced_plumbers_dataset.csv')
results = system.match_plumbers({'client_lat': 21.1702, 'client_lon': 72.8311}, max_results=3)
print(f'✅ Attribute system working - Found {len(results)} plumbers')
"

# Start the Flask app
echo "Starting Flask app on port 5001..."
echo "Open your browser and go to: http://localhost:5001"
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py 