from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/ingredients", tags=["ingredients"])


@router.get("/", response_model=list[schemas.IngredientOut])
def list_ingredients(active_only: bool = False, db: Session = Depends(get_db)):
    q = db.query(models.Ingredient)
    if active_only:
        q = q.filter(models.Ingredient.active == True)
    return q.order_by(models.Ingredient.name).all()


@router.post("/", response_model=schemas.IngredientOut, status_code=201)
def create_ingredient(data: schemas.IngredientIn, db: Session = Depends(get_db)):
    ingredient = models.Ingredient(**data.model_dump())
    db.add(ingredient)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.put("/{ingredient_id}", response_model=schemas.IngredientOut)
def update_ingredient(ingredient_id: int, data: schemas.IngredientIn, db: Session = Depends(get_db)):
    ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    for k, v in data.model_dump().items():
        setattr(ingredient, k, v)
    db.commit()
    db.refresh(ingredient)
    return ingredient


@router.delete("/{ingredient_id}", status_code=204)
def delete_ingredient(ingredient_id: int, db: Session = Depends(get_db)):
    ingredient = db.query(models.Ingredient).filter(models.Ingredient.id == ingredient_id).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Ingredient not found")
    db.delete(ingredient)
    db.commit()
