from fastapi import HTTPException, status


class RecordNotFoundError(Exception):
    """Should be raised when not finding a record is critical and will lead to follow-up errors."""


class RecordCreationError(Exception):
    """Should be raised when not being able to create a record is critical and will lead to follow-up errors."""


class ResourceInUseException(HTTPException):
    """Should be raised when trying to delete a resource that is still in use."""
    def __init__(self, usage_count: int):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "RESOURCE_IN_USE",
                "message": "Resource cannot be deleted because it is still in use.",
                "usage_count": usage_count,
            },
        )
