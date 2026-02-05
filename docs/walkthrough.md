# Blogspot Publishing Action Walkthrough

I have successfully implemented the GitHub Action to publish articles to
Blogspot.

## Changes Created

### 1. Application Logic

* **`src/blogger/publish.py`**: Contains the core logic to authenticate with
  OAuth 2.0 and publish posts. It implements the "idempotency" rule: searching
  for an existing post by title and updating it if found (preserving the title
  but replacing content), otherwise creating a new draft.
* **`src/blogger/main.py`**: The CLI entrypoint using `argparse`.
* **`tests/test_publish.py`**: Unit tests verifying the logic.

### 2. Configuration & Dependencies

* **`pyproject.toml`**: Added `google-api-python-client` and `google-auth`
  libraries.
* **`Dockerfile`**: Defines the container environment, installing dependencies
  with `uv`.
* **`action.yml`**: Defines the GitHub Action inputs (`title`, `source-file`,
  `blog-id`, etc.) and mapped them to the CLI arguments.

### 3. CI/CD

* **`.github/workflows/publish-action.yml`**: A workflow that automatically
  builds and publishes the Docker image to the GitHub Container Registry (GHCR)
  when changes are pushed to `main`.

### 4. Documentation

* **`README.md`**: Updated with comprehensive usage instructions and local
  development guide.
* **`Makefile`**: Added `build-image` and `test-container` targets for local
  Docker testing.
* **`docs/authentication_setup.md`**: Detailed instructions on how to set up a
  Google Cloud Project, enable the Blogger API, create OAuth Client Credentials,
  and obtain a Refresh Token for GitHub Secrets.

## Verification Results

### Automated Tests

Ran `make install && make test`.

* All tests passed, verifying the "insert vs update" logic and handling of API
  responses.

### Manual Verification

* Checked `action.yml` against the CLI implementation to ensure argument mapping
  is correct.

## Next Steps for You

1. Follow the instructions in `docs/authentication_setup.md` to get your
   `CLIENT_ID`, `CLIENT_SECRET`, and `REFRESH_TOKEN`.
2. Add these as Repository Secrets in your GitHub repo.
3. Use the action in your blog's workflow!

```yaml
- name: Publish to Blogspot
  uses: ./ # or your-username/blogger-action@main
  with:
    title: "My Post Title"
    source-file: "path/to/post.html"
    blog-id: ${{ secrets.BLOGGER_BLOG_ID }}
    client-id: ${{ secrets.BLOGGER_CLIENT_ID }}
    client-secret: ${{ secrets.BLOGGER_CLIENT_SECRET }}
    refresh-token: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
    labels: "tech,python"
```
