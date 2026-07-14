# Checkout setup — retired from TraderCockpit

TraderCockpit is the media and social operation. It does not own the consumer
product's seller identity, pricing, license system, releases, refund terms, or
checkout integration.

The previous Lemon Squeezy instructions were removed because they coupled this
repository directly to the consumer application and included unverified pricing,
platform, and refund claims.

If the consumer product offers a transaction, its deployment must publish the
approved facts through `product-manifest/v1`. TraderCockpit may render only that
manifest and must not patch the consumer repository or invent fallback commerce
claims.

Allowed manifest fields are product identity, Apollo status, verified capabilities,
platforms, offer display, CTA/checkout, support, and refund links. Missing or invalid
manifests fall back to the non-transactional waitlist.
