from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TeamMember(BaseModel):
    """Information about a company leader or team member."""

    name: str
    role: str
    linkedin_url: Optional[str] = None

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, value):
        """Accept only real-looking LinkedIn URLs."""

        if value is None:
            return None

        if not value.startswith("https://www.linkedin.com/"):
            return None

        return value


class CompanyData(BaseModel):
    """Structured company intelligence extracted by the LLM."""

    company_overview: str = Field(
        description="A concise 2-sentence summary of what the company does."
    )

    target_audience: str = Field(
        description="The primary target audience or ideal customer profile."
    )

    contact_points: List[str] = Field(
        default_factory=list,
        description="Generic or public email addresses found on the website."
    )

    leadership: List[TeamMember] = Field(
        default_factory=list,
        description="Key leadership or team members discovered from the website."
    )

    confidence_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Estimated confidence in the completeness and quality of the extracted data."
    )