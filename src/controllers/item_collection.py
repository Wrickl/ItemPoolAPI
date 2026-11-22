from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from database.dao_connection import get_session
from models.items.item_collection import ItemCollection
from models.items.tasks import Item
from schemas.items.item_collection import ItemCollectionCreate, ItemCollectionRead

router = APIRouter()


@router.post(
    "/createItemCollection", response_model=ItemCollectionRead, tags=["ItemCollections"]
)
async def create_item_collection(collection_data: ItemCollectionCreate, session: Session = Depends(get_session)):
    existing_item_ids = set(
        session.exec(select(Item.item_id).where(Item.item_id.in_(collection_data.item_ids))).all())
    requested_item_ids = set(collection_data.item_ids)

    missing_item_ids = sorted(
        item_id for item_id in requested_item_ids if item_id not in existing_item_ids
    )
    if missing_item_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Folgende Item-IDs wurden nicht gefunden: {missing_item_ids}",
        )

    new_collection = ItemCollection(
        name=collection_data.name.strip(),
        item_ids=collection_data.item_ids,
    )
    session.add(new_collection)
    session.commit()
    session.refresh(new_collection)
    return new_collection


@router.get(
    "/getAllItemCollections",
    response_model=list[ItemCollectionRead],
    tags=["ItemCollections"],
)
async def get_all_item_collections(session: Session = Depends(get_session)):
    collections = session.exec(select(ItemCollection)).all()
    return [
        ItemCollectionRead(
            collection_id=collection.collection_id,
            name=collection.name,
            item_ids=[item.item_id for item in collection.items],
            created_at=collection.created_at,
        )
        for collection in collections
    ]


@router.get(
    "/getItemCollection/{collection_id}",
    response_model=ItemCollectionRead,
    tags=["ItemCollections"],
)
async def get_item_collection(
    collection_id: UUID, session: Session = Depends(get_session)
):
    collection = session.get(ItemCollection, collection_id)
    if collection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Collection mit ID {collection_id} wurde nicht gefunden",
        )
    return ItemCollectionRead(
        collection_id=collection.collection_id,
        name=collection.name,
        item_ids=[item.item_id for item in collection.items],
        created_at=collection.created_at,
    )


@router.put(
    "/updateItemCollection/{collection_id}",
    response_model=ItemCollectionRead,
    tags=["ItemCollections"],
)
async def update_item_collection(
    collection_id: UUID,
    collection_data: ItemCollectionCreate,
    session: Session = Depends(get_session),
):
    collection = session.get(ItemCollection, collection_id)
    if collection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Collection mit ID {collection_id} wurde nicht gefunden",
        )

    existing_item_ids = set(
        session.exec(
            select(Item.item_id).where(Item.item_id.in_(collection_data.item_ids))
        ).all()
    )
    requested_item_ids = set(collection_data.item_ids)
    missing_item_ids = sorted(
        item_id for item_id in requested_item_ids if item_id not in existing_item_ids
    )
    if missing_item_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Folgende Item-IDs wurden nicht gefunden: {missing_item_ids}",
        )

    collection.name = collection_data.name.strip()
    collection.items = session.exec(
        select(Item).where(Item.item_id.in_(collection_data.item_ids))
    ).all()
    session.add(collection)
    session.commit()
    session.refresh(collection)
    return ItemCollectionRead(
        collection_id=collection.collection_id,
        name=collection.name,
        item_ids=[item.item_id for item in collection.items],
        created_at=collection.created_at,
    )


@router.delete("/deleteItemCollection/{collection_id}", tags=["ItemCollections"])
async def delete_item_collection(
    collection_id: UUID, session: Session = Depends(get_session)
):
    collection = session.get(ItemCollection, collection_id)
    if collection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Collection mit ID {collection_id} wurde nicht gefunden",
        )

    session.delete(collection)
    session.commit()
    return {"detail": f"Collection mit ID {collection_id} wurde gelöscht"}
