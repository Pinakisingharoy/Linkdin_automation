from app.models import SearchRequest, SearchResponse
from app.services.linkedin import fetch_posts_for_queries
from app.services.llm import analyze_post


async def run_search(request: SearchRequest, cv_summary: str) -> SearchResponse:
    posts = fetch_posts_for_queries(request.queries, request.max_posts_per_query)
    results = []

    for post in posts:
        analysis = await analyze_post(
            author=post.author,
            author_url=post.author_url,
            post_url=post.post_url,
            post_text=post.post_text,
            cv_summary=cv_summary,
        )
        if analysis.relevance_score >= request.min_relevance:
            results.append(analysis)

    results.sort(key=lambda item: item.relevance_score, reverse=True)

    return SearchResponse(
        total_posts_fetched=len(posts),
        qualified_leads=len(results),
        results=results,
    )
