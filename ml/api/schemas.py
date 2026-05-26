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

    # ── New causal price-driver fields ──────────────────────────────────
    # NOTE: supplier_cost and margin_pct are intentionally excluded — they
    #       are leakage features that must never be supplied at inference.
    brand_tier: int | None = Field(
        default=None, ge=1, le=5,
        description="Brand quality tier (1=budget … 5=flagship).",
    )
    product_tier: int | None = Field(
        default=None, ge=1, le=5,
        description="Product quality tier (1=entry … 5=premium).",
    )
    condition: str | None = Field(
        default=None, max_length=30,
        description="Product condition: 'new', 'refurbished', 'used', or 'open_box'.",
    )
    release_year: int | None = Field(
        default=None, ge=2000, le=2030,
        description="Product release/model year.",
    )
    warranty_months: int | None = Field(
        default=None, ge=0, le=120,
        description="Warranty duration in months.",
    )
    spec_score: float | None = Field(
        default=None, ge=0, le=100,
        description="Normalised specification/feature score (0-100).",
    )

    @field_validator("title", "description", "brand", "category_name", "subcategory_name")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip()
        return clean or None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: str | None) -> str | None:
        if value is None:
            return None
        clean = value.strip().lower()
        allowed = {"new", "refurbished", "used", "open_box"}
        if clean not in allowed:
            raise ValueError(f"condition must be one of {sorted(allowed)}, got '{clean}'")
        return clean

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
