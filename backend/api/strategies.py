from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from database import get_db
from models import Strategy as DBStrategy
from core.strategy_engine import StrategyRegistry, register_all_strategies
from pydantic import BaseModel

router = APIRouter()

register_all_strategies()

class StrategyCreate(BaseModel):
    name: str
    type: str
    params: Dict[str, Any]
    description: str = ""

@router.get("/presets")
def get_preset_strategies():
    return {"strategies": StrategyRegistry.list_strategies()}

@router.get("/")
def get_strategies(db: Session = Depends(get_db)):
    strategies = db.query(DBStrategy).all()
    return {"strategies": [
        {
            "id": s.id,
            "name": s.name,
            "type": s.type,
            "params": s.params,
            "is_active": s.is_active,
            "description": s.description
        }
        for s in strategies
    ]}

@router.post("/")
def create_strategy(data: StrategyCreate, db: Session = Depends(get_db)):
    strategy = DBStrategy(
        name=data.name,
        type=data.type,
        params=data.params,
        description=data.description,
        is_active=True
    )
    db.add(strategy)
    db.commit()
    db.refresh(strategy)
    return {"id": strategy.id, "name": strategy.name}

@router.put("/{strategy_id}/toggle")
def toggle_strategy(strategy_id: int, db: Session = Depends(get_db)):
    strategy = db.query(DBStrategy).filter(DBStrategy.id == strategy_id).first()
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")
    strategy.is_active = not strategy.is_active
    db.commit()
    return {"id": strategy.id, "is_active": strategy.is_active}
