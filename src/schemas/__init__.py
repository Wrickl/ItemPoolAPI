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
from .items.content_piece import (
    ContentPieceCreate,
    ContentPieceRead,
    ContentPieceReadFull,
)

# Task Schemas - DataTypes
from .items.data_types import (
    DataTypeRead,
    DataTypeResponse,
)

# Task Schemas - Item
from .items.Item import (
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
from .items.item_type import (
    ItemTypeCreate,
    ItemTypeRead,
)

# Task Schemas - ItemCollection
from .items.item_collection import (
    ItemCollectionCreate,
    ItemCollectionRead,
)

# Task Schemas - License
from .items.license import (
    LicenseCreate,
    LicenseUpdate,
    LicenseResponse,
)

# Task Schemas - Status
from .items.status import (
    StatusCreate,
    StatusUpdate,
    StatusResponse,
)

# Task Schemas - Themenbereich
from .items.themenbereich import (
    ThemenbereichCreate,
    ThemenbereichUpdate,
    ThemenbereichResponse,
)

# Task Schemas - Organisation
from .items.organisation import (
    OrganisationCreate,
    OrganisationUpdate,
    OrganisationResponse,
)

# Task Schemas - Content Types
from .items.content_types import (
    ContentSectionRead,
    ItemTypeContentSectionAssign,
    ItemTypeDetailRead,
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
    # items - ContentPiece
    "ContentPieceCreate",
    "ContentPieceRead",
    "ContentPieceReadFull",
    # items - DataTypes
    "DataTypeRead",
    "DataTypeResponse",
    # items - Item
    "FlexibleContentBlock",
    "ExportContentPiece",
    "EnrichedContentBlock",
    "ItemCreate",
    "ItemResponse",
    "ItemWithAuthorResponse",
    "ItemExportResponse",
    "ItemTemplateContentSectionResponse",
    "ItemTemplateResponse",
    # items - ItemType
    "ItemTypeCreate",
    "ItemTypeRead",
    # items - ItemCollection
    "ItemCollectionCreate",
    "ItemCollectionRead",
    # items - License
    "LicenseCreate",
    "LicenseUpdate",
    "LicenseResponse",
    # items - Status
    "StatusCreate",
    "StatusUpdate",
    "StatusResponse",
    # items - Themenbereich
    "ThemenbereichCreate",
    "ThemenbereichUpdate",
    "ThemenbereichResponse",
    # items - Organisation
    "OrganisationCreate",
    "OrganisationUpdate",
    "OrganisationResponse",
    # items - Content Types
    "ContentSectionRead",
    "ItemTypeContentSectionAssign",
    "ItemTypeDetailRead",
    # Solutions
    "SourcePayload",
    "SubmissionPayload",
    "EventLogPayload",
    "SolutionAttemptCreate",
    "SolutionAttemptRead",
    "SolutionAttemptEventCreate",
    "SolutionAttemptEventRead",
]
