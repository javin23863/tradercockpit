import { loadProductManifest } from "../product-manifest.mjs";

function statusText(status) {
  if (status === "available") return "TraderCockpit access: Available";
  if (status === "waitlist") return "TraderCockpit access: Waitlist";
  return "TraderCockpit access: Unavailable";
}

function platformText(platforms) {
  return Array.isArray(platforms) && platforms.length
    ? `Platform: ${platforms.join(" ? ")}.`
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
    detail.textContent = "See Pricing and Updates for the latest subscription, download, and release information.";
    return true;
  } catch {
    status.textContent = "Availability could not be loaded right now";
    platform.textContent = "Platform information could not be loaded.";
    detail.textContent = "Try Updates for the latest product information.";
    return false;
  }
}

renderFaqStatus();