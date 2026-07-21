from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

import frontmatter

from scripts import new_page


class CreatePageTests(TestCase):
    def test_generates_each_page_type_with_requested_metadata(self) -> None:
        with TemporaryDirectory() as directory:
            wiki = Path(directory)
            for section in new_page.TYPE_TO_DIR.values():
                (wiki / section).mkdir(parents=True, exist_ok=True)

            with patch.object(new_page, "WIKI", wiki):
                for page_type in new_page.TYPE_TO_DIR:
                    with self.subTest(page_type=page_type):
                        page_id = f"example-{page_type}"
                        title = f'Example "{page_type}"'
                        path = new_page.create_page(page_type, page_id, title)
                        post = frontmatter.load(path)

                        self.assertEqual(post.metadata["id"], page_id)
                        self.assertEqual(post.metadata["title"], title)
                        self.assertIn(f"# {title}", post.content)

    def test_rejects_id_that_can_escape_destination(self) -> None:
        with self.assertRaisesRegex(ValueError, "lowercase kebab-case"):
            new_page.create_page("paper", "../../outside", "Unsafe")

    def test_refuses_to_overwrite_existing_page(self) -> None:
        with TemporaryDirectory() as directory:
            wiki = Path(directory)
            (wiki / "topics").mkdir(parents=True)

            with patch.object(new_page, "WIKI", wiki):
                new_page.create_page("topic", "existing-topic", "First")
                with self.assertRaises(FileExistsError):
                    new_page.create_page("topic", "existing-topic", "Second")
