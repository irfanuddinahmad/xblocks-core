"""
Tests for WordCloudBlock
"""

from django.test import TestCase
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblocks_contrib import WordCloudBlock


class TestWordCloudBlock(TestCase):
    """Tests for WordCloudBlock"""

    def setUp(self):
        super().setUp()
        scope_ids = ScopeIds("1", "2", "3", "4")
        self.block = WordCloudBlock(ToyRuntime(), scope_ids=scope_ids)

    def test_my_student_view(self):
        """Test the basic view loads."""
        frag = self.block.student_view()
        as_dict = frag.to_dict()
        content = as_dict["content"]
        self.assertIn(
            "Word cloud",
            content,
            "XBlock did not render correct student view",
        )
        self.assertIn(
            "Your words were:",
            content,
            "XBlock did not render correct student view",
        )

    def test_good_word(self):
        self.assertEqual(self.block.good_word("  Test  "), "test")
        self.assertEqual(self.block.good_word("Hello"), "hello")
        self.assertEqual(self.block.good_word("  WORLD "), "world")

    def test_top_dict(self):
        words = {"hello": 3, "world": 5, "python": 2}
        top_words = self.block.top_dict(words, 2)
        self.assertEqual(top_words, {"world": 5, "hello": 3})

    def test_get_state_not_submitted(self):
        self.block.submitted = False
        state = self.block.get_state()
        self.assertFalse(state["submitted"])
        self.assertEqual(state["top_words"], {})

    def test_get_state_submitted(self):
        self.block.submitted = True
        self.block.student_words = ["Mango", "Strawberry", "Banana"]
        self.block.all_words = {"Mango": 11, "Apple": 13, "Banana": 21, "Strawberry": 28}
        self.block.top_words = {"Strawberry": 28, "Banana": 21}
        state = self.block.get_state()
        self.assertTrue(state["submitted"])
        self.assertEqual(
            state["top_words"],
            [{"text": "Banana", "size": 21, "percent": 29}, {"text": "Strawberry", "size": 28, "percent": 71}],
        )
        self.assertEqual(state["total_count"], 73)

    def test_submit_state_first_time(self):
        self.block.submitted = False
        data = {"student_words": ["hello", "world", "hello"]}
        response = self.block.submit_state(data)
        self.assertEqual(response["status"], "success")
        self.assertTrue(self.block.submitted)
        self.assertEqual(self.block.student_words, ["hello", "world", "hello"])
        self.assertEqual(self.block.all_words["hello"], 2)
        self.assertEqual(self.block.all_words["world"], 1)

    def test_submit_state_already_submitted(self):
        self.block.submitted = True
        data = {"student_words": ["new"]}
        response = self.block.submit_state(data)
        self.assertEqual(response["status"], "fail")
        self.assertEqual(response["error"], "You have already posted your data.")

    def test_prepare_words(self):
        top_words = {"hello": 3, "world": 2}
        result = self.block.prepare_words(top_words, 5)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["text"], "hello")
        self.assertEqual(result[0]["size"], 3)
        self.assertEqual(result[0]["percent"], 60)
        self.assertEqual(result[1]["text"], "world")
        self.assertEqual(result[1]["size"], 2)
        self.assertEqual(result[1]["percent"], 40)

    def test_good_ajax_request(self):
        """
        Make sure that ajax request works correctly.

        Ported from openedx-platform ``xmodule/tests/test_word_cloud.py::test_good_ajax_request``
        (see openedx/openedx-platform#38745). The pre-seeded ``all_words``/``top_words`` state and
        all assertions are kept so that the merge of a student's words into existing counts is covered.
        """
        self.block.all_words = {"cat": 10, "dog": 5, "mom": 1, "dad": 2}
        self.block.top_words = {"cat": 10, "dog": 5, "dad": 2}
        self.block.submitted = False

        # The extracted Word Cloud XBlock uses @XBlock.json_handler for handling AJAX requests.
        # It expects a standard Python dictionary as POST data and returns a JSON object in response.
        post_data = {"student_words": ["cat", "cat", "dog", "sun"]}
        response = self.block.submit_state(post_data)
        assert response["status"] == "success"
        assert response["submitted"] is True
        assert response["total_count"] == 22
        self.assertDictEqual(response["student_words"], {"sun": 1, "dog": 6, "cat": 12})

        self.assertListEqual(
            response["top_words"],
            [
                {"text": "cat", "size": 12, "percent": 55.0},
                {"text": "dad", "size": 2, "percent": 9.0},
                {"text": "dog", "size": 6, "percent": 27.0},
                {"text": "mom", "size": 1, "percent": 5.0},
                {"text": "sun", "size": 1, "percent": 4.0},
            ],
        )

        assert 100.0 == sum(i["percent"] for i in response["top_words"])
