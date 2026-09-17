(() => {
  "use strict";
  const root = document.documentElement;
  root.classList.add("lab-js");
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const reveal = [...document.querySelectorAll("[data-lab-reveal]")];
  if (reduced || typeof IntersectionObserver !== "function") {
    reveal.forEach((node) => node.classList.add("is-visible"));
  } else {
    const observer = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (!entry.isIntersecting) continue;
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
    reveal.forEach((node) => observer.observe(node));
  }
  if (reduced) return;
  const product = document.querySelector("[data-lab-parallax] .lab-monitor");
  const hero = document.querySelector(".lab-hero");
  if (!product || !hero) return;
  hero.addEventListener("pointermove", (event) => {
    if (matchMedia("(pointer: coarse)").matches) return;
    const box = hero.getBoundingClientRect();
    const x = (event.clientX - box.left) / box.width - 0.5;
    const y = (event.clientY - box.top) / box.height - 0.5;
    product.style.transform = `rotateY(${-8 + x * 2.4}deg) rotateX(${1.6 - y * 1.6}deg) rotateZ(-1deg) translate3d(${x * 5}px,${y * 4}px,0)`;
  }, { passive: true });
  hero.addEventListener("pointerleave", () => {
    product.style.transform = "";
  }, { passive: true });
})();
