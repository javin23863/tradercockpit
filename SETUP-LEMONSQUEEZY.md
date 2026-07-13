# Lemon Squeezy setup — the only human steps left

Everything else is wired: the landing page (live at https://javin23863.github.io/soical/)
falls back to a reserve-a-seat mailto until the checkout URL exists, the app's license
gate is merged (futures PR #203), and `tools/wire_checkout.py` patches the real URL into
both surfaces in one command. These steps need YOUR identity (email verification + payout
details) so they cannot be automated.

Time: ~20 minutes. Do them in order.

## 0. (Optional but recommended) Buy the domain — ~$10/yr, 5 min
`tradercockpit.com` is taken. **thetradercockpit.com is available** and matches the
YouTube handle @Thetradercockpit exactly; `tradercockpit.io` / `.app` / `.net` are
also free. Buy at Cloudflare Registrar (at-cost) or Porkbun/Namecheap, then tell me —
I do the rest (CNAME file, GitHub Pages custom-domain config, canonical/OG/sitemap
rewrite, HTTPS enforce). Until then the site is live at the branded Pages URL:
https://javin23863.github.io/tradercockpit/

## 1. Create the account + store (~10 min)
1. https://app.lemonsqueezy.com/register — use your business email.
2. Verify the email, then create a store:
   - Store name: **TraderCockpit** → subdomain `tradercockpit.lemonsqueezy.com`
     (if taken, anything works — the wire script derives everything from the URL).
   - Currency USD.
3. Settings → Payouts: connect your bank (required before real checkout works).
   Tax/W-9 questions: LS is merchant of record, they handle sales tax.

## 2. Create the product (~5 min)
Products → New product:
- Name: **TraderCockpit Early Access**
- Pricing: **Subscription**, **$49 / month** (researched: Build Alpha $1,497 lifetime,
  StrategyQuant X $1,290–2,900, Trade Ideas $89–178/mo, TrendSpider $54–91/mo — $49
  early-access undercuts every serious comp; raise toward $99 once there's a user base).
- Confirmation/delivery text: paste the download link (step 4) + "your license key is below".
- **License keys: ENABLE.** Activation limit: **2**. Length/expiry: defaults
  (key expires with subscription — that is what the app's gate checks).
- Publish the product (store must be out of draft: Settings → General → publish store).

## 3. Wire the checkout URL (~1 min)
Product → Share → copy the buy link (`https://<store>.lemonsqueezy.com/buy/<uuid>`), then:

    python tools/wire_checkout.py https://<store>.lemonsqueezy.com/buy/<uuid>
    git add docs/index.html && git commit -m "landing: live checkout" && git push

The page button flips from mailto-fallback to the LS overlay automatically.

## 4. Host the installer (~5 min, after the customer exe is built)
Build: `powershell -File scripts/build_desktop_customer.ps1` in repos/futures.
Upload the zip to the public B2 bucket (rclone remote `hft3-b2` already configured):

    rclone copy ESQ-Cockpit-Customer.zip hft3-b2:<public-bucket>/releases/

Put that URL in the LS product's delivery/confirmation text.

## 5. Test mode end-to-end (recommended before announcing)
LS dashboard → toggle **Test mode**: buy with test card 4242…, confirm the receipt
email contains a license key, activate inside the customer build, then Settings →
deactivate. Flip test mode off.

## Notes
- Refund policy (LS requirement): live at /refund-policy.html — 14-day money-back,
  7-day renewal window. Support email on page: joshuajacob2386@gmail.com.
- The app validates keys against the keyless LS License API — no API key of yours
  ever ships in the app or the page.
- Price display on the page is hardcoded ($49/mo, regular-$99 anchor) — keep the LS
  price in sync if you change it.
