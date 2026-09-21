from archiv.models.TaskMaterials.TextTaskMaterial import TextMetadata, TextTaskMaterial

from services.MetaDataInference.TextMetaDataInferenceHandlers.TextMetricsHandler import (
    TextMetricsHandler,
)
from services.TaskRegistration.TaskMaterialRegistrationHandlers.BaseHandler import TaskMaterialHandler


class TextMaterialHandler(TaskMaterialHandler):
    def __init__(self, dao):
        super().__init__(dao)

    def process_material(self, material: TextTaskMaterial) -> TextMetadata:
        text_meta_data_inference_handler = TextMetricsHandler()

        meta_data = text_meta_data_inference_handler.infer_metadata(material.text)

        return meta_data
