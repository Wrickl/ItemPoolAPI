from .BaseHandler import TaskMaterialHandler
from .GeneralHandlers.TextHandler import TextMaterialHandler
from .SQLMaterialHandlers.DatabaseHandler import DatabaseMaterialHandler
from .SQLMaterialHandlers.QueryHandler import QueryMaterialHandler
from .SQLMaterialHandlers.SchemaHandler import SchemaMaterialHandler
from archiv.models.TaskMaterials.BaseTaskMaterial import MaterialType

material_handlers: dict[str, TaskMaterialHandler] = {
    MaterialType.text: TextMaterialHandler,
    MaterialType.query: QueryMaterialHandler,
    MaterialType.schema: SchemaMaterialHandler,
    MaterialType.database: DatabaseMaterialHandler,
}
