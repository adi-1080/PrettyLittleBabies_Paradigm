import json
from pathlib import Path
from typing import List, Optional, Type, TypeVar

from pydantic import BaseModel

COLLECTIONS_DIR = Path(__file__).resolve().parent / "collections"
T = TypeVar("T", bound=BaseModel)


def save_collection(filename: str, items: List[BaseModel]) -> Path:
    COLLECTIONS_DIR.mkdir(exist_ok=True)
    path = COLLECTIONS_DIR / f"{filename}.json"
    data = [item.model_dump(mode="json") for item in items]
    path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
    print(f"💾  Saved {len(items)} item(s) → {path.relative_to(Path(__file__).resolve().parent)}")
    return path


def save_single(filename: str, item: BaseModel) -> Path:
    COLLECTIONS_DIR.mkdir(exist_ok=True)
    path = COLLECTIONS_DIR / f"{filename}.json"
    path.write_text(json.dumps(item.model_dump(mode="json"), indent=2, default=str), encoding="utf-8")
    print(f"💾  Saved → {path.relative_to(Path(__file__).resolve().parent)}")
    return path


def load_collection(filename: str, model_class: Type[T]) -> List[T]:
    path = COLLECTIONS_DIR / f"{filename}.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [model_class(**item) for item in data]


def load_single(filename: str, model_class: Type[T]) -> Optional[T]:
    path = COLLECTIONS_DIR / f"{filename}.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return model_class(**data)
