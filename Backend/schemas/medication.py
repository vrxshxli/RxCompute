from datetime import datetime

from pydantic import BaseModel, Field, model_validator


class UserMedicationCreate(BaseModel):
    medicine_id: int | None = None
    custom_name: str | None = None
    dosage_instruction: str = Field(min_length=2, max_length=120)
    frequency_per_day: int = Field(default=1, ge=1, le=12)
    quantity_units: int = Field(default=30, ge=1, le=2000)

    @model_validator(mode="after")
    def validate_source(self):
        if self.medicine_id is None and not self.custom_name:
            raise ValueError("Either medicine_id or custom_name is required")
        return self


class UserMedicationUpdate(BaseModel):
    dosage_instruction: str | None = Field(default=None, min_length=2, max_length=120)
    frequency_per_day: int | None = Field(default=None, ge=1, le=12)
    quantity_units: int | None = Field(default=None, ge=1, le=2000)


class UserMedicationOut(BaseModel):
    id: int
    medicine_id: int | None
    name: str
    dosage_instruction: str
    frequency_per_day: int
    quantity_units: int
    days_left: int
    rx_required: bool
    created_at: datetime | None


class HomeSummaryOut(BaseModel):
    todays_medications: int
    refill_alert: UserMedicationOut | None = None
    monthly_total_spend: float = 0.0
    monthly_order_count: int = 0
    active_order_count: int = 0
