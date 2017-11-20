from commons.abstractions.api import AudiopyleRestApi
from commons.abstractions.api_model import ApiRequest, ApiResponse, HttpStatusCode
from commons.audio.audio_tag_providing import read_id3_tag
from commons.audio.file_meta_providing import read_mp3_file_meta
from commons.utils.file_system import AUDIO_FILES_DIR, concatenate_paths, extract_extension, file_exists


class AudioMetaApi(AudiopyleRestApi):
    def get(self, request: ApiRequest) -> ApiResponse:
        audio_file_absolute_path = concatenate_paths(AUDIO_FILES_DIR, request.query_params.get("file"))
        if file_exists(audio_file_absolute_path):
            audio_files_meta = read_mp3_file_meta(audio_file_absolute_path)
            return ApiResponse(HttpStatusCode.ok, audio_files_meta)
        else:
            return ApiResponse(HttpStatusCode.not_found,
                               "Given file: {} does not exist".format(audio_file_absolute_path))


class AudioTagApi(AudiopyleRestApi):
    def get(self, request: ApiRequest):
        audio_file_name = request.query_params.get("file")
        self.logger.info("Reading ID3 tags of {}...".format(audio_file_name))
        if extract_extension(audio_file_name) == "mp3":
            audio_file_absolute_path = concatenate_paths(AUDIO_FILES_DIR, audio_file_name)
            id3_tag = read_id3_tag(audio_file_absolute_path)
            return ApiResponse(HttpStatusCode.ok, id3_tag.serialize())
        else:
            return ApiResponse(HttpStatusCode.bad_request,
                               "Can not read tags from non-mp3 file: {}".format(audio_file_name))
