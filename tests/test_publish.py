import unittest
from unittest.mock import MagicMock, patch

from blogspot_publishing.publish import find_post_by_title, publish_post


class TestPublish(unittest.TestCase):
    def setUp(self):
        self.mock_service = MagicMock()
        self.mock_posts = self.mock_service.posts.return_value

    def test_find_post_by_title_found(self):
        # Setup mock
        self.mock_posts.list.return_value.execute.return_value = {
            "items": [{"id": "123", "title": "My Post"}]
        }

        # Test
        result = find_post_by_title(self.mock_service, "blog_id", "My Post")

        # Verify
        self.assertEqual(result["id"], "123")
        self.assertEqual(result["title"], "My Post")

    def test_find_post_by_title_not_found(self):
        # Setup mock to return different title
        self.mock_posts.list.return_value.execute.return_value = {
            "items": [{"id": "123", "title": "Other Post"}]
        }
        self.mock_posts.list_next.return_value = None  # No next page

        # Test
        result = find_post_by_title(self.mock_service, "blog_id", "My Post")

        # Verify
        self.assertIsNone(result)

    @patch("blogspot_publishing.publish.get_service")
    def test_publish_post_insert(self, mock_get_service: MagicMock) -> None:
        mock_get_service.return_value = self.mock_service

        # Mock search to return None (not found)
        # We need to mock the sequence of list calls.
        # list() -> execute() -> {"items": []}
        self.mock_posts.list.return_value.execute.return_value = {}
        self.mock_posts.list_next.return_value = None

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
    def test_publish_post_update(self, mock_get_service: MagicMock) -> None:
        mock_get_service.return_value = self.mock_service

        # Mock search to return found
        self.mock_posts.list.return_value.execute.return_value = {
            "items": [{"id": "123", "title": "Existing Post"}]
        }

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


if __name__ == "__main__":
    unittest.main()
