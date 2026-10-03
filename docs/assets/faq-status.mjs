import { loadProductManifest } from "../product-manifest.mjs";

function statusText(status) {
  if (status === "available") return "TraderCockpit is available";
  if (status === "waitlist") return "TraderCockpit is on a waitlist";
  return "TraderCockpit is currently unavailable";
}

function platformText(platforms) {
  return Array.isArray(platforms) && platforms.length
    ? `Platform: ${platforms.join(" · ")}.`
    : "Platform information is not available right now.";
}

export async function renderFaqStatus(root = document) {
  const status = root.querySelector?.("[data-faq-status]");
  const platform = root.querySelector?.("[data-faq-platform]");
  const detail = root.querySelector?.("[data-faq-status-detail]");
  if (!status || !platform || !detail) return false;
  try {
    const manifest = await loadProductManifest("../product-manifest.v1.json");
    status.textContent = statusText(manifest.status);
    platform.textContent = platformText(manifest.platforms);
    detail.textContent = manifest.status === "available" ? "See Pricing for plans." : "Checkout is not open yet. See Pricing for plans and Updates for news.";
    return true;
  } catch {
    status.textContent = "Availability could not be loaded";
    platform.textContent = "Platform information could not be loaded.";
    detail.textContent = "Please try again later, or see Updates.";
    return false;
  }
}

renderFaqStatus();