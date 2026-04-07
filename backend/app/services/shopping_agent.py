"""
ShoppingAgentService — AP2-inspired cart building from user chat intent.

Flow:
  1. detect_shopping_intent(message) → calls Gemini (thinking_budget=0, lightweight)
     to detect if message contains shopping intent and extract item names
  2. build_cart_from_intent(intent) → fuzzy-matches items against products.json
     → builds a CartMandate (AP2 Cart Mandate concept)

The CartMandate is an in-memory dataclass passed between services (not a DB model).
"""
from __future__ import annotations

import json
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types
from loguru import logger

from app.core.config import settings

_MODEL = "gemini-2.5-flash"
_NO_THINK = types.GenerateContentConfig()

_PRODUCTS_FILE = Path(__file__).parent.parent / "mocks" / "products.json"

_INTENT_PROMPT = """\
Phân tích tin nhắn và xác định có ý định mua sắm nguyên liệu nấu ăn không.

Tin nhắn: "{message}"

Trả về JSON (không có markdown, không giải thích):
{{
  "has_intent": true/false,
  "items_mentioned": ["tên nguyên liệu 1", "tên nguyên liệu 2"],
  "suggested_store": null
}}

Ý định mua sắm bao gồm: mua nguyên liệu, đặt hàng đồ ăn, mua sắm cho bữa ăn, \
cần mua, order, giúp tôi mua, mua giúp, lấy đồ, lấy nguyên liệu.
Không phải ý định mua sắm: hỏi công thức, hỏi dinh dưỡng, hỏi cách nấu.

Nếu không có ý định mua sắm: has_intent=false, items_mentioned=[].
"""

# ── Dataclasses (AP2 Cart Mandate) ────────────────────────────────────────────


@dataclass
class CartMandateItem:
    product_id: str
    product_name: str
    product_emoji: str
    unit: str
    quantity: int
    unit_price: float   # in k VND
    subtotal: float


@dataclass
class CartMandate:
    store_id: str
    store_name: str
    items: list[CartMandateItem] = field(default_factory=list)
    subtotal: float = 0.0
    delivery_fee: float = 0.0
    estimated_total: float = 0.0
    intent_description: str = ""


@dataclass
class ShoppingIntentResult:
    has_intent: bool
    items_mentioned: list[str] = field(default_factory=list)
    suggested_store: Optional[str] = None


# ── Service ───────────────────────────────────────────────────────────────────


class ShoppingAgentService:
    """Singleton service for detecting shopping intent and building cart mandates."""

    _products: list[dict] | None = None  # lazy-loaded once

    def _load_products(self) -> list[dict]:
        if self.__class__._products is None:
            self.__class__._products = json.loads(
                _PRODUCTS_FILE.read_text(encoding="utf-8")
            )
            logger.info(
                "shopping_agent:products_loaded | count={}",
                len(self.__class__._products),
            )
        return self.__class__._products

    async def detect_shopping_intent(
        self, message: str
    ) -> Optional[ShoppingIntentResult]:
        """
        Call Gemini (no thinking) to detect shopping intent in a user message.
        Returns ShoppingIntentResult or None on error.
        Times out gracefully — caller should wrap with asyncio.wait_for().
        """
        t0 = time.perf_counter()
        logger.debug(
            "shopping_agent:detect | message_len={}", len(message)
        )
        try:
            key = settings.gemini_api_key
            if not key:
                logger.warning("shopping_agent:detect | no_api_key — skipping")
                return None
            client = genai.Client(api_key=key)
            prompt = _INTENT_PROMPT.format(message=message[:500])
            response = await client.aio.models.generate_content(
                model=_MODEL,
                contents=prompt,
                config=_NO_THINK,
            )
            raw = (response.text or "").strip()
            # Strip markdown fences if present
            raw = raw.strip("`").strip()
            if raw.startswith("json"):
                raw = raw[4:].strip()
            data = json.loads(raw)
            result = ShoppingIntentResult(
                has_intent=bool(data.get("has_intent", False)),
                items_mentioned=[
                    str(i).strip() for i in data.get("items_mentioned", []) if i
                ],
                suggested_store=data.get("suggested_store"),
            )
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.debug(
                "shopping_agent:intent | has_intent={} items={} latency={}ms",
                result.has_intent, result.items_mentioned, latency_ms,
            )
            return result
        except Exception as e:
            latency_ms = round((time.perf_counter() - t0) * 1000, 1)
            logger.warning(
                "shopping_agent:intent_error | latency={}ms error={}",
                latency_ms, str(e)[:100],
            )
            return None

    async def build_cart_from_intent(
        self, intent: ShoppingIntentResult
    ) -> CartMandate:
        """
        Match items_mentioned against products.json using simple substring matching.
        Picks the store with the most product matches.
        Returns a CartMandate with matched products (quantity=1 each by default).
        """
        products = self._load_products()
        items_lower = [i.lower() for i in intent.items_mentioned]

        matched: list[dict] = []
        seen_ids: set[str] = set()

        for item_query in items_lower:
            best: dict | None = None
            best_score = 0
            for product in products:
                for kw in product.get("keywords", []):
                    kw_lower = kw.lower()
                    # Score: exact match > contains query > query contains keyword
                    if kw_lower == item_query:
                        score = 3
                    elif item_query in kw_lower or kw_lower in item_query:
                        score = 2
                    elif any(word in kw_lower for word in item_query.split()):
                        score = 1
                    else:
                        continue
                    if score > best_score and product["id"] not in seen_ids:
                        best_score = score
                        best = product
                if best_score == 3:
                    break

            if best and best_score > 0:
                logger.debug(
                    "shopping_agent:match | query={!r} product={} score={}",
                    item_query, best["id"], best_score,
                )
                matched.append(best)
                seen_ids.add(best["id"])
            else:
                logger.debug("shopping_agent:no_match | query={!r}", item_query)

        # Pick the store with the most matches, preferring suggested_store
        if not matched:
            # Fallback: return a starter cart with popular items
            logger.warning(
                "shopping_agent:fallback_cart | reason=no_product_matches items_queried={}",
                intent.items_mentioned,
            )
            matched = [p for p in products if p["id"] in ("b2", "b9", "b10")][:3]

        # Determine best store
        if intent.suggested_store:
            store_id = intent.suggested_store
        else:
            store_counts: Counter = Counter(p["store_id"] for p in matched)
            store_id = store_counts.most_common(1)[0][0]

        # Filter to only products from the chosen store, or keep any if no match
        store_products = [p for p in matched if p["store_id"] == store_id]
        if not store_products:
            store_products = matched

        # Get store metadata from the first product
        store_name = store_products[0]["store_name"]
        delivery_fee = float(store_products[0].get("delivery_fee", 15))

        mandate_items: list[CartMandateItem] = [
            CartMandateItem(
                product_id=p["id"],
                product_name=p["name"],
                product_emoji=p["emoji"],
                unit=p["unit"],
                quantity=1,
                unit_price=float(p["price"]),
                subtotal=float(p["price"]),
            )
            for p in store_products
        ]

        subtotal = sum(i.subtotal for i in mandate_items)
        intent_desc = ", ".join(intent.items_mentioned) or "mua sắm nguyên liệu"

        mandate = CartMandate(
            store_id=store_id,
            store_name=store_name,
            items=mandate_items,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            estimated_total=subtotal + delivery_fee,
            intent_description=intent_desc,
        )

        logger.info(
            "shopping_agent:cart_built | store={} items={} total={}k",
            store_id,
            len(mandate_items),
            mandate.estimated_total,
        )
        return mandate


# ── Module singleton ───────────────────────────────────────────────────────────

shopping_agent_service = ShoppingAgentService()
