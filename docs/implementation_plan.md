# Implementation Plan - Blogspot Publishing GitHub Action

## Goal Description

Create a GitHub Action that uses the Blogger API v3 to publish articles
(Markdown/HTML) to a Blogspot blog. The action will be a Docker container action
written in Python, published to the GitHub Container Registry.

## User Review Required
> 
> [!IMPORTANT] **Authentication Method**: The Plan mentions "API key". However,
> publishing posts (write access) requires **OAuth 2.0** or a **Service
> Account**. An API key is strictly for read-only public data.
> 
> **Proposed Solution**: The Action will support **Service Account Credentials**
> (passed as a JSON string secret) OR **OAuth 2.0 Client Credentials** (Client
> ID, Client Secret, Refresh Token). I will implement support for a Service
> Account JSON as it is often easier for server-to-server automation, but I will
> also document how to use OAuth 2.0 keys if preferred. **Question**: Do you
> prefer Service Account or OAuth 2.0 Refresh Token flow? (I will assume Service
> Account for now as it's cleaner for Actions, but let me know).

## Proposed Changes

### Configuration

#### [MODIFY] [pyproject.toml](file:///home/frank/documents/articles/blogger/pyproject.toml)

- Add dependencies:
  - `google-api-python-client`
  - `google-auth`
  - `google-auth-httplib2`
  - `google-auth-oauthlib`
  - `markdown` (to convert MD to HTML if needed, though `PLAN.md` says
    "Assume... renders... into HTML", point 14. If the input is already HTML, we
    might not need this, but point 6 says "publish an article (either markdown
    or HTML)". I will add `markdown` just in case).
- Add `click` or `typer` for CLI interface.

### Source Code

#### [NEW] [src/blogger/publish.py](file:///home/frank/documents/articles/blogger/src/blogger/publish.py)

- Implement `publish_post` function.
- Handle authentication (Service Account or OAuth).
- Logic to:
  - Search for existing post by Title (to update instead of create duplicate?
    `PLAN.md` doesn't strictly say update, but "publish... to my blogspot"
    usually implies idempotency. Point 23 just lists parameters. I will
    implement "Create new" logic first, maybe "Update if exists" as a stretch or
    if title matches). *Correction*: `PLAN.md` doesn't explicitly ask for
    update. I will stick to "Create Draft" for now as per point 30.
  - Construct the post body.
  - Call `blogger.posts().insert()`.

#### [NEW] [src/blogger/main.py](file:///home/frank/documents/articles/blogger/src/blogger/main.py)

- CLI entrypoint using `argparse` or `click`.
- Parse arguments: `title`, `url` (source file path), `blog_id`, `credentials`,
  `labels`.

### GitHub Action

#### [NEW] [action.yml](file:///home/frank/documents/articles/blogger/action.yml)

- Define inputs: `blog-id`, `title`, `source-file`, `credentials-json`,
  `labels`.
- Define runs: `using: 'docker'`, `image: 'Dockerfile'`.

#### [NEW] [Dockerfile](file:///home/frank/documents/articles/blogger/Dockerfile)

- Base image `python:3.11-slim`.
- Install `uv`.
- Install dependencies.
- Copy src.
- Entrypoint: `python -m blogger.main`.

### CI/CD

#### [NEW] [.github/workflows/publish-action.yml](file:///home/frank/documents/articles/blogger/.github/workflows/publish-action.yml)

- Build and publish Docker image to GHCR on release or push to main.

## Verification Plan

### Automated Tests

- Run `pytest` for unit tests (mocking the Google API).
- Create `tests/test_publish.py`.

### Manual Verification

- **Local Run**:
  - Create a dummy `credentials.json` (user provided).
  - Run `python -m blogger.main ...` targeting a test blog.
- **GitHub Action Dry Run**:
  - Since we cannot easily run the Action locally without act, we will rely on
    unit tests and careful code review.
