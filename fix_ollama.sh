#!/bin/bash

echo "============================================================"
echo "  OLLAMA TROUBLESHOOTING & FIX SCRIPT"
echo "============================================================"
echo ""

# Function to test Ollama
test_ollama() {
    echo "Testing Ollama connection..."
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama is running"
        return 0
    else
        echo "✗ Ollama is not running"
        return 1
    fi
}

# Stop existing Ollama processes
echo "1. Stopping existing Ollama processes..."
pkill ollama 2>/dev/null
sleep 2

# Start Ollama in background
echo "2. Starting Ollama server..."
nohup ollama serve > /tmp/ollama.log 2>&1 &
sleep 3

# Test connection
if ! test_ollama; then
    echo ""
    echo "⚠️  Could not start Ollama automatically"
    echo "Please run manually: ollama serve"
    exit 1
fi

# Pull a smaller, faster model
echo ""
echo "3. Current models:"
ollama list

echo ""
echo "4. Options to fix timeout issues:"
echo ""
echo "   A. Use a smaller/faster model (RECOMMENDED):"
echo "      ollama pull phi"
echo "      ollama pull tinyllama"
echo ""
echo "   B. Or continue with llama3.2 (slower but better quality)"
echo ""
read -p "Enter 'A' for fast model, 'B' to keep llama3.2, or 'S' to skip: " choice

case $choice in
    [Aa]* )
        echo ""
        echo "Pulling phi model (small and fast)..."
        ollama pull phi
        echo ""
        echo "✓ Update your .env file:"
        echo "  OLLAMA_MODEL=phi"
        ;;
    [Bb]* )
        echo ""
        echo "Keeping llama3.2"
        echo "Note: This model is slower. Consider using streaming or the improved fallback."
        ;;
    [Ss]* )
        echo "Skipping model change"
        ;;
    * )
        echo "Invalid choice"
        ;;
esac

echo ""
echo "============================================================"
echo "  NEXT STEPS"
echo "============================================================"
echo ""
echo "1. If you changed the model, update .env:"
echo "   OLLAMA_MODEL=phi"
echo ""
echo "2. Test again:"
echo "   python test_ollama.py"
echo ""
echo "3. Or just use the improved fallback extraction:"
echo "   It now works much better!"
echo ""
echo "4. Run your app:"
echo "   python main.py"
echo ""
echo "============================================================"