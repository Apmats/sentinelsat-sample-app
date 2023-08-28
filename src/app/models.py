from sqlmodel import SQLModel, Field


class BoundingBox(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    image_path: str
