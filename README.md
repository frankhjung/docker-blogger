# Blogspot Publishing Action

A GitHub Action to publish articles (HTML/Markdown) to a [Blogger](https://www.blogger.com) (Blogspot) blog using the Blogger API v3.

This action supports:

- **Publishing Drafts**: New posts are created as drafts by default.
- **Idempotency**: If a post with the same title already exists, it updates the existing post (content only) instead of creating a duplicate.
- **OAuth 2.0**: Secure authentication using Google OAuth 2.0 Refresh Tokens.

## Usage

### Prerequisites

To use this action, you need to set up Google API credentials.
Please refer to [docs/authentication_setup.md](docs/authentication_setup.md) for detailed instructions on how to obtain your:

- `CLIENT_ID`
- `CLIENT_SECRET`
- `REFRESH_TOKEN`
- `BLOG_ID`

### Example Workflow

Add this step to your GitHub Actions workflow (e.g., `.github/workflows/publish.yml`):

```yaml
steps:
  - name: Checkout code
    uses: actions/checkout@v4

  - name: Render Markdown to HTML
    # Assuming you have a step that generates the HTML content
    run: |
      pandoc post.md -o post.html

  - name: Publish to Blogspot
    uses: frankhjung/blogspot-publishing@main
    with:
      title: "My Awesome Post"
      source-file: "post.html"
      blog-id: ${{ secrets.BLOGGER_BLOG_ID }}
      client-id: ${{ secrets.BLOGGER_CLIENT_ID }}
      client-secret: ${{ secrets.BLOGGER_CLIENT_SECRET }}
      refresh-token: ${{ secrets.BLOGGER_REFRESH_TOKEN }}
      labels: "tech, tutorial"
```

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `title` | Title of the blog post | Yes | |
| `source-file` | Path to the file containing the HTML content | Yes | |
| `blog-id` | The ID of your Blogger blog | Yes | |
| `client-id` | Google OAuth Client ID | Yes | |
| `client-secret` | Google OAuth Client Secret | Yes | |
| `refresh-token` | Google OAuth Refresh Token | Yes | |
| `labels` | Comma-separated list of labels | No | |

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

# Run unit tests
make test

# Build the Docker image for the Action
make build-image

# Run the Docker container (sanity check - prints help)
make test-container
```

### Running the Action Locally

You can run the Docker container directly to simulate the Action execution, provided you have a local file to publish and your credentials.

```bash
docker run --rm \
  -v $(pwd):/data \
  blogspot-publishing \
  --title "Test Post" \
  --source-file "/data/test_article.html" \
  --blog-id "YOUR_BLOG_ID" \
  --client-id "YOUR_CLIENT_ID" \
  --client-secret "YOUR_CLIENT_SECRET" \
  --refresh-token "YOUR_REFRESH_TOKEN"
```
