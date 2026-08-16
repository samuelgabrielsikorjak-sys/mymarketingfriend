from pydantic import BaseModel
from typing import Optional

class Lead(BaseModel):
    name: str
    company: str
    web_site_url: str
    sector: str
    notes: Optional[str] = None
    score: Optional[float] = None
    score_reasoning: Optional[str] = None
    
    
    
    