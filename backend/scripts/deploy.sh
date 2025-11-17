#!/bin/bash

###############################################################################
# ChefGPT Production Deployment Script
#
# Usage:
#   ./scripts/deploy.sh [environment]
#
# Environments: production, staging, development
# Default: production
###############################################################################

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-production}
PROJECT_NAME="chefgpt"
DOCKER_COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}ChefGPT Deployment Script${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}=====================================${NC}\n"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(production|staging|development|dev)$ ]]; then
    echo -e "${RED}Error: Invalid environment '${ENVIRONMENT}'${NC}"
    echo "Valid environments: production, staging, development, dev"
    exit 1
fi

# Map 'development' and 'dev' to 'dev' for docker-compose file
if [[ "$ENVIRONMENT" == "development" ]]; then
    DOCKER_COMPOSE_FILE="docker-compose.dev.yml"
elif [[ "$ENVIRONMENT" == "dev" ]]; then
    DOCKER_COMPOSE_FILE="docker-compose.dev.yml"
fi

# Check if docker-compose file exists
if [ ! -f "$DOCKER_COMPOSE_FILE" ]; then
    echo -e "${RED}Error: Docker compose file '${DOCKER_COMPOSE_FILE}' not found${NC}"
    exit 1
fi

# Check if .env file exists
ENV_FILE=".env.${ENVIRONMENT}"
if [ "$ENVIRONMENT" == "dev" ] || [ "$ENVIRONMENT" == "development" ]; then
    ENV_FILE=".env"
fi

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${YELLOW}Warning: Environment file '${ENV_FILE}' not found${NC}"
    echo -e "${YELLOW}Using .env.example as template${NC}"

    if [ ! -f ".env.example" ]; then
        echo -e "${RED}Error: .env.example not found${NC}"
        exit 1
    fi

    cp .env.example "$ENV_FILE"
    echo -e "${YELLOW}Please update ${ENV_FILE} with your configuration${NC}"
    exit 1
fi

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}Error: Docker is not running${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker is running${NC}"
}

# Function to pull latest changes (if in git repo)
pull_latest() {
    if [ -d .git ]; then
        echo -e "\n${YELLOW}Pulling latest changes...${NC}"
        git pull origin main || git pull origin master || echo "Skip git pull"
    fi
}

# Function to backup database
backup_database() {
    if [ "$ENVIRONMENT" == "production" ]; then
        echo -e "\n${YELLOW}Creating database backup...${NC}"
        BACKUP_DIR="./backups"
        mkdir -p "$BACKUP_DIR"

        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.sql"

        # Backup database using docker-compose
        docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_dump -U postgres chefgpt > "$BACKUP_FILE" 2>/dev/null || echo "Skip backup (DB not running)"

        if [ -f "$BACKUP_FILE" ]; then
            echo -e "${GREEN}✓ Database backup created: ${BACKUP_FILE}${NC}"
        fi
    fi
}

# Function to build Docker images
build_images() {
    echo -e "\n${YELLOW}Building Docker images...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" build --no-cache
    echo -e "${GREEN}✓ Docker images built${NC}"
}

# Function to run database migrations
run_migrations() {
    echo -e "\n${YELLOW}Running database migrations...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend alembic upgrade head
    echo -e "${GREEN}✓ Migrations completed${NC}"
}

# Function to start services
start_services() {
    echo -e "\n${YELLOW}Starting services...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    echo -e "${GREEN}✓ Services started${NC}"
}

# Function to check service health
check_health() {
    echo -e "\n${YELLOW}Checking service health...${NC}"
    sleep 5

    # Check backend health
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "backend.*Up"; then
        echo -e "${GREEN}✓ Backend is running${NC}"
    else
        echo -e "${RED}✗ Backend failed to start${NC}"
        docker-compose -f "$DOCKER_COMPOSE_FILE" logs backend
        exit 1
    fi

    # Check database health
    if docker-compose -f "$DOCKER_COMPOSE_FILE" ps | grep -q "db.*Up"; then
        echo -e "${GREEN}✓ Database is running${NC}"
    else
        echo -e "${RED}✗ Database failed to start${NC}"
        exit 1
    fi
}

# Function to cleanup old images
cleanup() {
    echo -e "\n${YELLOW}Cleaning up old Docker images...${NC}"
    docker image prune -f
    echo -e "${GREEN}✓ Cleanup completed${NC}"
}

# Main deployment flow
main() {
    check_docker

    # Production safety check
    if [ "$ENVIRONMENT" == "production" ]; then
        echo -e "\n${RED}WARNING: You are deploying to PRODUCTION${NC}"
        read -p "Are you sure you want to continue? (yes/no): " confirm
        if [ "$confirm" != "yes" ]; then
            echo -e "${YELLOW}Deployment cancelled${NC}"
            exit 0
        fi
    fi

    pull_latest
    backup_database

    # Stop existing services
    echo -e "\n${YELLOW}Stopping existing services...${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" down

    build_images
    start_services

    # Wait for services to be ready
    echo -e "\n${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10

    run_migrations
    check_health
    cleanup

    echo -e "\n${GREEN}=====================================${NC}"
    echo -e "${GREEN}Deployment completed successfully!${NC}"
    echo -e "${GREEN}=====================================${NC}"

    # Show service URLs
    echo -e "\n${YELLOW}Service URLs:${NC}"
    if [ "$ENVIRONMENT" == "production" ]; then
        echo -e "Backend API: ${GREEN}https://api.chefgpt.com${NC}"
        echo -e "Health Check: ${GREEN}https://api.chefgpt.com/health${NC}"
    else
        echo -e "Backend API: ${GREEN}http://localhost:8000${NC}"
        echo -e "API Docs: ${GREEN}http://localhost:8000/docs${NC}"
        echo -e "Health Check: ${GREEN}http://localhost:8000/health${NC}"
        if [ "$ENVIRONMENT" == "dev" ]; then
            echo -e "Adminer (DB UI): ${GREEN}http://localhost:8080${NC}"
            echo -e "Redis Commander: ${GREEN}http://localhost:8081${NC}"
        fi
    fi

    # Show logs
    echo -e "\n${YELLOW}Viewing logs (Ctrl+C to exit):${NC}"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs -f
}

# Run main function
main
