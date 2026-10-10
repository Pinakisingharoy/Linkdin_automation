from pydantic import BaseModel, Field, field_validator


class LinkedInPost(BaseModel):
    author: str
    author_url: str
    post_url: str
    post_text: str
    posted_date: str | None = None


class SearchRequest(BaseModel):
    queries: list[str] = Field(default_factory=list)
    max_posts_per_query: int = Field(default=5, ge=1, le=10)
    min_relevance: int = Field(default=4, ge=0, le=10)

    @field_validator("queries")
    @classmethod
    def sanitize_queries(cls, value):
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]


class PostAnalysis(BaseModel):
    author: str
    author_url: str
    post_url: str
    post_text: str
    relevance_score: int = Field(ge=0, le=10)
    client_need: str
    matched_skills: list[str]
    connection_note: str = ""

    @field_validator("matched_skills")
    @classmethod
    def sanitize_skills(cls, value):
        if value is None:
            return []
        return [str(item).strip() for item in value if str(item).strip()]

    @field_validator("connection_note")
    @classmethod
    def enforce_char_limit(cls, value):
        return value[:250] if value else ""


class SearchResponse(BaseModel):
    total_posts_fetched: int
    qualified_leads: int
    results: list[PostAnalysis]
