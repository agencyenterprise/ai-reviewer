# RAND AI Analyst

An AI-powered document review system that analyzes documents for claims, citations, and references using agent-based workflows. The system consists of a Python backend (FastAPI + LangChain) and a Next.js frontend.

## Features

- **Document Analysis**: Upload and analyze documents for claims and citations
- **AI-Powered Workflows**: Uses LangGraph for orchestrated AI agent workflows
- **Claim Substantiation**: Automatically substantiate claims using supporting documents
- **Modern Stack**: FastAPI backend with Next.js 15 frontend
- **Docker Support**: Full containerization with PostgreSQL database
- **Infrastructure as Code**: Railway deployment with automated CI/CD

## Prerequisites

- **uv**: Fast Python package/dependency manager. Official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- **Node.js 20+**: For the frontend development
- **pnpm**: Fast, disk space efficient package manager for Node.js. Install via npm:

```bash
npm install -g pnpm
```

- **Docker & Docker Compose**: For containerized development

Verify installations:

```bash
uv --version
node --version
pnpm --version
docker --version
docker compose version
```

## Python Version

This project requires **Python 3.13**. The version is pinned in:

- `.python-version` file
- `pyproject.toml` (`requires-python = ">=3.13"`)

uv will automatically install Python 3.13 if it's not present on your system.

## Setup

### Backend Setup

From the project root:

```bash
# Install Python 3.13 if not present
uv python install 3.13

# Create virtual environment and install dependencies from lockfile (reproducible)
uv sync --frozen

# Alternative: Install without enforcing lockfile
# uv sync
```

This creates a local virtual environment at `.venv/` and installs all dependencies from `pyproject.toml` and `uv.lock`.

### Virtual Environment Activation

```bash
# Activate the virtual environment
source .venv/bin/activate

# Verify installation
python --version  # Should show Python 3.13.x
uv run python -c "import fastapi; print('FastAPI installed successfully')"
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies using pnpm (recommended)
pnpm install

# Alternative: using npm
npm install
```

## Running the Application

### Backend (FastAPI)

#### Development Mode

```bash
# From project root with virtual environment activated
uv run fastapi dev api/main.py

# Alternative: using uvicorn directly
uv run uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

```bash
uv run uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Next.js)

#### Development Mode

```bash
# From frontend directory
cd frontend
pnpm dev

# Alternative: using npm
npm run dev
```

#### Production Mode

```bash
# Build the application
pnpm build

# Start production server
pnpm start
```

### Managing dependencies

- **Add a dependency**:

```bash
uv add <package>
```

- **Remove a dependency**:

```bash
uv remove <package>
```

- **Upgrade using the lockfile**:

```bash
uv lock --upgrade && uv sync --frozen
```

## Docker Setup (Recommended)

The project includes comprehensive Docker support with three services:

### Services Overview

- **PostgreSQL Database** (`db`): Port 5432
- **FastAPI Backend** (`api`): Port 8000
- **Next.js Frontend** (`app`): Port 3000

### Docker Files

- **`Dockerfile`**: Backend container (Python 3.13 + FastAPI)
- **`frontend/Dockerfile`**: Frontend container (Node.js 20 + Next.js)
- **`docker-compose.yml`**: Orchestrates all services

### Quick Start

```bash
# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

### Database Migrations

After starting the services, run database migrations:

```bash
# With local Python environment
uv run alembic upgrade head

# Or using the containerized backend
docker compose exec api uv run alembic upgrade head
```

## Deployment

### Railway Deployment (Infrastructure as Code)

This project uses **Infrastructure as Code** through Railway's Config as Code feature. All infrastructure is defined in `railway.toml`.

#### One-Time Setup

1. **Railway Account**: Sign up at [railway.app](https://railway.app)

2. **GitHub Repository Secrets**:
   Go to **Settings** → **Secrets and variables** → **Actions**, add:

   - `RAILWAY_TOKEN`: Get from Railway dashboard → Account → Tokens
   - `RAILWAY_PROJECT_ID`: Your Railway project ID for linking
   - `RAILWAY_SERVICE_ID`: Your application service ID (not the database service)

   **How to find your Service ID:**

   ```bash
   # Run this in your project directory
   railway service list
   # Copy the ID of your application service (not Postgres)
   ```

3. **Environment Variables in Railway**:
   After first deployment, set in your Railway service's **Variables** tab:

   ```
   OPENAI_API_KEY=your_openai_api_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   LANGFUSE_PROJECT_ID=your_langfuse_project_id
   ```

   > **Database variables are automatic**: `railway.toml` references PostgreSQL variables automatically

#### Infrastructure as Code Files

- **`railway.toml`**: Defines build, deployment, and storage configuration
  - PostgreSQL database variables auto-linked
  - Persistent volume for file uploads (`/app/uploads`)
  - Pre-deployment migrations
- **`.github/workflows/deploy.yml`**: Automated CI/CD pipeline
- **`Dockerfile`**: Container configuration

#### Deployment Workflow

- **Push to `main`**:
  1. Creates PostgreSQL service (if doesn't exist)
  2. Deploys application service
  3. Runs database migrations automatically
- **Pull Requests**: Runs build validation checks only

**100% Infrastructure as Code** - PostgreSQL database, environment variable linking, and deployments all automated!

## Environment Variables

Copy the environment template file and fill in the required variables:

```bash
# Copy the template
cp .env.template .env

# Edit the file with your actual values
nano .env  # or use your preferred editor
```

## Development Workflow

### Dependency Management

- **Add a dependency**:

```bash
uv add <package>
```

- **Remove a dependency**:

```bash
uv remove <package>
```

- **Upgrade dependencies**:

```bash
uv lock --upgrade && uv sync --frozen
```

- **Reinstall if environment becomes inconsistent**:

```bash
uv sync --reinstall
```

### Database Management

```bash
# Create a new migration
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback migration
uv run alembic downgrade -1
```

### Testing

```bash
# Run all Python tests
uv run pytest

# Run with coverage
uv run pytest --cov=lib

# Run specific agent tests (e.g., claim substantiator)
uv run pytest tests/llm/claim_substantiator/ -v

# Run frontend tests (when implemented)
cd frontend && pnpm test
```

**Test Organization**: Tests are organized by agent in `tests/llm/[agent_name]/` with datasets in `tests/datasets/[agent_name]/`. Each agent can have multiple test datasets (e.g., `basic.yaml`, `common_knowledge.yaml`) sharing common test infrastructure via `conftest.py`.

#### Enhanced Test Results Export

The test suite includes comprehensive JSON reporting that captures complete test metadata, inputs, outputs, and evaluation results:

```bash
# Generate detailed JSON test results
uv run pytest tests/llm/ -n 10
  -v
```

**Test Results Structure**: Each test in the JSON includes:

- **Test Metadata**: Test name, agent information (name, version)
- **Complete Inputs**: All `prompt_kwargs` (full_document, chunk, claim, references, etc.)
- **Expected Output**: Golden reference for comparison
- **Actual Outputs**: Agent-generated results (supports multiple runs)
- **Evaluation Config**: Which fields use strict comparison vs LLM evaluation
- **Evaluation Results**: Pass/fail status with detailed rationale breaking down strict and LLM comparisons

**Analysis Examples**:

```bash
# View test summary
cat test_results.json | jq '.summary'

# Get all failed tests with evaluation details
cat test_results.json | jq '.tests[] | select(.outcome=="failed") | {
  name: .agent_test_case.name,
  eval_passed: .agent_test_case.evaluation_result.passed,
  rationale: .agent_test_case.evaluation_result.rationale
}'

# Compare expected vs actual severity across all tests
cat test_results.json | jq '.tests[] | {
  name: .agent_test_case.name,
  expected_severity: .agent_test_case.expected_output.severity,
  actual_severity: .agent_test_case.actual_outputs[0].severity
}'

# Evaluate pass rate by agent
cat test_results.json | jq '[.tests[] | {
  agent: .agent_test_case.agent.name,
  passed: .agent_test_case.evaluation_result.passed
}] | group_by(.agent) | map({
  agent: .[0].agent,
  total: length,
  passed: ([.[] | select(.passed)] | length),
  pass_rate: (([.[] | select(.passed)] | length) / length * 100 | round)
})'
```

This structured output enables systematic analysis of agent performance, identification of failure patterns, and tracking of improvements over time.

### Code Quality

```bash
# Format Python code
uv run black .

# Lint frontend code
cd frontend && pnpm lint

# Type check frontend
cd frontend && pnpm type-check
```
