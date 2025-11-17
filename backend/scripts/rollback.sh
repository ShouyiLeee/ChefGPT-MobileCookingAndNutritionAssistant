#!/bin/bash

###############################################################################
# ChefGPT Rollback Script
#
# Usage:
#   ./scripts/rollback.sh [environment] [backup_file]
###############################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-production}
BACKUP_FILE=$2
DOCKER_COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo -e "${RED}=====================================${NC}"
echo -e "${RED}ChefGPT Rollback Script${NC}"
echo -e "${RED}Environment: ${ENVIRONMENT}${NC}"
echo -e "${RED}=====================================${NC}\n"

# Safety check
if [ "$ENVIRONMENT" == "production" ]; then
    echo -e "${RED}WARNING: You are rolling back PRODUCTION${NC}"
    read -p "Are you sure? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        exit 0
    fi
fi

# List available backups
if [ -z "$BACKUP_FILE" ]; then
    echo -e "${YELLOW}Available backups:${NC}"
    ls -lh ./backups/*.sql 2>/dev/null || echo "No backups found"
    echo ""
    read -p "Enter backup filename: " BACKUP_FILE
fi

# Validate backup file
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: ${BACKUP_FILE}${NC}"
    exit 1
fi

echo -e "\n${YELLOW}Rolling back database migration...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" run --rm backend alembic downgrade -1

echo -e "\n${YELLOW}Restoring database from backup...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db psql -U postgres chefgpt < "$BACKUP_FILE"

echo -e "\n${YELLOW}Restarting services...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" restart

echo -e "\n${GREEN}Rollback completed${NC}"
