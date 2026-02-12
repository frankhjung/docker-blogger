import base64
import io
import logging
import mimetypes
from collections.abc import Iterator
from pathlib import Path
from typing import Any, Protocol, cast

import google.auth.exceptions  # type: ignore
from bs4 import BeautifulSoup, Tag
from google.oauth2.credentials import Credentials  # type: ignore
from googleapiclient.discovery import Resource, build  # type: ignore
from googleapiclient.errors import HttpError  # type: ignore
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)


def _norm(v: str | None) -> str:
    """Normalize string (strip and casefold)."""
    return str(v or "").strip().casefold()


class BloggerPostsResource(Protocol):
    """Protocol for Blogger API posts resource."""

    def list(self, blogId: str, status: list[str]) -> Any: ...
    def list_next(
        self, previous_request: Any, previous_response: Any
    ) -> Any: ...
    def update(
        self, blogId: str, postId: str, body: dict[str, Any]
    ) -> Any: ...
    def insert(
        self, blogId: str, body: dict[str, Any], isDraft: bool
    ) -> Any: ...


class BloggerService(Protocol):
    """Protocol for Blogger API service."""

    def posts(self) -> BloggerPostsResource: ...


def _encode_image(img_path: Path) -> str | None:
    """Encode image to JPEG data URI, resizing if needed."""
    try:
        mime = mimetypes.guess_type(str(img_path))[0]
        if not mime or not mime.startswith("image/"):
            logger.warning(
                "Skipping non-image or unknown type: %s (%s)",
                img_path.name,
                mime,
            )
            return None
        data = _resize_image_if_needed(img_path)
        if len(data) > 200 * 1024:
            logger.warning(
                "Image %s is large (%d bytes). This may cause API errors.",
                img_path.name,
                len(data),
            )

        b64 = base64.b64encode(data).decode()
        return f"data:image/jpeg;base64,{b64}"
    except (OSError, PermissionError, UnidentifiedImageError) as e:
        logger.warning(f"Failed to encode {img_path}: {e}")
        return None


def _resize_image_if_needed(img_path: Path) -> bytes:
    """Resize image to max width 1600px and encode as JPEG bytes."""
    MAX_WIDTH = 1600  # recommended for Blogger
    with Image.open(img_path) as image:
        width, height = image.size
        if width > MAX_WIDTH:
            new_height = max(1, round(height * (MAX_WIDTH / width)))
            resized = image.resize(
                (MAX_WIDTH, new_height), Image.Resampling.LANCZOS
            )
            logger.info(
                "Resized image %s from %dx%d to %dx%d",
                img_path.name,
                width,
                height,
                MAX_WIDTH,
                new_height,
            )
        else:
            resized = image.copy()

        if resized.mode not in {"RGB", "L"}:
            resized = resized.convert("RGB")

        buffer = io.BytesIO()
        resized.save(buffer, format="JPEG", quality=85, optimize=True)
        return buffer.getvalue()


def _process_img(img: Tag, base: Path) -> None:
    """Update img src to data URI if local."""
    src = str(img.get("src", ""))
    if not src or src.startswith(("http", "data:")):
        return
    path = base / src if not Path(src).is_absolute() else Path(src)
    if path.exists() and (uri := _encode_image(path)):
        img["src"] = uri


def _embed_images(html: str, base: Path | None) -> str:
    """Embed local images as data URIs."""
    soup = BeautifulSoup(html, "html.parser")
    for header in soup.find_all("header"):
        header.decompose()
    for img in soup.find_all("img"):
        _process_img(img, base or Path.cwd())

    # If input is a full HTML document, extract body and styles.
    if soup.body:
        content: list[str] = []
        if soup.head:
            content.extend(str(s) for s in soup.head.find_all("style"))
        content.append(soup.body.decode_contents())
        return "".join(content)

    return str(soup)


def get_service(client_id: str, secret: str, token: str) -> Resource:
    """Get authenticated Blogger service."""
    creds = Credentials(
        None,
        refresh_token=token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=secret,
        scopes=["https://www.googleapis.com/auth/blogger"],
    )
    return cast(
        Resource,
        build(
            "blogger",
            "v3",
            credentials=creds,
            static_discovery=False,
            cache_discovery=False,
        ),
    )


def _iter_posts(
    service: BloggerService, blog_id: str
) -> Iterator[dict[str, Any]]:
    """Yield all posts from blog."""
    for status in ["DRAFT", "SCHEDULED", "LIVE"]:
        req = service.posts().list(blogId=blog_id, status=[status])

        while req:
            res = req.execute()
            yield from res.get("items", [])
            req = service.posts().list_next(req, res)


def find_post_by_title(
    service: Any, blog_id: str, title: str
) -> dict[str, Any] | None:
    """Find post by case-insensitive title."""
    try:
        target = _norm(title)
        post = next(
            (
                p
                for p in _iter_posts(service, blog_id)
                if _norm(p.get("title")) == target
            ),
            None,
        )
        if post:
            logger.info(
                "Found: %s (ID:%s, Status:%s)",
                title,
                post["id"],
                post.get("status") or "UNKNOWN",
            )
        return post
    except (google.auth.exceptions.RefreshError, HttpError) as e:
        logger.error(f"Search failed: {e}")
        raise


def _exec(req: Any, op: str) -> dict[str, Any]:
    """Execute API call with error handling."""
    try:
        return req.execute()
    except (google.auth.exceptions.RefreshError, HttpError) as e:
        logger.error(f"Failed to {op}: {e}")
        raise


def publish_post(
    client_id: str,
    client_secret: str,
    refresh_token: str,
    blog_id: str,
    title: str,
    content: str,
    labels: list[str] | None = None,
    is_draft: bool = True,
    source_file_path: str | None = None,
) -> dict[str, Any]:
    """Publish or update a post to Blogspot."""
    base = Path(source_file_path).parent if source_file_path else None
    content = _embed_images(content, base)
    logger.debug("Processed content size: %d bytes", len(content))

    svc: Resource = get_service(client_id, client_secret, refresh_token)
    existing = find_post_by_title(svc, blog_id, title)

    body: dict[str, Any] = {"title": title, "content": content}
    if labels:
        body["labels"] = labels

    if not existing:
        logger.info("Creating new draft...")
        return _exec(
            svc.posts().insert(blogId=blog_id, body=body, isDraft=is_draft),  # type: ignore
            "create",
        )

    if _norm(existing.get("status")) != "draft":
        logger.warning(
            "Post '%s' is %s. Skipping.", title, existing.get("status")
        )
        return existing

    logger.info("Updating existing draft: %s", existing["id"])
    return _exec(
        svc.posts().update(blogId=blog_id, postId=existing["id"], body=body),  # type: ignore
        "update",
    )
