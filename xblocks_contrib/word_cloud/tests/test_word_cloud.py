"""
Tests for WordCloudBlock
"""
import json

from django.test import TestCase
from fs.memoryfs import MemoryFS
from lxml import etree
from webob import Request
from xblock.exceptions import NoSuchHandlerError
from xblock.fields import ScopeIds
from xblock.test.toy_runtime import ToyRuntime

from xblocks_contrib import WordCloudBlock


class _FakeUsageKey(str):
    """
    A minimal stand-in for a real opaque_keys UsageKey: it behaves like the
    plain string ToyRuntime's key-value store expects, while also exposing
    the ``block_type``/``block_id`` attributes that LegacyXmlMixin's XML
    export code reads off ``self.usage_key``.
    """

    def __new__(cls, block_type, block_id):
        obj = super().__new__(cls, f'{block_type}.{block_id}')
        obj.block_type = block_type
        obj.block_id = block_id
        return obj


class WordCloudTestRuntime(ToyRuntime):  # pylint: disable=abstract-method
    """
    ToyRuntime extended with the minimal filesystem/policy hooks that
    LegacyXmlMixin needs to run an OLX import/export cycle.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.export_fs = MemoryFS()

    def get_policy(self, usage_id):  # pylint: disable=unused-argument
        return {}


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
            [{'text': 'Banana', 'size': 21, 'percent': 29}, {'text': 'Strawberry', 'size': 28, 'percent': 71}]
        )
        self.assertEqual(state['total_count'], 73)

    def test_submit_state_first_time(self):
        self.block.submitted = False
        data = {"student_words": ["hello", "world", "hello"]}
        response = self.block.submit_state(data)
        self.assertEqual(response['status'], 'success')
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

    def test_indexibility(self):
        """Test indexibility of Word Cloud."""
        self.block.display_name = "Word Cloud Block"
        self.block.instructions = "Enter some random words that comes to your mind"
        self.assertEqual(
            self.block.index_dictionary(),
            {
                'content_type': 'Word Cloud',
                'content': {
                    'display_name': 'Word Cloud Block',
                    'instructions': 'Enter some random words that comes to your mind',
                },
            }
        )

    def test_xml_import_export_cycle(self):
        """Test the OLX import/export round trip."""
        runtime = WordCloudTestRuntime()

        original_xml = (
            '<word_cloud display_name="Favorite Fruits" display_student_percents="false" '
            'instructions="What are your favorite fruits?" num_inputs="3" num_top_words="100"/>\n'
        )
        olx_element = etree.fromstring(original_xml)
        usage_key = _FakeUsageKey('word_cloud', 'block_id')
        keys = ScopeIds(None, 'word_cloud', 'def_id', usage_key)
        block = WordCloudBlock.parse_xml(olx_element, runtime, keys)

        self.assertEqual(block.display_name, 'Favorite Fruits')
        self.assertFalse(block.display_student_percents)
        self.assertEqual(block.instructions, 'What are your favorite fruits?')
        self.assertEqual(block.num_inputs, 3)
        self.assertEqual(block.num_top_words, 100)

        node = etree.Element('unknown_root')
        # This will export the olx to a separate file.
        block.add_xml_to_node(node)

        with runtime.export_fs.open('word_cloud/block_id.xml') as f:
            exported_xml = f.read()

        self.assertEqual(exported_xml, original_xml)

    def test_bad_dispatch_request(self):
        """
        Make sure that dispatching to an unknown handler raises the expected error.
        """
        request = Request.blank('/')
        request.method = 'POST'
        request.body = json.dumps({}).encode('utf-8')
        with self.assertRaises(NoSuchHandlerError):
            self.block.handle('bad_dispatch', request)

    def test_handle_submit_state_request(self):
        """
        Make sure that the handle_submit_state AJAX handler works correctly end-to-end
        (i.e. through the runtime's handler dispatch, not just by calling submit_state directly).
        """
        request = Request.blank('/')
        request.method = 'POST'
        request.body = json.dumps({'student_words': ['cat', 'cat', 'dog', 'sun']}).encode('utf-8')

        response = json.loads(self.block.handle('handle_submit_state', request).body.decode('utf8'))

        self.assertEqual(response['status'], 'success')
        self.assertTrue(response['submitted'])
        self.assertEqual(response['total_count'], 4)
        self.assertEqual(response['student_words'], {'cat': 2, 'dog': 1, 'sun': 1})

    def test_submit_studio_edits(self):
        """
        Test the submit_studio_edits handler (Studio editor Save button), including
        boolean field handling for display_student_percents.
        """
        submitted_values = {
            'display_name': "New Word Cloud",
            'instructions': "This is a Test",
            'num_inputs': 5,
            'num_top_words': 10,
            'display_student_percents': False,
        }
        request = Request.blank('/')
        request.method = 'POST'
        request.body = json.dumps({'values': submitted_values}).encode('utf-8')

        response = json.loads(self.block.handle('submit_studio_edits', request).body.decode('utf8'))
        self.assertEqual(response, {'result': 'success'})

        self.assertEqual(self.block.display_name, submitted_values['display_name'])
        self.assertEqual(self.block.instructions, submitted_values['instructions'])
        self.assertEqual(self.block.num_inputs, submitted_values['num_inputs'])
        self.assertEqual(self.block.num_top_words, submitted_values['num_top_words'])
        self.assertIs(self.block.display_student_percents, submitted_values['display_student_percents'])
