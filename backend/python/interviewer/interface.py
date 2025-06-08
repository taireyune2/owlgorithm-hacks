
from pydantic import BaseModel
from typing import Optional



########################## POJO #################################
# Upload resume endpoint
class Resume(BaseModel):
    email: str
    phone: Optional[str]
    rawText: str

class JobDescription(BaseModel):
    link: Optional[str]
    rawText: str

class UserInfo(BaseModel):
    session_id: int
    resume: Resume
    job_description: JobDescription