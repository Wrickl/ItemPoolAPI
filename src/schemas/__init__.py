"""
Pydantic Schemas für die ItemPool API.

Diese Datei exportiert alle verfügbaren Schemas für die verschiedenen API-Endpunkte.
Die Schemas sind nach Modulen organisiert und können direkt von hier importiert werden.
"""

# ComplexType Schemas
from .complextype import (
    ComplexTypeCreate,
    ComplexTypeUpdate,
    ComplexTypeResponse,
)

# Content Blocks
from .contentblocks import (
    ContentBlockType,
    ContentBlockBase,
    TextBlock,
    ImageBlock,
    JsonBlock,
    ContentBlock,
    ContentBlockAdapter,
)

# Author Schemas
from .Author.Author import (
    CreatorCreate,
    CreatorRead,
    CreatorUpdate,
    CreatorResponse,
)
from .Author.Organisation import (
    OrganisationCreate as AuthorOrganisationCreate,
    OrganisationRead as AuthorOrganisationRead,
)

# Task Schemas - ContentPiece
from .Tasks.ContentPiece import (
    ContentPieceCreate,
    ContentPieceRead,
    ContentPieceReadFull,
)

# Task Schemas - DataTypes
from .Tasks.DataTypes import (
    DataTypeRead,
    DataTypeResponse,
)

# Task Schemas - Item
from .Tasks.Item import (
    FlexibleContentBlock,
    ExportContentPiece,
    EnrichedContentBlock,
    ItemCreate,
    ItemResponse,
    ItemWithAuthorResponse,
    ItemExportResponse,
    ItemTemplateContentSectionResponse,
    ItemTemplateResponse,
)

# Task Schemas - ItemType
from .Tasks.ItemType import (
    ItemTypeCreate,
    ItemTypeRead,
)

# Task Schemas - ItemCollection
from .Tasks.ItemCollection import (
    ItemCollectionCreate,
    ItemCollectionRead,
)

# Task Schemas - License
from .Tasks.License import (
    LicenseCreate,
    LicenseUpdate,
    LicenseResponse,
)

# Task Schemas - Status
from .Tasks.Status import (
    StatusCreate,
    StatusUpdate,
    StatusResponse,
)

# Task Schemas - Themenbereich
from .Tasks.Themenbereich import (
    ThemenbereichCreate,
    ThemenbereichUpdate,
    ThemenbereichResponse,
)

# Task Schemas - Organisation
from .Tasks.Organisation import (
    OrganisationCreate,
    OrganisationUpdate,
    OrganisationResponse,
)

# Task Schemas - Content Types
from .Tasks.content_types import (
    ContentSectionRead,
    ItemTypeContentSectionAssign,
    ItemTypeDetailRead,
)

# Task Schemas - Question Type
from .Tasks.question_type import (
    QuestionTypeBase,
    QuestionTypeCreate,
    QuestionTypeUpdate,
    QuestionTypeInDBBase,
    QuestionTypeRead,
    QuestionTypePublic,
)

# Solution Schemas
from .Solutions.SolutionAttempt import (
    SourcePayload,
    SubmissionPayload,
    EventLogPayload,
    SolutionAttemptCreate,
    SolutionAttemptRead,
    SolutionAttemptEventCreate,
    SolutionAttemptEventRead,
)

__all__ = [
    # ComplexType
    "ComplexTypeCreate",
    "ComplexTypeUpdate",
    "ComplexTypeResponse",
    # Content Blocks
    "ContentBlockType",
    "ContentBlockBase",
    "TextBlock",
    "ImageBlock",
    "JsonBlock",
    "ContentBlock",
    "ContentBlockAdapter",
    # Author
    "CreatorCreate",
    "CreatorRead",
    "CreatorUpdate",
    "CreatorResponse",
    "AuthorOrganisationCreate",
    "AuthorOrganisationRead",
    # Tasks - ContentPiece
    "ContentPieceCreate",
    "ContentPieceRead",
    "ContentPieceReadFull",
    # Tasks - DataTypes
    "DataTypeRead",
    "DataTypeResponse",
    # Tasks - Item
    "FlexibleContentBlock",
    "ExportContentPiece",
    "EnrichedContentBlock",
    "ItemCreate",
    "ItemResponse",
    "ItemWithAuthorResponse",
    "ItemExportResponse",
    "ItemTemplateContentSectionResponse",
    "ItemTemplateResponse",
    # Tasks - ItemType
    "ItemTypeCreate",
    "ItemTypeRead",
    # Tasks - ItemCollection
    "ItemCollectionCreate",
    "ItemCollectionRead",
    # Tasks - License
    "LicenseCreate",
    "LicenseUpdate",
    "LicenseResponse",
    # Tasks - Status
    "StatusCreate",
    "StatusUpdate",
    "StatusResponse",
    # Tasks - Themenbereich
    "ThemenbereichCreate",
    "ThemenbereichUpdate",
    "ThemenbereichResponse",
    # Tasks - Organisation
    "OrganisationCreate",
    "OrganisationUpdate",
    "OrganisationResponse",
    # Tasks - Content Types
    "ContentSectionRead",
    "ItemTypeContentSectionAssign",
    "ItemTypeDetailRead",
    # Tasks - Question Type
    "QuestionTypeBase",
    "QuestionTypeCreate",
    "QuestionTypeUpdate",
    "QuestionTypeInDBBase",
    "QuestionTypeRead",
    "QuestionTypePublic",
    # Solutions
    "SourcePayload",
    "SubmissionPayload",
    "EventLogPayload",
    "SolutionAttemptCreate",
    "SolutionAttemptRead",
    "SolutionAttemptEventCreate",
    "SolutionAttemptEventRead",
]
