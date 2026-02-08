import base64
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import google.auth.exceptions  # type: ignore
from PIL import Image

from blogger.publish import (  # type: ignore
    _encode_image,
    find_post_by_title,
    publish_post,
)


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_posts = self.mock_service.posts.return_value

    @patch("blogger.publish._iter_posts")
    def test_find_post_by_title_found(self, mock_iterate: MagicMock) -> None:
        # Setup mock to return posts
        mock_iterate.return_value = [
            {"id": "123", "title": "My Post", "status": "DRAFT"},
            {"id": "456", "title": "Other Post", "status": "DRAFT"},
        ]

        # Test
        result = find_post_by_title(self.mock_service, "blog_id", "My Post")

        # Verify
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["title"], "My Post")

    @patch("blogger.publish._iter_posts")
    def test_find_post_by_title_not_found(
        self, mock_iterate: MagicMock
    ) -> None:
        # Setup mock to return different title
        mock_iterate.return_value = [
            {"id": "123", "title": "Other Post", "status": "DRAFT"}
        ]

        # Test
        result = find_post_by_title(self.mock_service, "blog_id", "My Post")

        # Verify
        self.assertIsNone(result)

    @patch("blogger.publish.get_service")
    @patch("blogger.publish._iter_posts")
    def test_publish_post_insert(
        self, mock_iterate: MagicMock, mock_get_service: MagicMock
    ) -> None:
        mock_get_service.return_value = self.mock_service
        mock_iterate.return_value = []  # No existing post

        publish_post(
            "client_id",
            "client_secret",
            "refresh_token",
            "blog_id",
            "New Post",
            "Content",
        )

        # Verify insert called
        self.mock_posts.insert.assert_called_once()
        _, kwargs = self.mock_posts.insert.call_args
        self.assertEqual(kwargs["body"]["title"], "New Post")
        self.assertTrue(kwargs["isDraft"])  # Default is True

    @patch("blogger.publish.get_service")
    @patch("blogger.publish._iter_posts")
    def test_publish_post_update(
        self, mock_iterate: MagicMock, mock_get_service: MagicMock
    ) -> None:
        mock_get_service.return_value = self.mock_service

        # Mock search to return found
        mock_iterate.return_value = [
            {"id": "123", "title": "Existing Post", "status": "DRAFT"}
        ]

        publish_post(
            "client_id",
            "client_secret",
            "refresh_token",
            "blog_id",
            "Existing Post",
            "New Content",
        )

        # Verify update called
        self.mock_posts.update.assert_called_once()
        _, kwargs = self.mock_posts.update.call_args
        self.assertEqual(kwargs["postId"], "123")
        self.assertEqual(kwargs["body"]["content"], "New Content")

    @patch("blogger.publish.get_service")
    @patch("blogger.publish._iter_posts")
    def test_publish_post_skip_non_draft(
        self, mock_iterate: MagicMock, mock_get_service: MagicMock
    ) -> None:
        """Test that we skip updating if the post is not a draft."""
        mock_get_service.return_value = self.mock_service
        mock_iterate.return_value = [
            {"id": "123", "title": "Live Post", "status": "LIVE"}
        ]

        with self.assertLogs("blogger.publish", level="WARNING") as cm:
            result = publish_post(
                "client_id",
                "client_secret",
                "refresh_token",
                "blog_id",
                "Live Post",
                "New Content",
            )

        self.mock_posts.update.assert_not_called()
        self.mock_posts.insert.assert_not_called()
        self.assertEqual(result["status"], "LIVE")
        self.assertTrue(
            any("is LIVE. Skipping" in output for output in cm.output)
        )

    @patch("blogger.publish.get_service")
    def test_publish_post_auth_failure(
        self, mock_get_service: MagicMock
    ) -> None:
        """Test that auth errors are propagated."""
        mock_get_service.side_effect = google.auth.exceptions.RefreshError(
            "Invalid token"
        )

        with self.assertRaises(google.auth.exceptions.RefreshError):
            publish_post(
                "client_id",
                "client_secret",
                "refresh_token",
                "blog_id",
                "Test Post",
                "Content",
            )

    @patch("blogger.publish._iter_posts")
    def test_find_post_by_title_scheduled(
        self, mock_iterate: MagicMock
    ) -> None:
        """Test scheduled posts are found by title."""
        mock_iterate.return_value = [
            {"id": "123", "title": "My Post", "status": "SCHEDULED"},
        ]

        # Test
        result = find_post_by_title(self.mock_service, "blog_id", "My Post")

        # Verify - scheduled posts are now found and returned
        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["status"], "SCHEDULED")

    @patch("blogger.publish._iter_posts")
    def test_find_post_by_title_missing_status(
        self, mock_iterate: MagicMock
    ) -> None:
        """Test missing status does not raise during logging."""
        mock_iterate.return_value = [
            {"id": "123", "title": "My Post"},
        ]

        with self.assertLogs("blogger.publish", level="INFO") as cm:
            result = find_post_by_title(
                self.mock_service, "blog_id", "My Post"
            )

        self.assertIsNotNone(result)
        self.assertEqual(result["id"], "123")
        self.assertTrue(
            any("Status:UNKNOWN" in output for output in cm.output)
        )

    @patch("blogger.publish._iter_posts")
    def test_find_post_by_title_http_error(
        self, mock_iterate: MagicMock
    ) -> None:
        """Test that HTTP errors are propagated."""
        from googleapiclient.errors import HttpError

        mock_iterate.side_effect = HttpError(
            MagicMock(status=400), b"Bad Request"
        )

        with self.assertRaises(HttpError):
            find_post_by_title(self.mock_service, "blog_id", "Test")

    def test_encode_image_outputs_jpeg(self) -> None:
        """Ensure images are encoded as JPEG data URIs."""
        with TemporaryDirectory() as tmp_dir:
            img_path = Path(tmp_dir) / "input.png"
            image = Image.new("RGBA", (16, 16), (0, 128, 255, 255))
            image.save(img_path, format="PNG")

            uri = _encode_image(img_path)

            self.assertIsNotNone(uri)
            self.assertTrue(uri.startswith("data:image/jpeg;base64,"))
            payload = uri.split(",", 1)[1]
            raw = base64.b64decode(payload)
            self.assertTrue(raw.startswith(b"\xff\xd8\xff"))


if __name__ == "__main__":
    unittest.main()
