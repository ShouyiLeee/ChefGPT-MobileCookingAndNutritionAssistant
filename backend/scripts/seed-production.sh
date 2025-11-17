#!/bin/bash

###############################################################################
# ChefGPT Production Data Seeding Script
# Seeds production database with initial recipes
###############################################################################

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-production}
DOCKER_COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Seeding Production Database${NC}"
echo -e "${GREEN}=====================================${NC}\n"

echo -e "${YELLOW}Running seed script...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" exec backend python scripts/seed_recipes.py

echo -e "\n${YELLOW}Generating embeddings for recipes...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" exec backend python scripts/reindex_recipes.py

echo -e "\n${GREEN}✓ Database seeding completed${NC}"
