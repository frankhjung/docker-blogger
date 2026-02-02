import logging
from typing import Any, Optional

import google.auth.exceptions
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build  # type: ignore

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/blogger"]


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
    googleapiclient.discovery.Resource
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
    return build("blogger", "v3", credentials=creds)


def find_post_by_title(
    service: Resource, blog_id: str, title: str
) -> Optional[dict[str, Any]]:
    """
    Search for a blog post by exact title.

    Searches the blog for a post with the exact title match.
    Uses full-text search API with manual filtering for precision.

    Parameters
    ----------
    service : googleapiclient.discovery.Resource
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
    google.auth.exceptions.GoogleAuthError
        If other authentication errors occur.

    Examples
    --------
    >>> post = find_post_by_title(service, "blog123", "My Post")
    >>> if post:
    ...     print(f"Found post: {post['id']}")
    """
    try:
        request = service.posts().list(blogId=blog_id, fetchBodies=False)
        while request:
            response = request.execute()
            items = response.get("items", [])
            matches = [item for item in items if item["title"] == title]
            if matches:
                return matches[0]
            request = service.posts().list_next(request, response)
    except google.auth.exceptions.RefreshError as e:
        logger.error(f"Authentication failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error searching for post: {e}")
        raise
    return None


def publish_post(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    blog_id: str,
    title: str,
    content: str,
    labels: Optional[list[str]] = None,
    is_draft: bool = True,
) -> dict[str, Any]:
    """
    Publish or update a post to Blogspot.

    Creates a new draft post or updates existing post by title.
    If a post with matching title exists, updates its content.
    Otherwise, creates a new post as a draft.

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
    ...     labels=["python", "tutorial"]
    ... )
    >>> print(f"Published: {result['url']}")
    """
    service = get_service(client_id, client_secret, refresh_token)
    existing_post = find_post_by_title(service, blog_id, title)

    body: dict[str, Any] = {"title": title, "content": content}
    if labels:
        body["labels"] = labels

    if existing_post:
        logger.info(
            f"Found existing post with ID {existing_post['id']}. Updating..."
        )
        try:
            updated = (
                service.posts()
                .update(blogId=blog_id, postId=existing_post["id"], body=body)
                .execute()
            )
            logger.info(f"Successfully updated post: {updated.get('url')}")
            return updated
        except google.auth.exceptions.RefreshError as e:
            logger.error(f"Authentication failed during update: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update post: {e}")
            raise
    else:
        logger.info("No existing post found. Creating new draft...")
        try:
            created = (
                service.posts()
                .insert(blogId=blog_id, body=body, isDraft=is_draft)
                .execute()
            )
            logger.info(f"Successfully created post: {created.get('url')}")
            return created
        except google.auth.exceptions.RefreshError as e:
            logger.error(f"Authentication failed during creation: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            raise
