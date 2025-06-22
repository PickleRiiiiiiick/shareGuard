# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShareGuard is a Windows file system permissions scanner and monitoring tool that audits and tracks access permissions on shared folders. It consists of a FastAPI backend (Python) and a React frontend (TypeScript).

## Common Development Commands

### Running the Application

```powershell
# Start both backend and frontend (opens two PowerShell windows)
.\startProject.ps1

# Or run separately:
.\start-backend.ps1  # Backend: activates venv, runs uvicorn app:app --reload
.\start-frontend.ps1  # Frontend: cd src/web && npm run dev
```

### Frontend Development

```bash
cd src/web
npm install          # Install dependencies
npm run dev         # Start Vite dev server on localhost:5173
npm run build       # Production build
npm run lint        # Run ESLint
npm run typecheck   # TypeScript type checking
```

### Database Management

```bash
# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Running Tests

Backend tests are standalone Python scripts:
```bash
python test_api.py              # API endpoint tests
python test_auth.py             # Authentication tests
python test_basic_scanning.py   # Core scanning tests
python test_user_access.py      # User access pattern tests
```

PowerShell test:
```powershell
.\Test-GroupResolver.ps1        # Group resolver functionality
```

## Architecture

### Backend Structure
- **src/app.py**: FastAPI application entry point
- **src/api/**: API routes organized by feature (auth, scan, targets, cache, folders, users)
- **src/core/scanner.py**: Core scanning orchestration logic
- **src/scanner/**: Windows-specific permission scanning implementation
- **src/db/**: SQLAlchemy models and database configuration
- **src/api/middleware/auth.py**: JWT authentication middleware

### Frontend Structure
- **src/web/src/**: React application root
- **src/web/src/api/**: API client modules for each backend service
- **src/web/src/components/**: Reusable UI components organized by feature
- **src/web/src/contexts/**: React contexts (Auth, Alert)
- **src/web/src/hooks/**: Custom React hooks for data fetching
- **src/web/src/pages/**: Top-level page components
- **src/web/src/types/**: TypeScript type definitions

### Key Technologies
- **Backend**: FastAPI, SQLAlchemy, Alembic, pywin32, PyJWT, pyodbc (SQL Server)
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, React Query, Zustand

### API Patterns
- All API routes are prefixed with `/api/v1/`
- Authentication uses JWT tokens in Authorization header
- Pagination uses `skip` and `limit` query parameters
- API documentation available at `/docs` when backend is running

### Database Connection
The application uses SQL Server via ODBC. Connection string is configured in:
- `alembic.ini` for migrations
- `config/settings.py` for runtime

### Development Notes
- CORS is configured for localhost:5173 (frontend) and localhost:8000 (backend)
- Logs are written to the `logs/` directory with daily rotation
- The scanner requires Windows admin privileges to read NTFS permissions
- Test data uses C:\ShareGuardTest\* paths