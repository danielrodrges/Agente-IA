#!/bin/bash

# Fluxi Docker Runner Script
# This script provides easy commands to run Fluxi with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DEFAULT_PORT=8001
DEFAULT_HOST="0.0.0.0"
DEFAULT_DEBUG="True"
DEFAULT_DB_URL="sqlite:///./fluxi.db"
DEFAULT_UPLOAD_DIR="./uploads"

# Function to print colored output
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

# Function to show help
show_help() {
    echo "Fluxi Docker Runner"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  start       Start Fluxi with Docker Compose"
    echo "  stop        Stop Fluxi"
    echo "  restart     Restart Fluxi"
    echo "  build       Build Docker image"
    echo "  logs        Show logs"
    echo "  shell       Open shell in container"
    echo "  clean       Clean up containers and images"
    echo "  setup       Initial setup with environment file"
    echo ""
    echo "Options:"
    echo "  -p, --port PORT          Set port (default: $DEFAULT_PORT)"
    echo "  -d, --db-path PATH       Set database path (default: $DEFAULT_DB_PATH)"
    echo "  -u, --uploads-path PATH  Set uploads path (default: $DEFAULT_UPLOADS_PATH)"
    echo "  -s, --sessoes-path PATH  Set sessions path (default: $DEFAULT_SESSOES_PATH)"
    echo "  -r, --rags-path PATH     Set RAG documents path (default: $DEFAULT_RAGS_PATH)"
    echo ""
    echo "Examples:"
    echo "  $0 setup"
    echo "  $0 start"
    echo "  $0 start -p 8080 -d /custom/path/fluxi.db"
    echo "  $0 logs"
    echo "  $0 stop"
}

# Function to create .env file
setup_env() {
    print_info "Setting up environment file..."
    
    if [ -f .env ]; then
        print_warning ".env file already exists. Backing up to .env.backup"
        cp .env .env.backup
    fi
    
    cat > .env << EOF
# Fluxi Configuration
# Generated on $(date)

# Configuração do Banco de Dados
DATABASE_URL=$DEFAULT_DB_URL

# Configuração do Servidor
HOST=$DEFAULT_HOST
PORT=$DEFAULT_PORT
DEBUG=$DEFAULT_DEBUG

# Diretório de Upload de Imagens
UPLOAD_DIR=$DEFAULT_UPLOAD_DIR
EOF
    
    print_success "Environment file created: .env"
    print_info "You can edit .env to customize paths and port"
}

# Function to start Fluxi
start_fluxi() {
    print_info "Starting Fluxi..."
    
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating default configuration..."
        setup_env
    fi
    
    # Create directories if they don't exist
    mkdir -p uploads sessoes rags
    
    docker-compose up -d
    
    print_success "Fluxi started successfully!"
    print_info "Access Fluxi at: http://localhost:${PORT:-$DEFAULT_PORT}"
    print_info "To view logs: $0 logs"
}

# Function to stop Fluxi
stop_fluxi() {
    print_info "Stopping Fluxi..."
    docker-compose down
    print_success "Fluxi stopped"
}

# Function to restart Fluxi
restart_fluxi() {
    print_info "Restarting Fluxi..."
    docker-compose restart
    print_success "Fluxi restarted"
}

# Function to build image
build_fluxi() {
    print_info "Building Fluxi Docker image..."
    docker-compose build
    print_success "Fluxi image built successfully"
}

# Function to show logs
show_logs() {
    print_info "Showing Fluxi logs..."
    docker-compose logs -f
}

# Function to open shell
open_shell() {
    print_info "Opening shell in Fluxi container..."
    docker-compose exec fluxi bash
}

# Function to clean up
clean_up() {
    print_info "Cleaning up Docker resources..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed"
}

# Parse command line arguments
COMMAND=""
PORT=""
DB_PATH=""
UPLOADS_PATH=""
SESSOES_PATH=""
RAGS_PATH=""

while [[ $# -gt 0 ]]; do
    case $1 in
        start|stop|restart|build|logs|shell|clean|setup)
            COMMAND="$1"
            shift
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -d|--db-path)
            DB_PATH="$2"
            shift 2
            ;;
        -u|--uploads-path)
            UPLOADS_PATH="$2"
            shift 2
            ;;
        -s|--sessoes-path)
            SESSOES_PATH="$2"
            shift 2
            ;;
        -r|--rags-path)
            RAGS_PATH="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Set environment variables if provided
if [ ! -z "$PORT" ]; then
    export FLUXI_PORT="$PORT"
fi

if [ ! -z "$DB_PATH" ]; then
    export FLUXI_DB_PATH="$DB_PATH"
fi

if [ ! -z "$UPLOADS_PATH" ]; then
    export FLUXI_UPLOADS_PATH="$UPLOADS_PATH"
fi

if [ ! -z "$SESSOES_PATH" ]; then
    export FLUXI_SESSOES_PATH="$SESSOES_PATH"
fi

if [ ! -z "$RAGS_PATH" ]; then
    export FLUXI_RAGS_PATH="$RAGS_PATH"
fi

# Execute command
case $COMMAND in
    start)
        start_fluxi
        ;;
    stop)
        stop_fluxi
        ;;
    restart)
        restart_fluxi
        ;;
    build)
        build_fluxi
        ;;
    logs)
        show_logs
        ;;
    shell)
        open_shell
        ;;
    clean)
        clean_up
        ;;
    setup)
        setup_env
        ;;
    "")
        print_error "No command specified"
        show_help
        exit 1
        ;;
    *)
        print_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac
