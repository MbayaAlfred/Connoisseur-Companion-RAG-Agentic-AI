"""Connoisseur Companion: MCP restaurant data server (Module 4, Lesson 1)."""
import json
from pathlib import Path
from fastmcp import FastMCP

mcp = FastMCP("Connoisseur-Server")
DATA_DIR = Path(__file__).resolve().parents[2] / "data"
CULINARY_MAP_PATH = DATA_DIR / "California-Culinary-Map.txt"
RESTAURANT_DATA_PATH = DATA_DIR / "structured_restaurant_data.json"
REVIEW_DATA_PATH = DATA_DIR / "augmented_user_review.json"


def load_restaurant_data() -> list[dict]:
    """Load structured restaurant data produced in Module 1."""
    with RESTAURANT_DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_review_data() -> list[dict]:
    """Load augmented user reviews produced in Module 1."""
    with REVIEW_DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@mcp.resource("culinary-map://california")
def get_culinary_map() -> str:
    """Raw California Culinary Map restaurant descriptions."""
    return CULINARY_MAP_PATH.read_text(encoding="utf-8")


@mcp.tool()
def get_restaurant_info(restaurant_name: str) -> str:
    """Search for restaurants by partial name; return structured details as JSON."""
    restaurants = load_restaurant_data()
    query = restaurant_name.lower().strip()
    matches = [r for r in restaurants if query in r["name"].lower() or r["name"].lower() in query]
    if not matches:
        return json.dumps({"status": "not_found", "message": f"No restaurant found matching '{restaurant_name}'.", "suggestion": "Try a partial name like 'Iron' or 'Sakura'."}, indent=2)
    return json.dumps({"status": "found", "count": len(matches), "results": matches}, indent=2)


@mcp.tool()
def recommend_by_vibe(vibe: str) -> str:
    """Find restaurants by vibe keyword in structured tags, descriptions and raw text."""
    restaurants = load_restaurant_data()
    vibe_lower = vibe.lower().strip()
    structured_matches = []
    for restaurant in restaurants:
        vibes_list = [v.lower() for v in restaurant.get("vibes", [])]
        description = restaurant.get("description", "").lower()
        if any(vibe_lower in v for v in vibes_list) or vibe_lower in description:
            structured_matches.append({
                "name": restaurant["name"],
                "neighborhood": restaurant["neighborhood"],
                "cuisine": restaurant["cuisine"],
                "rating": restaurant["rating"],
                "vibes": restaurant["vibes"],
                "price_range": restaurant["price_range"],
            })
    paragraphs = CULINARY_MAP_PATH.read_text(encoding="utf-8").split("\n\n")
    text_excerpts = [p.strip()[:300] for p in paragraphs if vibe_lower in p.lower() and p.strip()]
    return json.dumps({"vibe_searched": vibe, "structured_matches": structured_matches, "raw_text_excerpts": text_excerpts[:5]}, indent=2)


@mcp.tool()
def get_review(restaurant_name: str) -> str:
    """Retrieve the first matching augmented restaurant review as JSON."""
    reviews = load_review_data()
    query = restaurant_name.lower().strip()
    matching_review = next((r for r in reviews if query in r["restaurant_name"].lower()), None)
    if not matching_review:
        return json.dumps({"status": "not_found", "message": f"No review found for '{restaurant_name}'."}, indent=2)
    return json.dumps({
        "status": "found",
        "restaurant": matching_review["restaurant_name"],
        "reviewer": matching_review["reviewer"],
        "rating": matching_review["rating"],
        "review_text": matching_review["review_text"],
        "image_description": matching_review.get("image_description", "N/A"),
        "visit_date": matching_review.get("visit_date", "N/A"),
    }, indent=2)


if __name__ == "__main__":
    mcp.run()
