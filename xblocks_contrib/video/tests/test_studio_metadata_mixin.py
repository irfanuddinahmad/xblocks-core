"""Tests for StudioMetadataMixin.editable_metadata_fields (VideoBlock)."""
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from django.test.utils import override_settings
from opaque_keys.edx.locator import CourseLocator
from xblock.field_data import DictFieldData
from xblock.fields import ScopeIds

from xblocks_contrib.video.exceptions import TranscriptNotFoundError
from xblocks_contrib.video.tests.test_utils import DummyRuntime
from xblocks_contrib.video.video import VideoBlock

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

    @staticmethod
    def _service_stub(service_name, service_obj):
        """Return a runtime.service stub that serves service_obj only for service_name."""
        return lambda _block, name: service_obj if name == service_name else None

    def _get_fields(self, include_license=False, public_url=None, transcripts=None, service=None):
        """
        Call editable_metadata_fields with standard mocks applied.

        Pass service=<callable> to simulate a real runtime service (e.g. for
        licensing or video_config tests); omit it to have all service calls
        return None (skipping license and English-transcript logic).
        """
        service_kwargs = {'side_effect': service} if service else {'return_value': None}
        with patch.object(self.block, '_get_editable_metadata_fields',
                          return_value=self._base_fields(include_license)):
            with patch.object(self.block, 'get_transcripts_info',
                              return_value={'sub': '', 'transcripts': transcripts or {}}):
                with patch.object(self.block, 'get_public_video_url', return_value=public_url):
                    with patch.object(self.block.runtime, 'service', **service_kwargs):
                        return self.block.editable_metadata_fields

    # ------------------------------------------------------------------
    # Field-level modifications
    # ------------------------------------------------------------------

    def test_default_field_modifications(self):
        """Verify all field-level changes made by editable_metadata_fields with default args."""
        fields = self._get_fields()
        assert 'sub' not in fields
        assert fields['transcripts']['custom'] is True
        assert fields['transcripts']['type'] == 'VideoTranslations'
        assert fields['transcripts']['languages'] == [
            {'label': 'English', 'code': 'en'},
            {'label': 'Esperanto', 'code': 'eo'},
            {'label': 'Urdu', 'code': 'ur'},
        ]
        # DummyRuntime.handler_url returns '/handler/block/handler'
        assert fields['transcripts']['urlRoot'] == '/handler/block/handler'
        assert fields['edx_video_id']['type'] == 'VideoID'
        assert fields['handout']['type'] == 'FileUploader'

    def test_field_modifications_with_custom_args(self):
        """Verify transcripts.value passthrough and public_access enrichment."""
        fields = self._get_fields(transcripts={'fr': 'french.srt'})
        assert fields['transcripts']['value'] == {'fr': 'french.srt'}

        fields = self._get_fields(public_url='https://example.com/video')
        assert fields['public_access']['type'] == 'PublicAccess'
        assert fields['public_access']['url'] == 'https://example.com/video'

    # ------------------------------------------------------------------
    # License field handling
    # ------------------------------------------------------------------

    def test_license_removed_when_licensing_disabled(self):
        """'license' is removed when the settings service reports licensing_enabled=False."""
        settings_service = Mock()
        settings_service.get_settings_bucket.return_value = {'licensing_enabled': False}
        fields = self._get_fields(
            include_license=True,
            service=self._service_stub('settings', settings_service),
        )
        assert 'license' not in fields

    def test_license_kept_when_licensing_enabled(self):
        """'license' is kept when the settings service reports licensing_enabled=True."""
        settings_service = Mock()
        settings_service.get_settings_bucket.return_value = {'licensing_enabled': True}
        fields = self._get_fields(
            include_license=True,
            service=self._service_stub('settings', settings_service),
        )
        assert 'license' in fields

    # ------------------------------------------------------------------
    # English transcript lookup via video_config service
    # ------------------------------------------------------------------

    def test_english_transcript_found_added_to_value(self):
        """When video_config returns an English transcript, it is added to transcripts.value."""
        video_config = Mock()
        video_config.get_transcript.return_value = ('content', 'en_subs_id', 'txt')
        self.block.sub = 'some_sub_id'  # non-empty so possible_sub_ids is non-empty
        fields = self._get_fields(
            transcripts={},
            service=self._service_stub('video_config', video_config),
        )
        assert fields['transcripts']['value'] == {'en': 'en_subs_id'}

    def test_english_transcript_merged_with_existing_transcripts(self):
        """English transcript from video_config is merged with, not replacing, existing transcripts."""
        video_config = Mock()
        video_config.get_transcript.return_value = ('content', 'en_subs_id', 'txt')
        self.block.sub = 'some_sub_id'
        fields = self._get_fields(
            transcripts={'fr': 'french.srt'},
            service=self._service_stub('video_config', video_config),
        )
        assert fields['transcripts']['value'] == {'fr': 'french.srt', 'en': 'en_subs_id'}

    def test_transcript_not_found_leaves_value_unchanged(self):
        """When video_config raises TranscriptNotFoundError, transcripts.value is not modified."""
        video_config = Mock()
        video_config.get_transcript.side_effect = TranscriptNotFoundError
        self.block.sub = 'some_sub_id'
        fields = self._get_fields(
            transcripts={'fr': 'french.srt'},
            service=self._service_stub('video_config', video_config),
        )
        assert 'en' not in fields['transcripts']['value']
        assert fields['transcripts']['value'] == {'fr': 'french.srt'}
