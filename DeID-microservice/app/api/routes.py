from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.item import Item as ItemModel
from app.models.schemas import ItemCreate, Item as ItemSchema, ItemList

router = APIRouter()

@router.get("/")
async def read_root():
    return {"message": "Welcome to my FastAPI project!"}

@router.post("/items", response_model=ItemSchema, status_code=status.HTTP_201_CREATED)
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    db_item = ItemModel(**item.dict())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


@router.get("/items", response_model=ItemList)
def list_items(db: Session = Depends(get_db)):
    items = db.query(ItemModel).all()
    return {"items": items}


@router.get("/items/{item_id}", response_model=ItemSchema)
def read_item(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(ItemModel).filter(ItemModel.id == item_id).first()
    if not db_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return db_item

def setup_routes(app):
    app.include_router(router)