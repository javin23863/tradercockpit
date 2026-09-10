import { loadProductManifest } from "../product-manifest.mjs";

function statusText(status) {
  if (status === "available") return "Current public status: Available";
  if (status === "waitlist") return "Current public status: Waitlist";
  return "Current public status: Unavailable";
}

function platformText(platforms) {
  return Array.isArray(platforms) && platforms.length
    ? `Published platform target: ${platforms.join(" · ")}.`
    : "No public platform target is currently listed.";
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
    detail.textContent = "Pricing, download, checkout, and feature availability are shown only when the current public status explicitly publishes them.";
    return true;
  } catch {
    status.textContent = "Current public status could not be verified here";
    platform.textContent = "No availability or platform claim is inferred from a failed status read.";
    detail.textContent = "Use Updates for the current published state.";
    return false;
  }
}

renderFaqStatus();