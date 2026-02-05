#!/bin/bash

##############################################################################
# YouTube Clipper - Setup Script
#
# Function:
# 1. Install Python dependencies
# 2. Check system dependencies (yt-dlp, FFmpeg)
# 3. Create initial configuration (.env)
#
# Usage:
#   bash setup.sh
##############################################################################

set -e  # Exit immediately if a command exits with a non-zero status.

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# Check command existence
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main function
main() {
    print_header "YouTube Clipper - Environment Setup"

    # Current directory is the target
    SKILL_DIR="$(pwd)"
    print_info "Working Directory: $SKILL_DIR"

    # 1. Check Python
    print_info "Checking Python environment..."
    if ! command_exists python3; then
        print_error "Python 3 not found. Please install Python 3.8+"
        exit 1
    fi

    PYTHON_VERSION=$(python3 --version)
    print_success "Python installed: $PYTHON_VERSION"

    # 2. Setup Virtual Environment
    print_info "Setting up Python virtual environment..."
    
    VENV_DIR="$SKILL_DIR/.venv"
    
    if [ ! -d "$VENV_DIR" ]; then
        print_info "Creating venv at $VENV_DIR..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists at $VENV_DIR"
    fi

    # 3. Install Python dependencies in venv
    print_info "Installing Python dependencies in venv..."
    
    # Use the pip inside the venv
    VENV_PIP="$VENV_DIR/bin/pip"
    
    if [ ! -x "$VENV_PIP" ]; then
        print_error "pip not found in venv at $VENV_PIP"
        exit 1
    fi
    
    # Upgrade pip first
    "$VENV_PIP" install --upgrade pip -q
    
    # Install dependencies
    "$VENV_PIP" install -q yt-dlp pysrt python-dotenv pycryptodomex brotli certifi requests
    
    print_success "Python dependencies installed in venv (yt-dlp, pysrt, python-dotenv, pycryptodomex)"

    # 4. Check yt-dlp
    print_info "Checking yt-dlp..."
    if command_exists yt-dlp; then
        YT_DLP_VERSION=$(yt-dlp --version)
        print_success "yt-dlp installed: $YT_DLP_VERSION"
    else
        print_warning "yt-dlp CLI tool not found"
        print_info "Installation:"
        print_info "  macOS:  brew install yt-dlp"
        print_info "  Ubuntu: sudo apt-get install yt-dlp"
        print_info "  Or: pip3 install -U yt-dlp"
    fi

    # 5. Check FFmpeg (Critical: needs libass)
    print_header "Checking FFmpeg (Required for subtitle burning)"

    FFMPEG_FOUND=false
    LIBASS_SUPPORTED=false

    # Check ffmpeg-full (macOS recommended)
    if [ -f "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg" ]; then
        print_success "ffmpeg-full found (Apple Silicon)"
        FFMPEG_FOUND=true
        LIBASS_SUPPORTED=true
    elif [ -f "/usr/local/opt/ffmpeg-full/bin/ffmpeg" ]; then
        print_success "ffmpeg-full found (Intel Mac)"
        FFMPEG_FOUND=true
        LIBASS_SUPPORTED=true
    elif command_exists ffmpeg; then
        FFMPEG_VERSION=$(ffmpeg -version | head -n 1)
        print_success "FFmpeg found: $FFMPEG_VERSION"
        FFMPEG_FOUND=true

        # Check libass support
        if ffmpeg -filters 2>&1 | grep -q "subtitles"; then
            print_success "FFmpeg supports libass (Subtitle burning available)"
            LIBASS_SUPPORTED=true
        else
            print_warning "FFmpeg does NOT support libass (Subtitle burning unavailable)"
        fi
    fi

    if [ "$FFMPEG_FOUND" = false ]; then
        print_error "FFmpeg not found"
        print_info "Installation:"
        print_info "  macOS:  brew install ffmpeg-full  # Recommended, includes libass"
        print_info "  Ubuntu: sudo apt-get install ffmpeg libass-dev"
    elif [ "$LIBASS_SUPPORTED" = false ]; then
        print_warning "FFmpeg lacks libass support"
        print_info "Fix (macOS):"
        print_info "  brew uninstall ffmpeg"
        print_info "  brew install ffmpeg-full"
    fi

    # 6. Create .env file
    print_header "Configuration"

    if [ -f "$SKILL_DIR/.env" ]; then
        print_info ".env file already exists"
    elif [ -f "$SKILL_DIR/.env.example" ]; then
        print_info "Creating .env file..."
        cp "$SKILL_DIR/.env.example" "$SKILL_DIR/.env"
        print_success ".env file created"
        echo ""
        print_info "Config file: $SKILL_DIR/.env"
        print_info "To customize:"
        print_info "  nano .env"
    else
        print_warning "No .env.example found, skipping .env creation"
    fi

    # 7. Complete
    print_header "Setup Complete!"

    print_success "YouTube Clipper is ready to use"
    echo ""
    
    # Check dependency status
    if [ "$FFMPEG_FOUND" = false ] || [ "$LIBASS_SUPPORTED" = false ]; then
        print_warning "System dependencies are incomplete. Some features may not work."
        echo ""
    fi

    print_info "Usage:"
    print_info "  1. Activate virtual environment:"
    print_info "     source .venv/bin/activate"
    print_info "  2. Run scripts as described in SKILL.md"
    echo ""
    print_success "Enjoy! 🎉"
    echo ""
}

# Error handling
trap 'print_error "An error occurred during setup"; exit 1' ERR

# Run main
main
