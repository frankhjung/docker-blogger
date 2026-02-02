import argparse
import logging
import os
import sys

from blogspot_publishing.publish import publish_post

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Publish content to Blogspot.")

    parser.add_argument("--title", required=True, help="Title of the blog post")
    parser.add_argument(
        "--source-file",
        required=True,
        help="Path to the file containing the post content (HTML)",
    )
    parser.add_argument("--blog-id", required=True, help="Blogger Blog ID")
    parser.add_argument("--client-id", required=True, help="OAuth Client ID")
    parser.add_argument("--client-secret", required=True, help="OAuth Client Secret")
    parser.add_argument("--refresh-token", required=True, help="OAuth Refresh Token")
    parser.add_argument(
        "--labels",
        help="Comma-separated list of labels",
        default="",
    )

    args = parser.parse_args()

    # Read content
    if not os.path.exists(args.source_file):
        logger.error(f"Source file not found: {args.source_file}")
        sys.exit(1)

    with open(args.source_file, encoding="utf-8") as f:
        content = f.read()

    # Parse labels
    labels_list = [l.strip() for l in args.labels.split(",")] if args.labels else []

    try:
        publish_post(
            client_id=args.client_id,
            client_secret=args.client_secret,
            refresh_token=args.refresh_token,
            blog_id=args.blog_id,
            title=args.title,
            content=content,
            labels=labels_list,
        )
    except Exception as e:
        logger.error(f"Failed to publish post: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
