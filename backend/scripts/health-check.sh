#!/bin/bash

###############################################################################
# ChefGPT Health Check Script
# Monitors all services and reports status
###############################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ENVIRONMENT=${1:-production}
DOCKER_COMPOSE_FILE="docker-compose.${ENVIRONMENT}.yml"

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}ChefGPT Health Check${NC}"
echo -e "${GREEN}Environment: ${ENVIRONMENT}${NC}"
echo -e "${GREEN}=====================================${NC}\n"

# Check Docker
echo -e "${YELLOW}Checking Docker...${NC}"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Docker is running${NC}\n"
else
    echo -e "${RED}✗ Docker is not running${NC}\n"
    exit 1
fi

# Check services
echo -e "${YELLOW}Checking services...${NC}"
docker-compose -f "$DOCKER_COMPOSE_FILE" ps

# Check backend health endpoint
echo -e "\n${YELLOW}Checking backend API...${NC}"
if [ "$ENVIRONMENT" == "production" ]; then
    BACKEND_URL="https://api.chefgpt.com"
else
    BACKEND_URL="http://localhost:8000"
fi

HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/health" || echo "failed")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo -e "${GREEN}✓ Backend API is healthy${NC}"
    echo "$HEALTH_RESPONSE" | python3 -m json.tool
else
    echo -e "${RED}✗ Backend API is not responding${NC}"
fi

# Check database
echo -e "\n${YELLOW}Checking database...${NC}"
DB_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T db pg_isready -U postgres 2>&1)
if echo "$DB_STATUS" | grep -q "accepting connections"; then
    echo -e "${GREEN}✓ Database is accepting connections${NC}"
else
    echo -e "${RED}✗ Database is not responding${NC}"
fi

# Check Redis
echo -e "\n${YELLOW}Checking Redis...${NC}"
REDIS_STATUS=$(docker-compose -f "$DOCKER_COMPOSE_FILE" exec -T redis redis-cli ping 2>&1 || echo "failed")
if echo "$REDIS_STATUS" | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is responding${NC}"
else
    echo -e "${RED}✗ Redis is not responding${NC}"
fi

# Check disk space
echo -e "\n${YELLOW}Checking disk space...${NC}"
df -h | grep -E "Filesystem|/$" | awk '{print $5 " used on " $6}'

# Check memory usage
echo -e "\n${YELLOW}Checking memory usage...${NC}"
free -h | grep -E "Mem:|Swap:"

echo -e "\n${GREEN}Health check completed${NC}"
