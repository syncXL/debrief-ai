from pydantic import BaseModel, Field

class Preference(BaseModel):
    refined_prompt : str = Field(description="The refined prompt")
    hours : int = Field(description="The time window")
