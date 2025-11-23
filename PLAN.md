# Implementation Plan

This document outlines the step-by-step implementation plan to modernize the Quran Center application, migrating it to a robust, secure, and scalable architecture.

## Strategy
*   **Iterative Approach:** Each step is a self-contained Pull Request (PR).
*   **Verification:** Every PR must pass CI checks and include verification instructions.
*   **No Regressions:** Existing functionality (Teacher/Parent portals, Reports) must remain operational.

---

## Phase 1: Foundation & Security (PRs 01-05)

### PR-01: Database Migration & Password Hardening
*   **Goal:** Migrate from SQLite to MySQL and secure user credentials.
*   **Scope:**
    *   Scripts to dump SQLite and import to MySQL (`scripts/migrate_sqlite_to_mysql.sh`, `scripts/dump_sqlite_py.py`).
    *   Password rehashing script (`scripts/rehash_plain_passwords.py`).
    *   Update `app.py` to support `DATABASE_URL` env var.
    *   Idempotent Admin initialization.
    *   Docker Compose for local MySQL.
*   **Verification:** Successful data migration and login with rehashed passwords.

### PR-02: Flask-Migrate (Alembic) + Unified Models
*   **Goal:** Establish a proper database migration system.
*   **Scope:**
    *   Initialize Flask-Migrate (`flask db init`).
    *   Refactor `app.py` to move models into `models.py` (optional but recommended for clarity, or keep in app.py if strictly monolithic, but Alembic setup is key).
    *   Generate initial migration for the existing schema.
    *   Add the `password_needs_rehash` column via migration.
*   **Verification:** `flask db upgrade` works on a fresh DB; `flask db downgrade` works.

### PR-03: Safe Uploader Module & S3 Adapter
*   **Goal:** Secure file uploads and support cloud storage.
*   **Scope:**
    *   Create a strict file validation module (extensions, magic numbers).
    *   Abstract storage backend (Local filesystem vs S3).
    *   Update upload endpoints in `app.py` to use this module.
*   **Verification:** Uploading a malicious file fails; valid files persist in the configured storage.

### PR-04: Auth Hardening (Bcrypt, Reset, MFA Scaffold)
*   **Goal:** Modernize authentication.
*   **Scope:**
    *   Replace `werkzeug.security` with `passlib` (Argon2/Bcrypt).
    *   Implement Password Reset flow (Email token).
    *   Add database fields for MFA (TOTP secret) - scaffold only.
*   **Verification:** Login works with new hashing; Password reset email is sent.

### PR-05: RBAC Central Enforcement
*   **Goal:** Strict Role-Based Access Control.
*   **Scope:**
    *   Create explicit decorators `@require_permission('feature_name')`.
    *   Centralize permission logic (moving away from ad-hoc `if session['role']` where possible, or standardizing it).
    *   Unit tests for permission denial.
*   **Verification:** Users cannot access routes not assigned to their role.

---

## Phase 2: API & Observability (PRs 06-10)

### PR-06: REST API Versioning & Swagger
*   **Goal:** Expose a clean API for future mobile apps or frontend decoupling.
*   **Scope:**
    *   Create Blueprint for `/api/v1/`.
    *   Integrate Swagger/OpenAPI (e.g., `flasgger`).
    *   Move existing JSON endpoints to the API blueprint.
*   **Verification:** `/api/docs` shows interactive documentation.

### PR-07: Security Middleware (CSRF, Rate Limiting)
*   **Goal:** Protect against common web attacks.
*   **Scope:**
    *   Integrate `Flask-WTF` for CSRF protection globally.
    *   Add `Flask-Limiter` for rate limiting login/API endpoints.
    *   Add Security Headers (HSTS, CSP, X-Frame-Options).
*   **Verification:** POST requests without CSRF token fail; Spamming login triggers 429.

### PR-08: Logging & Monitoring
*   **Goal:** Production-grade observability.
*   **Scope:**
    *   Configure JSON logging (structlog or python-json-logger).
    *   Add Sentry SDK integration.
    *   Add Prometheus metrics endpoint (`/metrics`).
*   **Verification:** Logs are structured JSON; Metrics endpoint returns data.

### PR-09: Docker Production Setup
*   **Goal:** Containerize for production.
*   **Scope:**
    *   Optimized `Dockerfile` (multi-stage).
    *   `docker-compose.prod.yml` (Nginx reverse proxy, Gunicorn).
    *   Nginx configuration.
*   **Verification:** `docker-compose up` brings up the full stack locally.

### PR-10: CI/CD Pipeline
*   **Goal:** Automated testing and linting.
*   **Scope:**
    *   GitHub Actions workflow (`.github/workflows/main.yml`).
    *   Steps: Lint (flake8/black), Test (pytest), Build Docker Image.
*   **Verification:** Pushing code triggers a successful green build.

---

## Phase 3: Quality & Features (PRs 11-15)

### PR-11: Test Coverage Expansion
*   **Goal:** Reach >= 70% coverage.
*   **Scope:**
    *   Write unit tests for core business logic (Reports, Attendance).
    *   Write integration tests for critical flows.
*   **Verification:** `pytest --cov` report shows >70%.

### PR-12: Frontend Polish
*   **Goal:** Fix responsive issues and standardize UI.
*   **Scope:**
    *   Implement a consistent design system (CSS variables).
    *   Fix flagged mobile responsiveness issues (Tables, Nav).
*   **Verification:** UI looks good on Mobile and Desktop.

### PR-13: Reporting & Dashboarding
*   **Goal:** Enhanced insights.
*   **Scope:**
    *   Improve PDF export (styling, fonts).
    *   Add Chart.js visualization to Admin Dashboard.
*   **Verification:** PDF downloads correctly; Charts render data accurately.

### PR-14: Operational Scripts
*   **Goal:** Maintenance tools.
*   **Scope:**
    *   Backup/Restore scripts (S3/Local).
    *   `smoke_test.sh` for post-deployment checks.
*   **Verification:** Backup script produces a valid archive.

### PR-15: Final Documentation & Release
*   **Goal:** Handoff.
*   **Scope:**
    *   Generate ERD (Entity Relationship Diagram).
    *   Final `README_PROD.md`.
    *   `setup_production.sh` helper.
*   **Verification:** Documentation is complete and accurate.
