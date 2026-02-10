import argparse
import logging
import sys
from pathlib import Path

from blogger import __version__
from blogger.publish import publish_post

logger = logging.getLogger(__name__)


def main():
    """CLI entry point to publish a blog post to Blogspot."""
    parser = argparse.ArgumentParser(
        prog="blogger", description="Publish content to Blogspot."
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )
    parser.add_argument("--title", required=True, help="Post title")
    parser.add_argument(
        "--source-file", required=True, help="Source HTML file"
    )
    parser.add_argument("--blog-id", required=True, help="Blogger Blog ID")
    parser.add_argument("--client-id", required=True, help="OAuth Client ID")
    parser.add_argument(
        "--client-secret", required=True, help="OAuth Client Secret"
    )
    parser.add_argument(
        "--refresh-token", required=True, help="OAuth Refresh Token"
    )
    parser.add_argument("--labels", default="", help="Comma-separated labels")

    args = parser.parse_args()
    source = Path(args.source_file)

    if not source.exists():
        logger.error(f"Source file not found: {source}")
        sys.exit(1)

    try:
        publish_post(
            client_id=args.client_id,
            client_secret=args.client_secret,
            refresh_token=args.refresh_token,
            blog_id=args.blog_id,
            title=args.title,
            content=source.read_text(encoding="utf-8"),
            labels=[L.strip() for L in args.labels.split(",")]
            if args.labels
            else [],
            source_file_path=str(source),
        )
    except Exception as e:
        logger.error(f"Failed to publish post: {e}")
        sys.exit(1)
