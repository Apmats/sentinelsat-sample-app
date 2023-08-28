from sqlmodel import SQLModel, Field


class BoundingBox(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    min_x: float = Field(index=True)
    min_y: float = Field(index=True)
    max_x: float = Field(index=True)
    max_y: float = Field(index=True)
    image_path: str
