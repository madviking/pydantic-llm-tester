#!/bin/bash
# Installation script for LLM Tester

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=======================================================${NC}"
echo -e "${BLUE}             LLM Tester Installation                   ${NC}"
echo -e "${BLUE}=======================================================${NC}"
echo

# Check if Python 3 is installed
if command -v python3 &>/dev/null; then
    echo -e "${GREEN}Python 3 is installed${NC}"
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    python_version=$(python --version 2>&1 | awk '{print $2}' | cut -d'.' -f1)
    if [ "$python_version" -ge 3 ]; then
        echo -e "${GREEN}Python 3 is installed${NC}"
        PYTHON_CMD="python"
    else
        echo -e "${RED}Python 3 is required but not found${NC}"
        echo "Please install Python 3 and try again"
        exit 1
    fi
else
    echo -e "${RED}Python is not installed${NC}"
    echo "Please install Python 3 and try again"
    exit 1
fi

# Create a virtual environment
echo
echo -e "${BLUE}Creating virtual environment...${NC}"
$PYTHON_CMD -m venv venv

# Activate the virtual environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo -e "${RED}Failed to create virtual environment${NC}"
    exit 1
fi

echo -e "${GREEN}Virtual environment created and activated${NC}"

# Install requirements
echo
echo -e "${BLUE}Installing required packages...${NC}"

# Install the package in development mode and dependencies from requirements.txt
pip install -e . -r requirements.txt

echo -e "${GREEN}Packages installed successfully${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo
    echo -e "${BLUE}Creating .env file for API keys...${NC}"
    cat > .env << EOF
# API Keys for LLM Providers
# Uncomment and add your keys

# OpenAI
# OPENAI_API_KEY=your_openai_key

# Anthropic
# ANTHROPIC_API_KEY=your_anthropic_key

# Mistral
# MISTRAL_API_KEY=your_mistral_key

# Google Vertex AI
# GOOGLE_PROJECT_ID=your_google_project_id
# GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
EOF
    echo -e "${GREEN}.env file created. Edit it to add your API keys.${NC}"
fi

# Make the main CLI entry point executable
chmod +x src/pydantic_llm_tester/cli/main.py

source venv/bin/activate
pip install build
python -m build
pip install -e .

echo
echo -e "${GREEN}LLM Tester installed successfully!${NC}"
echo
echo -e "To activate the virtual environment: ${BLUE}source venv/bin/activate${NC}"
echo -e "To run the interactive tool: ${BLUE}source venv/bin/activate && python src/pydantic_llm_tester/cli/main.py interactive${NC}"
echo -e "To run tests: ${BLUE}source venv/bin/activate && PYTHONPATH=./src pytest${NC}"
echo -e "Make sure to add your API keys to the .env file if you want to use real LLM providers."
echo
echo -e "${BLUE}=======================================================${NC}"
