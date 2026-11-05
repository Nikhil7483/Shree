#!/usr/bin/env bash
# ==============================================================================
# Shree Shanishwara Swamy Temple Website — Safe Production Deployment Script
# ==============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}================================================================${NC}"
echo -e "${YELLOW}  Shree Shanishwara Swamy Temple — Safe Deployment Runner${NC}"
echo -e "${CYAN}================================================================${NC}"

# 1. Verify Docker and Docker Compose
command -v docker >/dev/null 2>&1 || {
    echo -e "${RED}[ERROR] Docker is not installed. Please install Docker first:${NC}"
    echo "  curl -fsSL https://get.docker.com | sh"
    exit 1
}

docker compose version >/dev/null 2>&1 || {
    echo -e "${RED}[ERROR] Docker Compose plugin is not installed.${NC}"
    exit 1
}

echo -e "${GREEN}[OK] Docker and Docker Compose detected.${NC}"

# 2. Check for .env.production
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

if [ ! -f ".env.production" ]; then
    echo -e "${RED}[ERROR] .env.production file not found!${NC}"
    echo -e "Please create it from the template:"
    echo -e "  cp .env.production.example .env.production"
    echo -e "  chmod 600 .env.production"
    echo -e "Then fill in strong production passwords and your domain."
    exit 1
fi

# 3. Security audit of .env.production (Verify placeholders have been changed)
if grep -q "CHANGE_THIS" ".env.production" || grep -q "GENERATE_RANDOM" ".env.production"; then
    echo -e "${RED}[SECURITY ALERT] Placeholder credentials detected in .env.production!${NC}"
    echo -e "You must update MONGO_ROOT_PASSWORD, JWT_SECRET_KEY, and ADMIN_PASSWORD before deploying."
    exit 1
fi

# 4. Restrict permissions on sensitive configuration
chmod 600 .env.production
echo -e "${GREEN}[OK] .env.production security permissions verified (chmod 600).${NC}"

# 5. Build and deploy containers
echo -e "${CYAN}[+] Building production Docker images...${NC}"
docker compose build --pull

echo -e "${CYAN}[+] Starting production containers in detached mode...${NC}"
docker compose up -d --remove-orphans

echo -e "${CYAN}[+] Waiting for services to become healthy...${NC}"
sleep 5

# 6. Check health status
docker compose ps

echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}  Deployment completed successfully!${NC}"
echo -e "${GREEN}================================================================${NC}"
echo -e "View live logs with: ${YELLOW}docker compose logs -f${NC}"

