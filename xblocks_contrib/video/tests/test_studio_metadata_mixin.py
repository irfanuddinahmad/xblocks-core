# pylint: disable=protected-access
"""Tests for StudioMetadataMixin.editable_metadata_fields (VideoBlock)."""
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.test.utils import override_settings

from xblocks_contrib.video.exceptions import TranscriptNotFoundError
from xblocks_contrib.video.tests.test_utils import DummyRuntime
from xblocks_contrib.video.video import VideoBlock
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds
from opaque_keys.edx.locator import CourseLocator

ALL_LANGUAGES = (
    ["en", "English"],
    ["eo", "Esperanto"],
    ["ur", "Urdu"],
)


def instantiate_block(**field_data):
    """Instantiate a VideoBlock with a DummyRuntime."""
    system = DummyRuntime()
    course_key = CourseLocator('org', 'course', 'run')
    usage_key = course_key.make_usage_key('video', 'SampleProblem')
    return system.construct_xblock_from_class(
        VideoBlock,
        scope_ids=ScopeIds(None, None, usage_key, usage_key),
        field_data=DictFieldData(field_data),
    )


@override_settings(ALL_LANGUAGES=ALL_LANGUAGES)
class TestEditableMetadataFieldsProperty(SimpleTestCase):
    """
    Unit tests for VideoBlock.editable_metadata_fields property.

    The property enriches the raw editable fields returned by
    _get_editable_metadata_fields with video-specific customisations:
    transcript language lists, special types for certain fields, etc.
    """

    def setUp(self):
        super().setUp()
        self.block = instantiate_block()

    def _base_fields(self, include_license=True):
        """Return a minimal editable-fields dict that satisfies the property's expectations."""
        fields = {
            'sub': {'type': 'Generic', 'value': ''},
            'transcripts': {'type': 'Dict', 'value': {}},
            'edx_video_id': {'type': 'Generic', 'value': ''},
            'public_access': {'type': 'Select', 'value': False},
            'handout': {'type': 'Generic', 'value': ''},
        }
        if include_license:
            fields['license'] = {'type': 'License', 'value': ''}
        return fields

    def _get_fields(self, include_license=False, public_url=None, transcripts=None):
        """
        Call editable_metadata_fields with standard mocks applied.

        All runtime services return None (no settings service, no video_config),
        so license checks and English-transcript lookups are skipped.
        """
        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': '', 'transcripts': transcripts or {}}):
                with patch.object(self.block, 'get_public_video_url', return_value=public_url):
                    with patch.object(self.block.runtime, 'service', return_value=None):
                        return self.block.editable_metadata_fields

    # ------------------------------------------------------------------
    # Field-level modifications
    # ------------------------------------------------------------------

    def test_sub_field_is_removed(self):
        """'sub' is deprecated and must be absent from the returned fields."""
        fields = self._get_fields()
        assert 'sub' not in fields

    def test_transcripts_custom_flag_and_type(self):
        """'transcripts' field gets custom=True and type='VideoTranslations'."""
        fields = self._get_fields()
        assert fields['transcripts']['custom'] is True
        assert fields['transcripts']['type'] == 'VideoTranslations'

    def test_transcripts_languages_sorted_by_label(self):
        """Language list injected into 'transcripts' must be sorted by label."""
        fields = self._get_fields()
        assert fields['transcripts']['languages'] == [
            {'label': 'English', 'code': 'en'},
            {'label': 'Esperanto', 'code': 'eo'},
            {'label': 'Urdu', 'code': 'ur'},
        ]

    def test_transcripts_value_comes_from_get_transcripts_info(self):
        """'transcripts.value' must reflect the dict returned by get_transcripts_info."""
        fields = self._get_fields(transcripts={'fr': 'french.srt'})
        assert fields['transcripts']['value'] == {'fr': 'french.srt'}

    def test_transcripts_url_root_from_handler_url(self):
        """'transcripts.urlRoot' must be built from runtime.handler_url (trailing /? stripped)."""
        fields = self._get_fields()
        # DummyRuntime.handler_url returns '/handler/block/handler'
        assert fields['transcripts']['urlRoot'] == '/handler/block/handler'

    def test_edx_video_id_type_is_video_id(self):
        """'edx_video_id' type must be changed to 'VideoID'."""
        fields = self._get_fields()
        assert fields['edx_video_id']['type'] == 'VideoID'

    def test_public_access_type_and_url(self):
        """'public_access' type becomes 'PublicAccess' and url is set from get_public_video_url."""
        fields = self._get_fields(public_url='https://example.com/video')
        assert fields['public_access']['type'] == 'PublicAccess'
        assert fields['public_access']['url'] == 'https://example.com/video'

    def test_handout_type_is_file_uploader(self):
        """'handout' type must be changed to 'FileUploader'."""
        fields = self._get_fields()
        assert fields['handout']['type'] == 'FileUploader'

    # ------------------------------------------------------------------
    # License field handling
    # ------------------------------------------------------------------

    def test_license_removed_when_licensing_disabled(self):
        """'license' is removed when the settings service reports licensing_enabled=False."""
        settings_service = Mock()
        settings_service.get_settings_bucket.return_value = {'licensing_enabled': False}

        def _service(_block, name):
            return settings_service if name == 'settings' else None

        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license=True)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': '', 'transcripts': {}}):
                with patch.object(self.block, 'get_public_video_url', return_value=None):
                    with patch.object(self.block.runtime, 'service', side_effect=_service):
                        fields = self.block.editable_metadata_fields

        assert 'license' not in fields

    def test_license_kept_when_licensing_enabled(self):
        """'license' is kept when the settings service reports licensing_enabled=True."""
        settings_service = Mock()
        settings_service.get_settings_bucket.return_value = {'licensing_enabled': True}

        def _service(_block, name):
            return settings_service if name == 'settings' else None

        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license=True)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': '', 'transcripts': {}}):
                with patch.object(self.block, 'get_public_video_url', return_value=None):
                    with patch.object(self.block.runtime, 'service', side_effect=_service):
                        fields = self.block.editable_metadata_fields

        assert 'license' in fields

    # ------------------------------------------------------------------
    # English transcript lookup via video_config service
    # ------------------------------------------------------------------

    def test_english_transcript_found_added_to_value(self):
        """When video_config returns an English transcript, it is added to transcripts.value."""
        video_config = Mock()
        video_config.get_transcript.return_value = ('content', 'en_subs_id', 'txt')

        def _service(_block, name):
            return video_config if name == 'video_config' else None

        self.block.sub = 'some_sub_id'  # non-empty so possible_sub_ids is non-empty

        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license=False)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': 'some_sub_id', 'transcripts': {}}):
                with patch.object(self.block, 'get_public_video_url', return_value=None):
                    with patch.object(self.block.runtime, 'service', side_effect=_service):
                        fields = self.block.editable_metadata_fields

        assert fields['transcripts']['value'] == {'en': 'en_subs_id'}

    def test_transcript_not_found_leaves_value_unchanged(self):
        """When video_config raises TranscriptNotFoundError, transcripts.value is not modified."""
        video_config = Mock()
        video_config.get_transcript.side_effect = TranscriptNotFoundError

        def _service(_block, name):
            return video_config if name == 'video_config' else None

        self.block.sub = 'some_sub_id'

        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license=False)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': 'some_sub_id', 'transcripts': {'fr': 'french.srt'}}):
                with patch.object(self.block, 'get_public_video_url', return_value=None):
                    with patch.object(self.block.runtime, 'service', side_effect=_service):
                        fields = self.block.editable_metadata_fields

        assert 'en' not in fields['transcripts']['value']
        assert fields['transcripts']['value'] == {'fr': 'french.srt'}
