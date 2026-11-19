"""Word cloud is ungraded xblock used by students to
generate and view word cloud.

On the client side we show:
If student does not yet answered - `num_inputs` numbers of text inputs.
If student have answered - words he entered and cloud.
"""

import uuid

from django.utils.translation import gettext_noop as _
from lxml import etree
from web_fragments.fragment import Fragment
from xblock.core import XBlock
from xblock.fields import Boolean, Dict, Integer, List, Scope, String
from xblock.utils.resources import ResourceLoader
from xblock.utils.studio_editable import StudioEditableXBlockMixin

from xblocks_core.legacy_utils.xml_utils import LegacyXmlMixin

resource_loader = ResourceLoader(__name__)


def pretty_bool(value):
    """Check value for possible `True` value.

    Using this function we can manage different type of Boolean value
    in xml files.
    """
    bool_dict = [True, "True", "true", "T", "t", "1"]
    return value in bool_dict


@XBlock.needs("i18n")
class WordCloudBlock(StudioEditableXBlockMixin, LegacyXmlMixin, XBlock):
    """
    Word Cloud XBlock.
    """

    # Indicates that this XBlock has been extracted from edx-platform.
    is_extracted = True
    # "data" class attribute is added to make the following test case pass in edx-platform repo.
    # cms/djangoapps/contentstore/tests/test_contentstore.py::ImportRequiredTestCases::test_empty_data_roundtrip
    data = String(default="", scope=Scope.content)

    editable_fields = ["display_name", "num_inputs", "instructions", "num_top_words", "display_student_percents"]

    display_name = String(
        display_name=_("Display Name"),
        help=_("The display name for this component."),
        scope=Scope.settings,
        default="Word cloud",
    )
    instructions = String(
        display_name=_("Instructions"),
        help=_(
            "Add instructions to help learners understand how to use the word cloud. Clear instructions are "
            "important, especially for learners who have accessibility requirements."
        ),
        scope=Scope.settings,
    )
    num_inputs = Integer(
        display_name=_("Inputs"),
        help=_("The number of text boxes available for learners to add words and sentences."),
        scope=Scope.settings,
        default=5,
        values={"min": 1},
    )
    num_top_words = Integer(
        display_name=_("Maximum Words"),
        help=_("The maximum number of words displayed in the generated word cloud."),
        scope=Scope.settings,
        default=250,
        values={"min": 1},
    )
    display_student_percents = Boolean(
        display_name=_("Show Percents"),
        help=_("Statistics are shown for entered words near that word."),
        scope=Scope.settings,
        default=True,
    )

    # Fields for descriptor.
    submitted = Boolean(
        help=_("Whether this learner has posted words to the cloud."), scope=Scope.user_state, default=False
    )
    student_words = List(help=_("Student answer."), scope=Scope.user_state, default=[])
    all_words = Dict(help=_("All possible words from all learners."), scope=Scope.user_state_summary)
    top_words = Dict(help=_("Top num_top_words words for word cloud."), scope=Scope.user_state_summary)

    @staticmethod
    def workbench_scenarios():
        """Create canned scenario for display in the workbench."""
        return [
            (
                "WordCloudBlock",
                """<_word_cloud_extracted/>
                """,
            ),
            (
                "Multiple WordCloudBlock",
                """<vertical_demo>
                <_word_cloud_extracted/>
                <_word_cloud_extracted/>
                <_word_cloud_extracted/>
                </vertical_demo>
                """,
            ),
        ]

    @XBlock.supports("multi_device")
    def student_view(self, context=None):  # pylint: disable=W0613
        """
        Create primary view of the WordCloudXBlock, shown to students when viewing courses.
        """
        frag = Fragment()
        frag.add_content(
            resource_loader.render_django_template(
                "templates/word_cloud.html",
                {
                    "display_name": self.display_name,
                    "instructions": self.instructions,
                    "element_class": self.scope_ids.block_type,
                    "element_id": uuid.uuid1(0),
                    "num_inputs": self.num_inputs,
                    "range_num_inputs": range(self.num_inputs),
                    "submitted": self.submitted,
                },
                i18n_service=self.runtime.service(self, "i18n"),
            )
        )
        frag.add_css(resource_loader.load_unicode("static/css/word_cloud.css"))
        frag.add_javascript(resource_loader.load_unicode("static/js/src/word_cloud.js"))
        frag.add_javascript(resource_loader.load_unicode("static/js/src/d3.min.js"))
        frag.add_javascript(resource_loader.load_unicode("static/js/src/d3.layout.cloud.js"))
        frag.add_javascript(resource_loader.load_unicode("static/js/src/html_utils.js"))
        frag.initialize_js("WordCloudBlock")
        return frag

    def good_word(self, word):
        """Convert raw word to suitable word."""
        return word.strip().lower()

    def top_dict(self, dict_obj, amount):
        """Return top words from all words, filtered by number of
        occurences

        :param dict_obj: all words
        :type dict_obj: dict
        :param amount: number of words to be in top dict
        :type amount: int
        :rtype: dict
        """
        return dict(sorted(dict_obj.items(), key=lambda x: x[1], reverse=True)[:amount])

    def get_state(self):
        """Return success json answer for client."""
        if self.submitted:
            total_count = sum(self.all_words.values())
            return {
                "status": "success",
                "submitted": True,
                "display_student_percents": pretty_bool(self.display_student_percents),
                "student_words": {word: self.all_words[word] for word in self.student_words},
                "total_count": total_count,
                "top_words": self.prepare_words(self.top_words, total_count),
            }
        else:
            return {
                "status": "success",
                "submitted": False,
                "display_student_percents": False,
                "student_words": {},
                "total_count": 0,
                "top_words": {},
            }

    @XBlock.json_handler
    def handle_get_state(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        AJAX handler to get the current state of the XBlock

        Args:
            data: dict having request get parameters

        Returns:
            json string
        """
        return self.get_state()

    @XBlock.json_handler
    def handle_submit_state(self, data, suffix=""):  # pylint: disable=unused-argument
        return self.submit_state(data)

    def submit_state(self, data, suffix=""):  # pylint: disable=unused-argument
        """
        AJAX handler to submit the current state of the XBlock

        Args:
            data: dict having request get parameters

        Returns:
            json string
        """

        if self.submitted:
            return {"status": "fail", "error": "You have already posted your data."}

        # Student words from client.
        # FIXME: we must use raw JSON, not a post data (multipart/form-data)
        raw_student_words = data.get("student_words")
        student_words = [word for word in map(self.good_word, raw_student_words) if word]

        self.student_words = student_words

        # FIXME: fix this, when xblock will support mutable types.
        # Now we use this hack.
        # speed issues
        temp_all_words = self.all_words

        self.submitted = True

        # Save in all_words.
        for word in self.student_words:
            temp_all_words[word] = temp_all_words.get(word, 0) + 1

        # Update top_words.
        self.top_words = self.top_dict(temp_all_words, self.num_top_words)

        # Save all_words in database.
        self.all_words = temp_all_words

        return self.get_state()

    def prepare_words(self, top_words, total_count):
        """Convert words dictionary for client API.

        :param top_words: Top words dictionary
        :type top_words: dict
        :param total_count: Total number of words
        :type total_count: int
        :rtype: list of dicts. Every dict is 3 keys: text - actual word,
            size - counter of word, percent - percent in top_words dataset.

        Calculates corrected percents for every top word:

        For every word except last, it calculates rounded percent.
        For the last is 100 - sum of all other percents.

        """
        list_to_return = []
        percents = 0
        sorted_top_words = sorted(top_words.items(), key=lambda x: x[0].lower())
        for num, word_tuple in enumerate(sorted_top_words):
            if num == len(top_words) - 1:
                percent = 100 - percents
            else:
                percent = round((100.0 * word_tuple[1]) / total_count)
                percents += percent
            list_to_return.append({"text": word_tuple[0], "size": word_tuple[1], "percent": percent})
        return list_to_return

    def index_dictionary(self):
        """
        Return dictionary prepared with block content and type for indexing.
        """
        # return key/value fields in a Python dict object
        # values may be numeric / string or dict
        # default implementation is an empty dict

        xblock_body = super().index_dictionary()

        index_body = {
            "display_name": self.display_name,
            "instructions": self.instructions,
        }

        if "content" in xblock_body:
            xblock_body["content"].update(index_body)
        else:
            xblock_body["content"] = index_body

        xblock_body["content_type"] = "Word Cloud"

        return xblock_body

    @classmethod
    def definition_from_xml(cls, xml_object, system):
        if len(xml_object) == 0 and len(list(xml_object.items())) == 0:
            return {"data": ""}, []
        return {"data": etree.tostring(xml_object, pretty_print=True, encoding="unicode")}, []

    def definition_to_xml(self, resource_fs):
        if self.data:
            return etree.fromstring(self.data)
        return etree.Element(self.usage_key.block_type)
