# Blogger Publishing Action

This GitHub Action will publish pre-rendered HTML articles to a
[Blogger](https://www.blogger.com) (Blogspot) blog using the Blogger API v3.

This action supports:

- **Publishing Drafts**: New posts are created as drafts by default.
- **Conditional Updates**: If a draft post with the same title already exists,
  it updates the existing content and labels. Note that live or scheduled posts
  are not modified to prevent accidental overwrites.
- **Embedded Assets**: Local images referenced in your HTML are automatically
  encoded as JPEG Base64 data URIs. Images wider than 1600 pixels are resized to
  fit.
- **Smart Extraction**: If a full HTML document is provided, the action
  intelligently extracts the body content and internal CSS styles. The header
  section is ignored, allowing you to focus on the article content.
- **OAuth 2.0**: Secure authentication using Google OAuth 2.0 Refresh Tokens.

## Usage

### Prerequisites

To use this action, you need to set up Google API credentials. Please refer to
[docs/authentication_setup.md](docs/authentication_setup.md) for detailed
instructions on how to obtain your:

- `CLIENT_ID`
- `CLIENT_SECRET`
- `REFRESH_TOKEN`
- `BLOG_ID`

### Example Workflow

The recommended step to add to your GitHub Actions workflow (e.g.,
`.github/workflows/publish.yml`) is:

```yaml
- name: Publish to Blogspot
  if: success()
  uses: frankhjung/blogger@v1.3
  with:
    title: "Your Blog Post Title"
    source-file: "path/to/your/article.html"
    labels: "news, linux"
    blog-id: ${{ secrets.BLOGGER_BLOG_ID }}
    client-id: ${{ secrets.BLOGGER_CLIENT_ID }}
    client-secret: ${{ secrets.BLOGGER_CLIENT_SECRET }}
    refresh-token: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
```

Alternatively, to use the image from GHCR, use this instead:

```yaml
- name: publish to blog
  if: success()
  uses: docker://ghcr.io/frankhjung/blogger:v1.3
  with:
    args: >-
      --title "Your Blog Post Title"
      --source-file "path/to/your/article.html"
      --labels "news, linux"
      --blog-id "${{ secrets.BLOGGER_BLOG_ID }}"
      --client-id "${{ secrets.BLOGGER_CLIENT_ID }}"
      --client-secret "${{ secrets.BLOGGER_CLIENT_SECRET }}"
      --refresh-token "${{ secrets.BLOGGER_REFRESH_TOKEN }}"
```

**Note:** Ensure you have defined the necessary secrets in your GitHub
repository settings under **Settings > Secrets and variables > Actions**.

### Inputs

| Input | Description | Required |
| ----- | ----------- | -------- |
| `title` | Title of the blog post | Yes |
| `source-file` | Path to the file containing the HTML content | Yes |
| `labels` | Comma-separated list of labels | No |
| `blog-id` | The ID of your Blogger blog | Yes |
| `client-id` | Google OAuth Client ID | Yes |
| `client-secret` | Google OAuth Client Secret | Yes |
| `refresh-token` | Google OAuth Refresh Token | Yes |

## Local Development

You can build and test this action locally using the provided `Makefile`.

### Local Prerequisites

- [Docker](https://www.docker.com/)
- [Python 3.9+](https://www.python.org/)
- [uv](https://docs.astral.sh/uv/)

### Build Commands

The project includes a `Makefile` to simplify common tasks:

```bash
# Install Python dependencies locally
make install

# Lock and upgrade Python dependencies
make upgrade

# Format, lint, run tests, and generate coverage report
make check

# Build the Docker image for the Action
make build-image

# Run the Docker container (sanity check - prints help)
make test-container
```

### Python Code Quality

#### To format code with ruff, run

```bash
make format
```

#### To lint code with ruff, run

```bash
make lint
```

#### To run tests with coverage, run

```bash
make coverage
```

### Running the Action Locally

You can run the Docker container directly to simulate the Action execution,
provided you have a local file to publish and your credentials.

```bash
docker run --rm -v $(pwd):/data blogger:latest \
  --title "Test Post" \
  --source-file "/data/test_article.html" \
  --labels "test, local" \
  --blog-id "YOUR_BLOG_ID" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --refresh-token "YOUR_REFRESH_TOKEN"
```

## Packages

### To install Python dependencies, run

```bash
make install
```

### To check for outdated Python packages, run

```bash
make outdated
```

### To apply updates to Python packages, run

```bash
make upgrade
```

## Examples

This action is used by the following repositories:

- [frankhjung/article-publish-to-blogspot](https://github.com/frankhjung/article-publish-to-blogspot)
- [frankhjung/article-base-rate](https://github.com/frankhjung/article-base-rate)
