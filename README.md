## rand-ai-reviewer

Minimal Python project managed with uv.

### Prerequisites

- **uv**: Fast Python package/dependency manager. Official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- Verify:

```bash
uv --version
```

Python 3.13 is required and will be handled by uv (it can auto-install it if missing).

### Setup

From the project root:

```bash
# Sync env from lockfile (reproducible)
uv sync --frozen

# If you don't want to enforce the lockfile, use:
# uv sync
```

This creates a local virtual environment at `.venv/` and installs dependencies from `pyproject.toml` / `uv.lock`.

If Python 3.13 is not present, install it via uv:

```bash
uv python install 3.13
```

### Run

Execute the app using uv (no manual activation needed):

```bash
uv run python main.py
```

Streamlit (temporary UI for PoC)

```
streamlit run streamlit/main.py
```

### Optional: activate the virtual environment

```bash
source .venv/bin/activate
python main.py
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

### Docker Setup (Recommended)

The simplest way to get started:

```bash
# Start the database and app services
docker compose up -d

# Run database migrations
uv run alembic upgrade head
```

That's it! The PostgreSQL database will be running on port 5432 and your app will be available.

## Deployment

### Railway Deployment (Infrastructure as Code)

This project uses **Infrastructure as Code** through Railway's Config as Code feature. All infrastructure is defined in `railway.toml`.

#### One-Time Setup

1. **Railway Account**: Sign up at [railway.app](https://railway.app)

2. **GitHub Repository Secrets**:
   Go to **Settings** → **Secrets and variables** → **Actions**, add:
   - `RAILWAY_TOKEN`: Get from Railway dashboard → Account → Tokens
   - `RAILWAY_PROJECT_ID` (optional): Your Railway project ID for linking

3. **Environment Variables in Railway**:
   After first deployment, set in your Railway service's **Variables** tab:
   ```
   OPENAI_API_KEY=your_openai_api_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key  
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```
   
   > **Database variables are automatic**: `railway.toml` references PostgreSQL variables automatically

#### Infrastructure as Code Files

- **`railway.toml`**: Defines build and deployment configuration
- **`.github/workflows/deploy.yml`**: Automated CI/CD pipeline
- **`Dockerfile`**: Container configuration

#### Deployment Workflow

- **Push to `main`**: 
  1. Creates PostgreSQL service (if doesn't exist)
  2. Deploys application service
  3. Runs database migrations automatically
- **Pull Requests**: Runs build validation checks only  

**100% Infrastructure as Code** - PostgreSQL database, environment variable linking, and deployments all automated!

### Environment Variables

Required environment variables (set in Railway for production, `.env` for local):

```bash
# AI/ML Services
OPENAI_API_KEY=your_openai_api_key

# Langfuse (observability)
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key  
LANGFUSE_HOST=https://cloud.langfuse.com

# Database (Railway provides DATABASE_URL automatically)
DATABASE_URL=postgresql://user:password@host:port/database
```

**Local Development**: Create a `.env` file in the project root:
```bash
# Copy this template and fill in your values
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_HOST=https://cloud.langfuse.com
DATABASE_URL=postgresql://rand_user:rand_password@localhost:5432/rand_ai_reviewer
EOF
```

### Notes

- Python version is pinned to 3.13 via `.python-version` and `pyproject.toml`.
- Use `uv sync --reinstall` if your environment becomes inconsistent.
- Database runs on port `5432`
