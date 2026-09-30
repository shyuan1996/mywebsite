// Shared interactions. Company content remains readable without JavaScript.
document.documentElement.classList.add("js");
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
const menuButton = document.querySelector(".menu-toggle");
const navigation = document.querySelector("#site-nav");
function closeMenu(returnFocus = false) {
  menuButton?.setAttribute("aria-expanded", "false");
  navigation?.classList.remove("is-open");
  document.body.classList.remove("menu-open");
  document.querySelectorAll("main,.contact-cta,.site-footer").forEach((el) => {
    el.inert = false;
  });
  if (returnFocus) menuButton?.focus();
}
menuButton?.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(open));
  navigation.classList.toggle("is-open", open);
  document.body.classList.toggle("menu-open", open);
  document.querySelectorAll("main,.contact-cta,.site-footer").forEach((el) => {
    el.inert = open;
  });
});
navigation?.addEventListener("click", (e) => {
  if (e.target.closest("a")) closeMenu();
});
document.addEventListener("keydown", (e) => {
  if (menuButton?.getAttribute("aria-expanded") !== "true") return;
  if (e.key === "Escape") {
    e.preventDefault();
    closeMenu(true);
  }
  if (e.key === "Tab") {
    const controls = [menuButton, ...navigation.querySelectorAll("a")];
    if (e.shiftKey && document.activeElement === controls[0]) {
      e.preventDefault();
      controls.at(-1).focus();
    } else if (!e.shiftKey && document.activeElement === controls.at(-1)) {
      e.preventDefault();
      controls[0].focus();
    }
  }
});
matchMedia("(min-width: 781px)").addEventListener("change", (e) => {
  if (e.matches) closeMenu();
});
document.querySelectorAll("[data-year]").forEach((el) => {
  el.textContent = new Date().getFullYear();
});
if (!reduceMotion && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver(
    (entries) =>
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.remove("is-pending");
          observer.unobserve(entry.target);
        }
      }),
    { threshold: 0.06 },
  );
  document
    .querySelectorAll(
      ".section-heading,.craft-grid,.values-grid,.team-section,.service-detail-row,.process-heading",
    )
    .forEach((el) => {
      // Do not delay above-the-fold content or alter the reading order.
      if (el.getBoundingClientRect().top > innerHeight) {
        el.classList.add("reveal", "is-pending");
        observer.observe(el);
      }
    });
}

// A public, versioned snapshot contains published projects only. No Airtable key is shipped.
let projectPromise;
function getProjects() {
  if (!projectPromise)
    projectPromise = fetch("data/projects.json")
      .then((response) => {
        if (!response.ok) throw Error("Project archive unavailable");
        return response.json();
      })
      .catch((error) => {
        projectPromise = undefined;
        throw error;
      });
  return projectPromise;
}
function node(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}
const arrowSVG =
  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 19 19 5M5 5h14v14"/></svg>';
const dialog = document.querySelector(".project-dialog");
let activeProject,
  photoIndex = 0,
  opener;
function showPhoto(index) {
  photoIndex =
    (index + activeProject.images.length) % activeProject.images.length;
  const image = document.querySelector("#gallery-image");
  image.src = activeProject.images[photoIndex];
  image.alt = `${activeProject.name}，照片 ${photoIndex + 1}`;
  document.querySelector("#gallery-count").textContent =
    `${String(photoIndex + 1).padStart(2, "0")} / ${String(activeProject.images.length).padStart(2, "0")}`;
  document
    .querySelectorAll(".gallery-thumbs button")
    .forEach((button, i) =>
      button.setAttribute("aria-pressed", String(i === photoIndex)),
    );
  document.querySelector(".gallery-prev").hidden = document.querySelector(
    ".gallery-next",
  ).hidden = activeProject.images.length <= 1;
}
async function openProject(id, button) {
  if (!dialog) return;
  button.setAttribute("aria-busy", "true");
  try {
    const projects = await getProjects();
    activeProject = projects.find((p) => p.id === id);
    if (!activeProject) throw Error("Project not found");
    opener = button;
    document.querySelector("#gallery-title").textContent = activeProject.name;
    document.querySelector("#gallery-category").textContent =
      activeProject.category + " / PROJECT ARCHIVE";
    document.querySelector("#gallery-description").textContent =
      activeProject.description;
    const thumbs = document.querySelector("#gallery-thumbs");
    thumbs.replaceChildren();
    activeProject.images.forEach((src, i) => {
      const thumb = node("button");
      thumb.type = "button";
      thumb.setAttribute("aria-label", `查看第 ${i + 1} 張照片`);
      const image = node("img");
      image.src = src;
      image.alt = "";
      image.loading = "lazy";
      thumb.append(image);
      thumb.addEventListener("click", () => showPhoto(i));
      thumbs.append(thumb);
    });
    showPhoto(0);
    dialog.showModal();
    document.body.classList.add("dialog-open");
    document.querySelector(".dialog-close").focus();
  } catch {
    let error = button.parentElement.querySelector(".gallery-error");
    if (!error) {
      error = node("p", "gallery-error", "相簿暫時無法開啟，請稍後再試。");
      error.setAttribute("role", "status");
      button.after(error);
    }
  } finally {
    button.removeAttribute("aria-busy");
  }
}
document.addEventListener("click", (e) => {
  const button = e.target.closest("[data-project]");
  if (button) openProject(button.dataset.project, button);
});
if (dialog) {
  document
    .querySelector(".dialog-close")
    .addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) {
      const r = dialog.getBoundingClientRect();
      if (
        e.clientX < r.left ||
        e.clientX > r.right ||
        e.clientY < r.top ||
        e.clientY > r.bottom
      )
        dialog.close();
    }
  });
  dialog.addEventListener("close", () => {
    document.body.classList.remove("dialog-open");
    opener?.focus();
  });
  dialog.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      showPhoto(photoIndex - 1);
    }
    if (e.key === "ArrowRight") {
      e.preventDefault();
      showPhoto(photoIndex + 1);
    }
  });
  document
    .querySelector(".gallery-prev")
    .addEventListener("click", () => showPhoto(photoIndex - 1));
  document
    .querySelector(".gallery-next")
    .addEventListener("click", () => showPhoto(photoIndex + 1));
}
const portfolioGrid = document.querySelector("#portfolio-grid");
if (portfolioGrid) {
  let all = [],
    category = "所有作品",
    query = "",
    page = 1;
  const perPage = 12;
  const status = document.querySelector("#project-status");
  const pagination = document.querySelector("#pagination");
  const categories = [
    "所有作品",
    "北北基",
    "桃竹苗",
    "中彰投",
    "雲嘉南",
    "高屏",
    "宜花東",
    "客製品",
  ];
  function render(scroll = false) {
    const filtered = all.filter(
      (p) =>
        (category === "所有作品" || p.category === category) &&
        `${p.name} ${p.category} ${p.description}`
          .toLocaleLowerCase()
          .includes(query),
    );
    const pages = Math.ceil(filtered.length / perPage);
    page = Math.max(1, Math.min(page, pages || 1));
    portfolioGrid.replaceChildren();
    filtered.slice((page - 1) * perPage, page * perPage).forEach((p, i) => {
      const article = node("article", "project-card");
      const button = node("button", "project-open");
      button.type = "button";
      button.dataset.project = p.id;
      button.setAttribute("aria-label", `查看${p.name}相簿`);
      const box = node("div", "project-image");
      const image = node("img");
      image.src = p.images[0];
      image.alt = `${p.name}，${p.description || p.category}`;
      image.loading = "lazy";
      image.decoding = "async";
      image.width = 1000;
      image.height = 750;
      const arrow = node("span", "image-arrow");
      arrow.innerHTML = arrowSVG;
      box.append(
        image,
        arrow,
        node(
          "span",
          "image-count",
          `${String(p.images.length).padStart(2, "0")} PHOTOS`,
        ),
      );
      const meta = node("div", "project-meta");
      meta.append(
        node("span", "eyebrow", p.description || p.category),
        node(
          "span",
          "project-no",
          String((page - 1) * perPage + i + 1).padStart(2, "0"),
        ),
      );
      button.append(box, meta, node("h3", "", p.name));
      article.append(button);
      portfolioGrid.append(article);
    });
    if (!filtered.length) {
      const empty = node("div", "empty-state");
      empty.append(
        node("h2", "", "暫時沒有符合的作品。"),
        node("p", "", "換個關鍵字，或選擇其他地區，再看看。"),
      );
      portfolioGrid.append(empty);
    }
    status.textContent = filtered.length
      ? `${category} · ${filtered.length} 件作品 · 第 ${page} / ${pages} 頁`
      : "沒有符合條件的作品";
    pagination.replaceChildren();
    function pageButton(label, target, current = false, disabled = false) {
      const button = node("button", "", label);
      button.type = "button";
      button.disabled = disabled;
      if (current) button.setAttribute("aria-current", "page");
      if (typeof label === "number")
        button.setAttribute("aria-label", `第 ${label} 頁`);
      button.addEventListener("click", () => {
        page = target;
        render(true);
      });
      pagination.append(button);
    }
    if (pages > 1) {
      pageButton("←", page - 1, false, page === 1);
      for (let i = 1; i <= pages; i++) pageButton(i, i, i === page);
      pageButton("→", page + 1, false, page === pages);
    }
    if (scroll)
      document
        .querySelector(".archive-toolbar")
        .scrollIntoView({
          behavior: reduceMotion ? "instant" : "smooth",
          block: "start",
        });
  }
  getProjects()
    .then((projects) => {
      all = projects;
      const filters = document.querySelector("#filter-buttons");
      categories
        .filter((c) => c === "所有作品" || all.some((p) => p.category === c))
        .forEach((c) => {
          const button = node("button", "", c);
          button.type = "button";
          button.setAttribute("aria-pressed", String(c === category));
          button.addEventListener("click", () => {
            category = c;
            page = 1;
            filters
              .querySelectorAll("button")
              .forEach((b) =>
                b.setAttribute("aria-pressed", String(b === button)),
              );
            render();
          });
          filters.append(button);
        });
      render();
    })
    .catch(() => {
      document.querySelector("#archive-error").hidden = false;
      status.textContent = "作品暫時無法載入";
    });
  document.querySelector("#project-search").addEventListener("input", (e) => {
    query = e.target.value.trim().toLocaleLowerCase();
    page = 1;
    render();
  });
}

const form = document.querySelector("#inquiry-form");
if (form) {
  const preview = Boolean(
    document.querySelector('meta[name="shyuan-preview"]'),
  );
  const notice = document.querySelector(".preview-notice");
  if (notice) notice.hidden = !preview;
  const service = new URLSearchParams(location.search).get("service");
  if (
    service &&
    form.elements.service.querySelector(
      `option[value="${CSS.escape(service)}"]`,
    )
  )
    form.elements.service.value = service;
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const status = document.querySelector("#form-status");
    if (preview) {
      status.textContent = "試填完成。這是設計預覽，資料沒有送出。";
      return;
    }
    const button = form.querySelector('[type="submit"]');
    button.disabled = true;
    button.setAttribute("aria-busy", "true");
    status.textContent = "正在送出需求…";
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) throw Error("Form submission failed");
      status.textContent =
        "謝謝你的訊息，需求已送出。我們將透過你提供的聯絡方式回覆。";
      form.reset();
    } catch {
      status.textContent =
        "暫時無法確認是否送出，請透過電話或 LINE 與我們聯繫。你的填寫內容已保留。";
    } finally {
      clearTimeout(timeout);
      button.disabled = false;
      button.removeAttribute("aria-busy");
    }
  });
}
document.querySelectorAll(".detail-point").forEach((point) =>
  point.addEventListener("click", () => {
    const open = point.getAttribute("aria-expanded") !== "true";
    document
      .querySelectorAll(".detail-point")
      .forEach((other) => other.setAttribute("aria-expanded", "false"));
    point.setAttribute("aria-expanded", String(open));
    const detail = document.querySelector("#hero-detail");
    detail.textContent = point.dataset.detail;
    detail.hidden = !open;
  }),
);
