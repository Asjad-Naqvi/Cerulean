import pytest
from tools.store_tools import select_target_stores_fn, ACTIVE_STORES

def test_select_target_stores_defaults():
    # Calling with default values should return some stores if active list is not empty
    slugs = select_target_stores_fn()
    assert isinstance(slugs, list)
    if ACTIVE_STORES:
        assert len(slugs) > 0
        assert all(isinstance(s, str) for s in slugs)

def test_select_target_stores_gender_matching():
    # If we filter by 'women', it should only return stores that match 'women' or 'unisex' / 'any'
    slugs = select_target_stores_fn(gender="women")
    assert isinstance(slugs, list)
    
    # Check that each returned slug belongs to an active store with matching gender
    store_map = {s["slug"]: s for s in ACTIVE_STORES}
    for slug in slugs:
        store = store_map[slug]
        assert store["gender"] in ("women", "unisex", "any")

def test_select_target_stores_price_matching():
    # If we filter by budget, the store's price_tier should be 'budget'
    slugs = select_target_stores_fn(price_tier="budget")
    
    store_map = {s["slug"]: s for s in ACTIVE_STORES}
    for slug in slugs:
        store = store_map[slug]
        assert store["price_tier"] == "budget"
