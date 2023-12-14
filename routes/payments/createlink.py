donotload = False
import json
from fastapi import APIRouter, Request, Response
from app import CONFIG
import aiohttp

router = APIRouter()
CONFIG = CONFIG()
def setup():
    @router.get("/")
    async def main(request: Request, amount: int, typeOfPayment: str = 'one_time', currency: str = CONFIG.currency, intervalCount: int = 1):
        """Generates a payment link."""
        if CONFIG.enforceCurrency and currency != CONFIG.currency:
            return Response(json.dumps({"error": "Currency not supported."}), 400)
        elif amount < CONFIG.minimumAmount:
            return Response(json.dumps({"error": "Amount is too low."}), 400)
        elif typeOfPayment == "recurring" and intervalCount < 1 or intervalCount > 12:
            return Response(json.dumps({"error": "Interval count is invalid. Intervals over 12 or under 1 are not supported by stripe."}), 400)
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.stripe.com/v1/prices/search", headers={"Authorization": f'Bearer {CONFIG.stripeToken}'}, params={"query": f'product:"{CONFIG.productID}" and type:"{typeOfPayment}" and currency:"{currency}"'}) as resp:
                data = await resp.json()
            for i in data["data"]:
                if i["unit_amount"] == amount:
                    priceID = i["id"]
                    break

            if not "priceID" in locals():
                async with session.post("https://api.stripe.com/v1/prices", headers={"Authorization": f'Bearer {CONFIG.stripeToken}'}, data={"currency": currency, "product":CONFIG.productID, "recurring[interval]": CONFIG.paymentCycle, "recurring[interval_count]": intervalCount, "unit_amount": amount}) as resp:
                    priceID = (await resp.json())['id']

            async with session.post("https://api.stripe.com/v1/payment_links", headers={"Authorization": f'Bearer {CONFIG.stripeToken}'}, data={"after_completion[redirect][url]": CONFIG.redirectURL+"?session={CHECKOUT_SESSION_ID}", "after_completion[type]":"redirect", "line_items[0][price]": priceID, "line_items[0][quantity]": 1, "automatic_tax[enabled]": True, "inactive_message": CONFIG.inactiveMessage}) as resp:
                data = await resp.json()

        return Response(json.dumps({"Message": "Link created!", "url": data["url"]}), 200)