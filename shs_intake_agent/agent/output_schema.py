from pydantic import BaseModel, Field, validator
from typing import Optional, List

class IntakeData(BaseModel):
    name: str = Field(..., description="Full name of the client")
    age: int = Field(..., ge=0, le=120, description="Age of the client")
    medicaid_status: bool = Field(..., description="Is the client currently on Medicaid?")
    disability_type: Optional[str] = Field(None, description="Type of disability, if any")
    housing_status: str = Field(..., description="Current housing status (e.g., homeless, at risk, stably housed)")
    eligible: Optional[bool] = Field(None, description="Eligibility for SHS Housing Stabilization Services")
    eligibility_score: Optional[int] = Field(None, ge=0, le=10, description="Eligibility assessment score")
    eligibility_reasons: Optional[List[str]] = Field(None, description="List of reasons for eligibility decision")

    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Name must not be empty')
        return v

    @validator('housing_status')
    def housing_status_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Housing status must not be empty')
        return v 