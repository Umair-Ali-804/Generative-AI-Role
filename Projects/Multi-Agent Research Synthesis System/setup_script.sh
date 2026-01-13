#!/bin/bash

# Multi-Agent Research Synthesis System - Automated Setup Script
# This script sets up the complete environment for the project

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${GREEN}"
cat << "EOF"
╔═══════════════════════════════════════════════════════════════════════╗
║                                                                       ║
║        Multi-Agent Research Synthesis System                          ║
║                   Setup Script v1.0                                   ║
║                                                                       ║
╚═══════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check if running on supported OS
check_os() {
    print_info "Checking operating system..."
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_success "Running on Linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_success "Running on macOS"
    elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        print_warning "Running on Windows (use WSL for best experience)"
    else
        print_error "Unsupported operating system"
        exit 1
    fi
}

# Check Python version
check_python() {
    print_info "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.11+"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$MAJOR" -lt 3 ] || ([ "$MAJOR" -eq 3 ] && [ "$MINOR" -lt 11 ]); then
        print_error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Skipping creation."
    else
        python3 -m venv venv
        print_success "Virtual environment created"
    fi
}

# Activate virtual environment
activate_venv() {
    print_info "Activating virtual environment..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    pip install --upgrade pip
    pip install -r requirements.txt
    
    print_success "Dependencies installed successfully"
}

# Setup environment file
setup_env() {
    print_info "Setting up environment configuration..."
    
    if [ -f ".env" ]; then
        print_warning ".env file already exists. Skipping creation."
        print_info "Please ensure your API keys are configured in .env"
    else
        cp .env.template .env
        print_success ".env file created from template"
        print_warning "Please edit .env and add your API keys:"
        echo "  - OPENAI_API_KEY"
        echo "  - ANTHROPIC_API_KEY"
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating project directories..."
    
    mkdir -p output
    mkdir -p logs
    mkdir -p data
    
    print_success "Directories created"
}

# Check Docker (optional)
check_docker() {
    print_info "Checking for Docker..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        
        if command -v docker-compose &> /dev/null; then
            print_success "Docker Compose is installed"
        else
            print_warning "Docker Compose not found. Install for containerized deployment."
        fi
    else
        print_warning "Docker not found. Install Docker for containerized deployment."
    fi
}

# Run tests
run_tests() {
    print_info "Running system tests..."
    
    if python test_system.py; then
        print_success "All tests passed!"
    else
        print_warning "Some tests failed. Please check the output above."
    fi
}

# Print next steps
print_next_steps() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Setup Complete!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${BLUE}Next Steps:${NC}"
    echo ""
    echo "1. Configure API Keys:"
    echo "   ${YELLOW}nano .env${NC}"
    echo "   Add your OpenAI and Anthropic API keys"
    echo ""
    echo "2. Activate virtual environment:"
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
        echo "   ${YELLOW}source venv/Scripts/activate${NC}"
    else
        echo "   ${YELLOW}source venv/bin/activate${NC}"
    fi
    echo ""
    echo "3. Test the system:"
    echo "   ${YELLOW}python main.py -q \"What are RAG techniques for LLMs?\"${NC}"
    echo ""
    echo "4. Run in interactive mode:"
    echo "   ${YELLOW}python main.py -i${NC}"
    echo ""
    echo "5. Process batch queries:"
    echo "   ${YELLOW}python main.py -b example_queries.txt -o output/${NC}"
    echo ""
    echo -e "${BLUE}Documentation:${NC}"
    echo "   - README.md: Complete system documentation"
    echo "   - DEPLOYMENT.md: Production deployment guide"
    echo ""
    echo -e "${BLUE}Support:${NC}"
    echo "   - GitHub: https://github.com/Umair-Ali-804/research-synthesis-system"
    echo "   - Email: aliumair64488@gmail.com"
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════${NC}"
}

# Verify installation
verify_installation() {
    print_info "Verifying installation..."
    
    # Check if required files exist
    required_files=(
        "research_synthesis_system.py"
        "main.py"
        "config.py"
        "requirements.txt"
        ".env.template"
    )
    
    for file in "${required_files[@]}"; do
        if [ ! -f "$file" ]; then
            print_error "Required file missing: $file"
            exit 1
        fi
    done
    
    print_success "All required files present"
}

# Main setup function
main() {
    echo ""
    print_info "Starting setup process..."
    echo ""
    
    # Run checks and setup
    check_os
    check_python
    verify_installation
    create_directories
    create_venv
    activate_venv
    install_dependencies
    setup_env
    check_docker
    
    echo ""
    print_info "Setup process completed!"
    
    # Ask if user wants to run tests
    read -p "$(echo -e ${BLUE}[QUESTION]${NC} Do you want to run system tests now? \(y/n\): )" -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_tests
    else
        print_info "Skipping tests. You can run them later with: python test_system.py"
    fi
    
    # Print next steps
    print_next_steps
}

# Run main function
main "$@"