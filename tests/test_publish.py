import unittest
from unittest.mock import MagicMock, patch

import google.auth.exceptions  # type: ignore

from blogspot_publishing.publish import (  # type: ignore
    find_post_by_title,
    publish_post,
)


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_posts = self.mock_service.posts.return_value

    @patch("blogspot_publishing.publish._iter_posts")
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

    @patch("blogspot_publishing.publish._iter_posts")
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

    @patch("blogspot_publishing.publish.get_service")
    @patch("blogspot_publishing.publish._iter_posts")
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

    @patch("blogspot_publishing.publish.get_service")
    @patch("blogspot_publishing.publish._iter_posts")
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

    @patch("blogspot_publishing.publish.get_service")
    @patch("blogspot_publishing.publish._iter_posts")
    def test_publish_post_skip_non_draft(
        self, mock_iterate: MagicMock, mock_get_service: MagicMock
    ) -> None:
        """Test that we skip updating if the post is not a draft."""
        mock_get_service.return_value = self.mock_service
        mock_iterate.return_value = [
            {"id": "123", "title": "Live Post", "status": "LIVE"}
        ]

        with self.assertLogs(
            "blogspot_publishing.publish", level="WARNING"
        ) as cm:
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

    @patch("blogspot_publishing.publish.get_service")
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

    @patch("blogspot_publishing.publish._iter_posts")
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

    @patch("blogspot_publishing.publish._iter_posts")
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


if __name__ == "__main__":
    unittest.main()
