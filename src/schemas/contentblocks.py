from abc import ABC
from enum import StrEnum
from typing import Annotated, Literal, Any

from pydantic import TypeAdapter
from sqlmodel import SQLModel, Field


class ContentBlockType(StrEnum):
    TEXT = "text"
    IMAGE = "image"
    JSON = "json"


class ContentBlockBase(SQLModel, ABC):
    type: str
    label: str


class TextBlock(ContentBlockBase):
    """Content Block für einfachen Text"""
    type: Literal[ContentBlockType.TEXT] = ContentBlockType.TEXT
    text: str


class ImageBlock(ContentBlockBase):
    """Content Block für ein Bild"""
    type: Literal[ContentBlockType.IMAGE] = ContentBlockType.IMAGE
    url: str
    alt_text: str | None = None


class JsonBlock(ContentBlockBase):
    type: Literal[ContentBlockType.JSON] = ContentBlockType.JSON
    data: dict[str, Any]


ContentBlock = Annotated[
    TextBlock | ImageBlock | JsonBlock,
    Field(discriminator="type"),
]
ContentBlockAdapter = TypeAdapter(ContentBlock)
