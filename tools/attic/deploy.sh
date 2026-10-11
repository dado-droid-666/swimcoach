#!/bin/bash
# SwimCoach Deployment Script
# Usage: ./deploy.sh [railway|render|docker|local]

set -e

ENVIRONMENT=${1:-local}
PROJECT_NAME="swimcoach"

echo "🚀 SwimCoach Deployment Script"
echo "Environment: $ENVIRONMENT"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_requirements() {
    echo "📋 Checking requirements..."
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 not found${NC}"
        exit 1
    fi
    
    if ! command -v pip &> /dev/null; then
        echo -e "${RED}❌ pip not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Requirements OK${NC}"
}

setup_env() {
    echo "🔧 Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.example ]; then
            cp .env.example .env
            echo -e "${YELLOW}⚠️  Created .env from .env.example - please edit it!${NC}"
        else
            echo -e "${RED}❌ No .env.example found${NC}"
            exit 1
        fi
    fi
    
    # Generate SECRET_KEY if not set
    if grep -q "SECRET_KEY=generate" .env || grep -q "SECRET_KEY=$" .env; then
        SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))")
        sed -i "s/SECRET_KEY=.*/SECRET_KEY=$SECRET/" .env
        echo -e "${GREEN}✅ Generated SECRET_KEY${NC}"
    fi
}

run_tests() {
    echo "🧪 Running tests..."
    if [ -f test_final_all.py ]; then
        python test_final_all.py
        echo -e "${GREEN}✅ Tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️  No test file found${NC}"
    fi
}

deploy_local() {
    echo "🏠 Starting local development server..."
    echo "   Backend: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
    echo "   Press Ctrl+C to stop"
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
}

deploy_docker() {
    echo "🐳 Building Docker image..."
    docker build -t swimcoach:latest .
    
    echo "🚀 Starting container..."
    docker run -d \
        --name swimcoach \
        -p 8000:8000 \
        --env-file .env \
        --restart unless-stopped \
        swimcoach:latest
    
    echo -e "${GREEN}✅ Container started on port 8000${NC}"
    echo "   View logs: docker logs -f swimcoach"
}

deploy_railway() {
    echo "🚂 Deploying to Railway..."
    
    if ! command -v railway &> /dev/null; then
        echo "Installing Railway CLI..."
        npm install -g @railway/cli
    fi
    
    railway login
    railway link
    railway up
    
    echo -e "${GREEN}✅ Deployed to Railway${NC}"
    echo "   View dashboard: https://railway.app/dashboard"
}

deploy_render() {
    echo "🎨 Deploying to Render..."
    echo "Please configure in Render dashboard:"
    echo "  1. Connect GitHub repo"
    echo "  2. Add PostgreSQL database"
    echo "  3. Set environment variables"
    echo "  4. Deploy"
    echo ""
    echo "Render will auto-deploy on push to main branch."
}

run_migrations() {
    echo "🔄 Running database migrations..."
    alembic upgrade head
    echo -e "${GREEN}✅ Migrations complete${NC}"
}

case $ENVIRONMENT in
    local)
        check_requirements
        setup_env
        run_migrations
        run_tests
        deploy_local
        ;;
    docker)
        check_requirements
        setup_env
        deploy_docker
        ;;
    railway)
        check_requirements
        setup_env
        run_migrations
        deploy_railway
        ;;
    render)
        check_requirements
        setup_env
        run_migrations
        deploy_render
        ;;
    migrate)
        run_migrations
        ;;
    test)
        check_requirements
        setup_env
        run_migrations
        run_tests
        ;;
    *)
        echo "Usage: $0 [local|docker|railway|render|migrate|test]"
        echo ""
        echo "Commands:"
        echo "  local     - Start local dev server (uvicorn --reload)"
        echo "  docker    - Build and run Docker container"
        echo "  railway   - Deploy to Railway"
        echo "  render    - Deploy to Render (manual steps)"
        echo "  migrate   - Run database migrations only"
        echo "  test      - Run tests only"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}✅ Done!${NC}"