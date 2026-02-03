import base64
import logging
import mimetypes
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Optional, cast

import google.auth.exceptions
from bs4 import BeautifulSoup
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build  # type: ignore
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/blogger"]


def _encode_images_in_html(
    html_content: str, base_path: Optional[Path] = None
) -> str:
    """
    Encode local images in HTML as Base64 data URIs.

    Scans HTML for img tags with local file paths and converts them to
    embedded Base64 data URIs. This allows images to be embedded directly
    in the HTML without external references.

    Parameters
    ----------
    html_content : str
        HTML content containing img tags.
    base_path : Path | None, optional
        Base directory for resolving relative image paths. If None, uses
        current working directory. Default is None.

    Returns
    -------
    str
        HTML content with local image paths converted to Base64 data URIs.

    Notes
    -----
    - External URLs (http://, https://) are left unchanged
    - Already-encoded data URIs are left unchanged
    - Missing local files are logged as warnings
    - Supported image types: jpg, jpeg, png, gif, webp, svg
    """
    if base_path is None:
        base_path = Path.cwd()

    soup = BeautifulSoup(html_content, "html.parser")
    img_tags = soup.find_all("img")

    for img in img_tags:
        src = img.get("src", "")

        # Skip external URLs and data URIs
        if isinstance(src, str) and src.startswith(
            ("http://", "https://", "data:")
        ):
            continue

        # Ensure src is a string for path operations
        src_str = str(src) if src else ""
        if not src_str:
            continue

        # Try to load the image file
        img_path: Path = (
            base_path / src_str
            if not Path(src_str).is_absolute()
            else Path(src_str)
        )

        if not img_path.exists():
            logger.warning(f"Image file not found: {img_path}")
            continue

        try:
            # Read image and encode as Base64
            with open(img_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(str(img_path))
            if mime_type is None:
                mime_type = "application/octet-stream"

            # Create data URI
            data_uri = f"data:{mime_type};base64,{image_data}"
            img["src"] = data_uri
            logger.debug(f"Encoded image: {img_path} ({mime_type})")

        except Exception as e:
            logger.warning(f"Failed to encode image {img_path}: {e}")

    return str(soup)


def get_service(
    client_id: str, client_secret: str, refresh_token: str
) -> Resource:
    """
    Authenticate and return the Blogger API service.

    Uses OAuth 2.0 refresh token to obtain credentials and build the
    Blogger API v3 service instance.

    Parameters
    ----------
    client_id : str
        Google OAuth 2.0 Client ID.
    client_secret : str
        Google OAuth 2.0 Client Secret.
    refresh_token : str
        Google OAuth 2.0 Refresh Token.

    Returns
    -------
    Resource
        An authenticated Blogger API v3 service resource.

    Raises
    ------
    google.auth.exceptions.RefreshError
        If token refresh fails due to invalid credentials.
    google.auth.exceptions.GoogleAuthError
        If other authentication errors occur.
    """
    creds = Credentials(
        None,  # Access token is None, it will be refreshed
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=SCOPES,
    )
    return cast(
        Resource,
        build("blogger", "v3", credentials=creds, static_discovery=False),
    )


def _iterate_all_posts(
    service: Any,  # Changed from Resource to Any
    blog_id: str,
) -> Iterator[dict[str, Any]]:
    """
    Generate all posts from paginated Blogger API.

    Handles pagination automatically, yielding each post from all
    pages. Only includes draft and scheduled posts (not published).

    Parameters
    ----------
    service : Any  # Changed from googleapiclient.discovery.Resource to Any
        Authenticated Blogger API service instance.
    blog_id : str
        ID of the Blogger blog to search.

    Yields
    ------
    dict[str, Any]
        Individual post resources from the blog.

    Raises
    ------
    google.auth.exceptions.RefreshError
        If token refresh fails during API call.
    googleapiclient.errors.HttpError
        If API request fails.
    """
    # Only search DRAFT and SCHEDULED posts for updates
    request = service.posts().list(
        blogId=blog_id, status=["DRAFT", "SCHEDULED"]
    )
    while request:
        response = request.execute()
        items = response.get("items", [])
        logger.debug(
            f"Retrieved {len(items)} posts from API, "
            f"available fields: {list(items[0].keys()) if items else 'none'}"
        )
        yield from items
        request = service.posts().list_next(request, response)


def find_post_by_title(
    service: Any,  # Changed from Resource to Any
    blog_id: str,
    title: str,
) -> Optional[dict[str, Any]]:
    """
    Search for a blog post by exact title.

    Searches the blog for a post with the exact title match.
    Uses full-text search API with manual filtering for precision.

    Parameters
    ----------
    service : Any  # Changed from googleapiclient.discovery.Resource to Any
        Authenticated Blogger API service instance.
    blog_id : str
        ID of the Blogger blog to search.
    title : str
        Exact title to match.

    Returns
    -------
    dict[str, Any] | None
        Post resource dict if found, None otherwise.

    Raises
    ------
    google.auth.exceptions.RefreshError
        If token refresh fails during API call.
    googleapiclient.errors.HttpError
        If API request fails.

    Examples
    --------
    >>> post = find_post_by_title(service, "blog123", "My Post")
    >>> if post:
    ...     print(f"Found post: {post['id']}")
    """
    try:
        posts = list(_iterate_all_posts(service, blog_id))
        logger.debug(f"Found {len(posts)} total posts in blog")

        matching = [post for post in posts if post.get("title") == title]

        if matching:
            matched_post = matching[0]
            logger.info(
                f"Found existing post with title '{title}' (ID: {matched_post.get('id')}, "  # noqa: E501
                f"Status: {matched_post.get('status', 'unknown')})"
            )
            return matched_post
        else:
            logger.debug(f"No post found with title '{title}'")
            if posts:
                available_titles = [p.get("title", "NO_TITLE") for p in posts]
                available_statuses = [
                    p.get("status", "unknown") for p in posts
                ]
                logger.debug(f"Available post titles: {available_titles}")
                logger.debug(f"Available post statuses: {available_statuses}")
                # Check for partial matches or case issues
                for post in posts:
                    post_title = post.get("title", "")
                    if post_title.lower() == title.lower():
                        logger.warning(
                            f"Found case-insensitive match: '{post_title}' vs '{title}'"  # noqa: E501
                        )
            return None
    except google.auth.exceptions.RefreshError as e:
        logger.error(f"Authentication failed: {e}")
        raise
    except HttpError as e:
        logger.error(f"Error searching for post: {e}")
        raise


def _execute_api_call(api_func: Any, operation_name: str) -> dict[str, Any]:
    """
    Execute API call with consistent error handling.

    Executes a Blogger API call and handles authentication and API
    errors uniformly.

    Parameters
    ----------
    api_func : callable
        A callable that returns the API request (e.g.,
        service.posts().insert(...)).
    operation_name : str
        Human-readable name of the operation for logging.

    Returns
    -------
    dict[str, Any]
        Response from the API call.

    Raises
    ------
    google.auth.exceptions.RefreshError
        If token refresh fails.
    googleapiclient.errors.HttpError
        If API request fails.
    """
    try:
        return api_func().execute()
    except google.auth.exceptions.RefreshError as e:
        logger.error(f"Authentication failed during {operation_name}: {e}")
        raise
    except HttpError as e:
        logger.error(f"Failed to {operation_name}: {e}")
        raise


def publish_post(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    blog_id: str,
    title: str,
    content: str,
    labels: Optional[list[str]] = None,
    is_draft: bool = True,
    source_file_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Publish or update a post to Blogspot.

    Creates a new draft post or updates existing post by title.
    If a post with matching title exists, updates its content.
    Otherwise, creates a new post as a draft.

    Automatically encodes any local images in the content as Base64
    data URIs for embedding in the blog.

    Parameters
    ----------
    client_id : str
        Google OAuth 2.0 Client ID.
    client_secret : str
        Google OAuth 2.0 Client Secret.
    refresh_token : str
        Google OAuth 2.0 Refresh Token.
    blog_id : str
        ID of the target Blogger blog.
    title : str
        Title of the blog post.
    content : str
        HTML content of the blog post.
    labels : list[str] | None, optional
        List of labels/tags to assign to the post. Default is None.
    is_draft : bool, optional
        Whether to create post as draft. Default is True.
    source_file_path : str | None, optional
        Path to source HTML file. Used as base directory for resolving
        relative image paths. If None, uses current working directory.
        Default is None.

    Returns
    -------
    dict[str, Any]
        The published/updated post resource from Blogger API.

    Raises
    ------
    google.auth.exceptions.RefreshError
        If token refresh fails during authentication or API calls.
    google.auth.exceptions.GoogleAuthError
        If other authentication errors occur.
    Exception
        For other API errors; error is logged and re-raised.

    Examples
    --------
    >>> result = publish_post(
    ...     "client_id",
    ...     "client_secret",
    ...     "refresh_token",
    ...     "blog123",
    ...     "My Post",
    ...     "<p>Content</p>",
    ...     labels=["python", "tutorial"],
    ...     source_file_path="/path/to/post.html"
    ... )
    >>> print(f"Published: {result['url']}")
    """
    # Encode images in content
    base_path = None
    if source_file_path:
        base_path = Path(source_file_path).parent

    content = _encode_images_in_html(content, base_path)

    service = get_service(client_id, client_secret, refresh_token)
    existing_post = find_post_by_title(service, blog_id, title)

    body: dict[str, Any] = {"title": title, "content": content}
    if labels:
        body["labels"] = labels

    if existing_post:
        logger.info(
            f"Found existing post with ID {existing_post['id']}. Updating..."
        )
        updated = _execute_api_call(
            lambda: service.posts().update(
                blogId=blog_id,
                postId=existing_post["id"],
                body=body,
            ),
            "update post",
        )
        logger.info(f"Successfully updated post: {updated.get('url')}")
        return updated
    else:
        logger.info("No existing post found. Creating new draft...")
        created = _execute_api_call(
            lambda: service.posts().insert(
                blogId=blog_id, body=body, isDraft=is_draft
            ),
            "create post",
        )
        logger.info(f"Successfully created post: {created.get('url')}")
        return created
