"""
app.py — Terraria Search Engine API
FastAPI backend serving search results and index stats.
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from search_engine import SearchEngine
import os

app = FastAPI(title="Terraria Search Engine")

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Load search engine once at startup
print("Loading search engine...")
engine = SearchEngine("corpus.json")
print(f"Ready. {engine.index.total_docs} docs indexed.")


# ---------------------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------------------

@app.get("/")
async def home(request: Request):
    stats = engine.get_stats()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "request": request,
            "stats": stats,
        },
    )


@app.get("/search")
async def search(
    q: str = Query(default="", description="Search query"),
    top_k: int = Query(default=10, ge=1, le=30),
    category: str = Query(default="", description="Filter by category"),
):
    """
    Search endpoint. Returns JSON with results, spell suggestion, and stats.
    """
    if not q.strip():
        return JSONResponse({"query": "", "results": [], "total_results": 0,
                             "suggestion": None, "used_suggestion": False,
                             "search_time_ms": 0, "stats": engine.get_stats()})

    result = engine.search(q.strip(), top_k=top_k)

    # Optional category filter (applied post-search)
    if category:
        result["results"] = [
            r for r in result["results"]
            if r["category"].lower() == category.lower()
        ]
        result["total_results"] = len(result["results"])

    return JSONResponse(result)


@app.get("/stats")
async def stats():
    """Return index statistics."""
    return JSONResponse(engine.get_stats())


@app.get("/index-view")
async def index_view(
    term: str = Query(default="", description="Term to look up in index"),
):
    """
    Return posting list for a specific term (for debugging / visualization).
    """
    if not term:
        # Return top 50 terms by document frequency
        top_terms = sorted(
            engine.index.index.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:50]
        return JSONResponse({
            "top_terms": [
                {"term": t, "doc_freq": len(postings), "postings": postings}
                for t, postings in top_terms
            ]
        })

    from search_engine import stem
    stemmed = stem(term.lower())
    postings = engine.index.index.get(stemmed, {})
    return JSONResponse({
        "term": term,
        "stemmed": stemmed,
        "doc_freq": len(postings),
        "postings": postings,
    })