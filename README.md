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

### Testing / Evaluation tests

```bash
# Run all Python tests
uv run pytest

# Run specific agent tests (e.g., reference extractor)
uv run pytest tests/llm/test_reference_extractor.py

# Run tests repeating test cases a specified number of times (with --count)
uv run pytest tests/llm/ --count=3
```

**Test Organization**: Tests are organized by agent in `tests/llm/[agent_name]/` with datasets in `tests/datasets/[agent_name]/`. Each agent can have multiple test datasets (e.g., `basic.yaml`, `common_knowledge.yaml`) sharing common test infrastructure via `conftest.py`.

#### Enhanced Test Results Export

Each test run will by default generate a `test_results.json` file that can be uploaded to a custom UI in the frontend for better visualization, in the `/evals` route.

### Code Quality

```bash
# Format Python code
uv run black .

# Lint frontend code
cd frontend && pnpm lint

# Type check frontend
cd frontend && pnpm type-check
```

## Security Scanning

Security scans run automatically on every PR using [Trivy](https://trivy.dev/) via the official [trivy-action](https://github.com/aquasecurity/trivy-action).

> **Why Trivy?** While Docker Scout is excellent and integrates natively with Docker, we use Trivy for compliance and auditing purposes. Trivy is open-source, vendor-neutral, and widely accepted in enterprise security workflows.

### Local Scanning (Optional)

```bash
# Install Trivy (macOS)
brew install aquasecurity/trivy/trivy

# Scan Docker images (build first with docker compose)
docker compose build
trivy image rand-ai-reviewer-api
trivy image rand-ai-reviewer-frontend
trivy image postgres:16-alpine

# Scan for Docker/config misconfigurations
trivy config .
```

**Note:** Trivy automatically uses `trivy.yaml` configuration (scans HIGH/CRITICAL only, outputs SARIF format).

### Automated PR Scanning

Every PR automatically scans using `aquasecurity/trivy-action@0.28.0`:
- **Docker Images**: Backend, frontend, and PostgreSQL containers
- **Configuration**: Dockerfiles, docker-compose.yml for misconfigurations
- **Built-in Caching**: Vulnerability database cached between runs for faster scans
- **Non-blocking**: Scans run with `exit-code: 0` to warn without failing builds

The action provides:
- Automatic Trivy installation and caching
- Table format output in workflow logs
- Optimized performance with `skip-setup-trivy` for subsequent scans

Results appear in:
1. **PR checks** → Security Scan workflow logs (table format)
2. **Actions tab** → Click workflow run to see detailed scan results

Scans **warn but don't block PRs** - they're informational to help you fix issues.

> **Note:** To upload results to GitHub Security tab, enable GitHub Advanced Security and change `format: table` to `format: sarif` with upload steps.
