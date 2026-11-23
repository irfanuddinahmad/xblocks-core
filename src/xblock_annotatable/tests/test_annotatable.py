"""Tests for the AnnotatableBlock."""

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from lxml import etree
from web_fragments.fragment import Fragment
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from xblock.test.tools import TestRuntime

from xblock_annotatable.block import AnnotatableBlock


class AnnotatableBlockTestCase(unittest.TestCase):
    """Tests for AnnotatableBlock."""

    # pylint: disable=protected-access

    sample_xml = """
    <annotatable display_name="Iliad">
        <instructions>Read the text.</instructions>
        <p>
            <annotation body="first">Sing</annotation>,
            <annotation title="goddess" body="second">O goddess</annotation>,
            <annotation title="anger" body="third" highlight="blue">the anger of Achilles
            son of Peleus</annotation>, that brought <i>countless</i> ills upon the
            Achaeans. Many a brave soul did it send hurrying down to Hades, and many a hero
            did it yield a prey to dogs and
            <div style="font-weight:bold">
                <annotation body="fourth" problem="4">vultures</annotation>, for so were
                the counsels of Jove fulfilled from the day on which the son of Atreus, king
                of men, and great Achilles, first fell out with one another.
            </div>
        </p>
        <annotation title="footnote" body="the end">The Iliad of Homer by Samuel Butler
        </annotation>
    </annotatable>
    """

    def setUp(self):
        super().setUp()
        runtime = TestRuntime()
        scope_ids = ScopeIds("user_id", "block_type", "block_id", "context_key")
        field_data = DictFieldData({"data": self.sample_xml})
        self.annotatable = AnnotatableBlock(runtime, field_data, scope_ids)

    def test_annotation_data_attr(self):
        el = etree.fromstring('<annotation title="bar" body="foo" problem="0">test</annotation>')

        expected_attr = {
            "data-comment-body": {"value": "foo", "_delete": "body"},
            "data-comment-title": {"value": "bar", "_delete": "title"},
            "data-problem-id": {"value": "0", "_delete": "problem"},
        }

        actual_attr = self.annotatable._get_annotation_data_attr(0, el)

        assert isinstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_default(self):
        xml = '<annotation title="x" body="y" problem="0">test</annotation>'
        el = etree.fromstring(xml)

        expected_attr = {"class": {"value": "annotatable-span highlight"}}
        actual_attr = self.annotatable._get_annotation_class_attr(0, el)

        assert isinstance(actual_attr, dict)
        self.assertDictEqual(expected_attr, actual_attr)

    def test_instruction_removal(self):
        xmltree = etree.fromstring(self.sample_xml)
        instructions = self.annotatable._extract_instructions(xmltree)

        assert instructions is not None
        assert "Read the text." in instructions
        assert xmltree.find("instructions") is None

    def test_annotation_class_attr_with_valid_highlight(self):
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for color in self.annotatable.HIGHLIGHT_COLORS:
            el = etree.fromstring(xml.format(highlight=color))
            value = f"annotatable-span highlight highlight-{color}"

            expected_attr = {"class": {"value": value, "_delete": "highlight"}}
            actual_attr = self.annotatable._get_annotation_class_attr(0, el)

            assert isinstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)

    def test_annotation_class_attr_with_invalid_highlight(self):
        xml = '<annotation title="x" body="y" problem="0" highlight="{highlight}">test</annotation>'

        for invalid_color in ["rainbow", "blink", "invisible", "", None]:
            el = etree.fromstring(xml.format(highlight=invalid_color))
            expected_attr = {"class": {"value": "annotatable-span highlight", "_delete": "highlight"}}
            actual_attr = self.annotatable._get_annotation_class_attr(0, el)

            assert isinstance(actual_attr, dict)
            self.assertDictEqual(expected_attr, actual_attr)

    def test_render_annotation(self):
        expected_html = (
            '<span class="annotatable-span highlight highlight-yellow" '
            'data-comment-title="x" data-comment-body="y" data-problem-id="0">'
            "z</span>"
        )
        expected_el = etree.fromstring(expected_html)

        actual_el = etree.fromstring('<annotation title="x" body="y" problem="0" highlight="yellow">z</annotation>')
        self.annotatable._render_annotation(0, actual_el)

        assert expected_el.tag == actual_el.tag
        assert expected_el.text == actual_el.text
        self.assertDictEqual(dict(expected_el.attrib), dict(actual_el.attrib))

    def test_render_content(self):
        content = self.annotatable._render_content()
        el = etree.fromstring(content)

        assert "div" == el.tag, "root tag is a div"

        expected_num_annotations = 5
        actual_num_annotations = el.xpath('count(//span[contains(@class,"annotatable-span")])')
        assert expected_num_annotations == actual_num_annotations, "check number of annotations"

    def test_get_html(self):
        context = self.annotatable.get_html()
        for key in ["display_name", "element_id", "content_html", "instructions_html"]:
            assert key in context

    def test_extract_instructions(self):
        xmltree = etree.fromstring(self.sample_xml)

        expected_xml = "<div>Read the text.</div>"
        actual_xml = self.annotatable._extract_instructions(xmltree)
        assert actual_xml is not None
        assert expected_xml.strip() == actual_xml.strip()

        xmltree = etree.fromstring("<annotatable>foo</annotatable>")
        actual = self.annotatable._extract_instructions(xmltree)
        assert actual is None

    def test_submit_studio_edits(self):
        mock_request = MagicMock()
        mock_request.method = "POST"
        mock_request.params = {
            "display_name": "New Display Name",
            "data": self.sample_xml,
        }
        mock_request.body = json.dumps(mock_request.params).encode("utf-8")

        response = self.annotatable.submit_studio_edits(mock_request)

        response_body = json.loads(response.body.decode("utf-8"))  # pylint: disable=no-member

        self.assertEqual(response_body["result"], "success")
        self.assertEqual(self.annotatable.display_name, "New Display Name")
        self.assertEqual(self.annotatable.data, self.sample_xml)

    def _block_with_data(self, data):
        runtime = TestRuntime()
        scope_ids = ScopeIds("user_id", "block_type", "block_id", "context_key")
        return AnnotatableBlock(runtime, DictFieldData({"data": data}), scope_ids)

    def test_get_html_with_empty_data(self):
        """
        A block with empty ``data`` (stored by earlier releases, which parsed a bare
        ``<annotatable/>`` to ``""``) renders as empty content instead of raising XMLSyntaxError.
        """
        for data in ("", "   \n"):
            block = self._block_with_data(data)
            context = block.get_html()
            assert context["instructions_html"] is None
            assert context["content_html"] == "<div/>"

    def test_bare_element_from_xml_renders(self):
        """
        A bare ``<annotatable/>`` (the content-library "create new component" flow, or an
        empty element in imported OLX) must render as empty content.
        """
        definition, _children = AnnotatableBlock.definition_from_xml(etree.fromstring("<annotatable/>"), None)
        block = self._block_with_data(definition["data"])
        assert block.get_html()["content_html"] == "<div/>"

    def test_bare_element_round_trips_on_export(self):
        """
        A bare ``<annotatable/>`` is kept as its OLX, like the built-in block (``RawMixin``),
        so export writes it back instead of dropping the block (``definition_to_xml`` returns
        None for empty ``data``).
        """
        definition, _children = AnnotatableBlock.definition_from_xml(etree.fromstring("<annotatable/>"), None)
        assert definition["data"].strip() == "<annotatable/>"
        block = self._block_with_data(definition["data"])
        exported = block.definition_to_xml(None)
        assert exported is not None
        assert exported.tag == "annotatable"
        assert len(exported) == 0


class AnnotatableBlockI18nJsCatalogTest(unittest.TestCase):
    """Tests for loading the block's namespaced JavaScript translation catalog."""

    def test_namespace(self):
        assert AnnotatableBlock.i18n_js_namespace == "XBlockAnnotatableI18N"
        assert AnnotatableBlock.get_i18n_js_namespace() == "XBlockAnnotatableI18N"

    def test_no_catalog_without_url(self):
        """No script is added when there is no catalog or the i18n service can't provide one."""
        no_catalog = Mock()
        no_catalog.get_javascript_i18n_catalog_url.return_value = None
        for i18n_service in (no_catalog, Mock(spec=[])):
            with self.subTest(i18n_service=i18n_service):
                block = Mock()
                block.runtime.service.return_value = i18n_service
                fragment = Fragment()

                AnnotatableBlock._add_i18n_js_catalog(block, fragment)  # pylint: disable=protected-access

                assert not fragment.resources

    def test_student_view_loads_catalog_before_block_js(self):
        runtime = TestRuntime()
        block = AnnotatableBlock(
            runtime,
            DictFieldData({"data": AnnotatableBlockTestCase.sample_xml}),
            ScopeIds("user_id", "block_type", "block_id", "context_key"),
        )
        with patch("xblock.runtime.NullI18nService.get_javascript_i18n_catalog_url", return_value="/static/catalog.js"):
            fragment = block.student_view()

        js = [r for r in fragment.resources if r.mimetype == "application/javascript"]
        assert js[0].kind == "url"
        assert js[0].data == "/static/catalog.js"
        assert "function Annotatable(" in js[1].data
