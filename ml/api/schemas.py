from pydantic import BaseModel, Field, field_validator, model_validator


class PricePredictionRequest(BaseModel):
    product_id: int | None = Field(default=None, gt=0, description="Existing product id to load from PostgreSQL.")
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    brand: str | None = Field(default=None, max_length=120)
    category_id: int | None = Field(default=None, ge=0)
    subcategory_id: int | None = Field(default=None, ge=0)
    category_name: str | None = Field(default=None, max_length=120)
    subcategory_name: str | None = Field(default=None, max_length=120)
    discount_percent: float | None = Field(default=None, ge=0, le=100)
    rating_avg: float | None = Field(default=None, ge=0, le=5)
    review_count: int | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    tags: list[str] | None = Field(default=None, max_length=50)
    is_active: bool | None = None

    @field_validator("title", "description", "brand", "category_name", "subcategory_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None

    @field_validator("tags")
    @classmethod
    def strip_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        clean = [item.strip() for item in value if item and item.strip()]
        return clean or None

    @model_validator(mode="after")
    def require_product_id_or_features(self):
        payload = self.model_dump(exclude_none=True)
        if not payload:
            raise ValueError("Provide product_id or product feature fields for price prediction.")
        if "product_id" not in payload:
            required = {
                "brand",
                "category_name",
                "subcategory_name",
                "discount_percent",
                "rating_avg",
                "review_count",
                "stock",
            }
            missing = sorted(required - payload.keys())
            if missing:
                raise ValueError(
                    "Provide product_id or complete product feature fields for price prediction. "
                    f"Missing: {', '.join(missing)}"
                )
        return self
