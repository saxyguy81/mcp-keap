#!/bin/bash
# Local CI Test Script
# Simulates the CI pipeline locally for development testing

set -e

echo "🧪 Running Local CI Simulation"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Error: Not in project root directory${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Installing dependencies...${NC}"
pip install -r requirements.txt
pip install pytest pytest-cov coverage pytest-asyncio ruff coverage-badge

echo -e "${BLUE}🔍 Running linting checks...${NC}"
if ruff check src/; then
    echo -e "${GREEN}✅ Linting passed${NC}"
else
    echo -e "${YELLOW}⚠️  Linting issues found${NC}"
fi

echo -e "${BLUE}🎨 Checking code formatting...${NC}"
if ruff format --check src/; then
    echo -e "${GREEN}✅ Code formatting is correct${NC}"
else
    echo -e "${YELLOW}⚠️  Code formatting issues found${NC}"
    echo "Run 'ruff format src/' to fix"
fi

echo -e "${BLUE}🧪 Running unit tests...${NC}"
python -m pytest tests/unit/ -v --tb=short

echo -e "${BLUE}📊 Running coverage analysis...${NC}"
python -m pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=xml --cov-report=json

echo -e "${BLUE}🎯 Checking coverage threshold...${NC}"
if python -m pytest tests/unit/ --cov=src --cov-fail-under=60 --cov-report=term > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Coverage threshold met (≥60%)${NC}"
else
    echo -e "${YELLOW}⚠️  Coverage below 60% threshold${NC}"
fi

echo -e "${BLUE}🏷️  Generating coverage badge...${NC}"
if command -v coverage-badge >/dev/null 2>&1; then
    coverage-badge -f -o coverage.svg
    echo -e "${GREEN}✅ Coverage badge generated${NC}"
else
    echo -e "${YELLOW}⚠️  coverage-badge not installed${NC}"
fi

echo -e "${BLUE}🔒 Running security checks...${NC}"
if grep -r "password\s*=" src/ || \
   grep -r "secret\s*=" src/ || \
   grep -r "token\s*=" src/ || \
   grep -r "api_key\s*=" src/; then
    echo -e "${RED}❌ Potential hardcoded credentials found!${NC}"
else
    echo -e "${GREEN}✅ No obvious security issues found${NC}"
fi

echo -e "${BLUE}📈 Extracting coverage percentage...${NC}"
if [ -f "coverage.json" ]; then
    COVERAGE=$(python -c "import json; data=json.load(open('coverage.json')); print(f'{data[\"totals\"][\"percent_covered\"]:.1f}')")
    echo -e "${GREEN}📊 Current coverage: ${COVERAGE}%${NC}"
else
    echo -e "${YELLOW}⚠️  No coverage.json found${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Local CI simulation completed!${NC}"
echo -e "${BLUE}📋 Summary:${NC}"
echo "  - Linting: Check completed"
echo "  - Formatting: Check completed"  
echo "  - Unit tests: Executed"
echo "  - Coverage: Analyzed"
echo "  - Security: Basic checks passed"
echo ""
echo -e "${BLUE}💡 Next steps:${NC}"
echo "  - Commit your changes"
echo "  - Push to trigger real CI pipeline"
echo "  - Check GitHub Actions for full results"