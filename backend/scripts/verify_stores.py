import asyncio
import json
import os
import httpx

CANDIDATES = [
    # Shopify
    {"slug": "sapphirepk", "name": "Sapphire", "domain": "sapphirepk.com", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["pret", "unstitched"]},
    {"slug": "outfitters", "name": "Outfitters", "domain": "outfitters.com.pk", "suspected": "shopify", "price_tier": "mid", "gender": "unisex", "categories": ["western", "eastern"]},
    {"slug": "gulahmed", "name": "Gul Ahmed", "domain": "gulahmedshop.com", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["lawn", "pret"]},
    {"slug": "alkaram", "name": "Alkaram Studio", "domain": "alkaramstudio.com", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["fabric", "pret"]},
    {"slug": "bonanzasatrangi", "name": "Bonanza Satrangi", "domain": "bonanzasatrangi.com", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["unstitched", "pret"]},
    {"slug": "asimjofa", "name": "Asim Jofa", "domain": "asimjofa.com", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["luxury", "pret"]},
    {"slug": "crossstitch", "name": "Cross Stitch", "domain": "cross-stitch.pk", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["eastern"]},
    {"slug": "limelight", "name": "Limelight", "domain": "limelight.pk", "suspected": "shopify", "price_tier": "budget", "gender": "women", "categories": ["pret"]},
    {"slug": "zeen", "name": "Zeen", "domain": "zeenwomanofficial.com", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["formal", "pret"]},
    {"slug": "kayseria", "name": "Kayseria", "domain": "kayseria.com", "suspected": "shopify", "price_tier": "budget", "gender": "women", "categories": ["pret"]},
    {"slug": "ego", "name": "Ego", "domain": "pk.ego.com", "suspected": "shopify", "price_tier": "mid", "gender": "unisex", "categories": ["urban", "casual"]},
    {"slug": "charcoal", "name": "Charcoal", "domain": "charcoalpk.com", "suspected": "shopify", "price_tier": "mid", "gender": "unisex", "categories": ["smart", "casual"]},
    {"slug": "sanasafinaz", "name": "Sana Safinaz", "domain": "sanasafinaz.com", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["formal", "lawn"]},
    {"slug": "mariab", "name": "Maria B", "domain": "mariab.pk", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["bridal", "pret"]},
    {"slug": "elan", "name": "Élan", "domain": "elanofficial.com", "suspected": "shopify", "price_tier": "luxury", "gender": "women", "categories": ["occasionwear"]},
    {"slug": "mushq", "name": "Mushq", "domain": "mushq.pk", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["trendy", "pret"]},
    {"slug": "zarashahjahan", "name": "Zara Shahjahan", "domain": "zarashahjahan.com", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["signature"]},
    {"slug": "baroque", "name": "Baroque", "domain": "baroquepk.com", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["embroidered", "pret"]},
    {"slug": "rangjah", "name": "Rang Jah", "domain": "rangjah.pk", "suspected": "shopify", "price_tier": "mid", "gender": "women", "categories": ["artisanal", "eastern"]},
    {"slug": "zubiahassan", "name": "Zubia Hassan", "domain": "zubiahassan.com", "suspected": "shopify", "price_tier": "premium", "gender": "women", "categories": ["luxury", "pret"]},
    # WooCommerce
    {"slug": "generation", "name": "Generation", "domain": "generation.com.pk", "suspected": "woocommerce", "price_tier": "mid", "gender": "women", "categories": ["ethical", "fashion"]},
    {"slug": "khaadi", "name": "Khaadi", "domain": "khaadi.com", "suspected": "woocommerce", "price_tier": "mid", "gender": "women", "categories": ["eastern", "western"]},
    {"slug": "nishatlinen", "name": "Nishat Linen", "domain": "nishatlinen.com", "suspected": "woocommerce", "price_tier": "mid", "gender": "women", "categories": ["fabric", "pret"]}
]

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 (FashionAggregator/1.0)"

async def probe_endpoint(client: httpx.AsyncClient, url: str) -> tuple[int, bool, int]:
    try:
        response = await client.get(url, timeout=6.0, follow_redirects=True)
        if response.status_code == 200:
            try:
                data = response.json()
                # Check for products key in Shopify, or direct list in WooCommerce
                if isinstance(data, dict) and "products" in data:
                    return 200, True, len(data["products"])
                elif isinstance(data, list):
                    return 200, True, len(data)
                return 200, False, 0
            except ValueError:
                return 200, False, 0
        return response.status_code, False, 0
    except httpx.HTTPError:
        return 0, False, 0

async def verify_store(client: httpx.AsyncClient, candidate: dict) -> dict:
    domain = candidate["domain"]
    
    shopify_url = f"https://{domain}/products.json?limit=1"
    woo_url = f"https://{domain}/wp-json/wc/store/v1/products?per_page=1"
    
    shopify_status, shopify_valid, shopify_count = await probe_endpoint(client, shopify_url)
    woo_status, woo_valid, woo_count = await probe_endpoint(client, woo_url)
    
    detected = "unknown"
    active = False
    endpoint = ""
    
    if shopify_valid:
        detected = "shopify"
        active = True
        endpoint = "/products.json"
    elif woo_valid:
        detected = "woocommerce"
        active = True
        endpoint = "/wp-json/wc/store/v1/products"
    
    # Fallback to suspected if active check failed but we want a configuration entry
    if not active:
        detected = candidate["suspected"]
        endpoint = "/products.json" if detected == "shopify" else "/wp-json/wc/store/v1/products"
    
    return {
        "slug": candidate["slug"],
        "name": candidate["name"],
        "base_url": f"https://{domain}",
        "platform": detected,
        "products_endpoint": endpoint,
        "price_tier": candidate["price_tier"],
        "gender": candidate["gender"],
        "categories": candidate["categories"],
        "active": active,
        "shopify_status": shopify_status,
        "woo_status": woo_status
    }

async def main():
    headers = {"User-Agent": USER_AGENT}
    
    # We use a transport with verify=False or standard settings. Some sites might have ssl issues.
    async with httpx.AsyncClient(headers=headers, verify=False) as client:
        tasks = [verify_store(client, c) for c in CANDIDATES]
        results = await asyncio.gather(*tasks)
    
    print("\nVerification Results:")
    print(f"{'Brand':<20} | {'Shopify Status':<14} | {'Woo Status':<12} | {'Detected Platform':<18} | {'Active':<6}")
    print("-" * 78)
    
    stores_config = []
    active_count = 0
    
    for r in results:
        print(f"{r['name']:<20} | {r['shopify_status']:<14} | {r['woo_status']:<12} | {r['platform']:<18} | {str(r['active']):<6}")
        config_entry = {
            "slug": r["slug"],
            "name": r["name"],
            "base_url": r["base_url"],
            "platform": r["platform"],
            "products_endpoint": r["products_endpoint"],
            "price_tier": r["price_tier"],
            "gender": r["gender"],
            "categories": r["categories"],
            "active": r["active"]
        }
        stores_config.append(config_entry)
        if r["active"]:
            active_count += 1
            
    # Write to backend/config/stores.json
    config_dir = os.path.join("d:\\Hackathon_AtomCamp", "backend", "config")
    os.makedirs(config_dir, exist_ok=True)
    config_path = os.path.join(config_dir, "stores.json")
    
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(stores_config, f, indent=2)
        
    print(f"\nWritten {len(stores_config)} stores to {config_path} ({active_count} active).")

if __name__ == "__main__":
    # Disable SSL warning spam since we verify=False
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    asyncio.run(main())
