class PhotoGallery {
  constructor() {
    this.pswpElement = document.querySelector(".pswp");
    this.items = [];
    this.shown = [];
    this.subfolders = [];
    this.controllers = {};
    this.tagDropdownShown = false;

    this.debounce = this.debounce.bind(this);
    this.openSwipe = this.openSwipe.bind(this);
    this.prefetch = this.prefetch.bind(this);
    this.cancel = this.cancel.bind(this);
    this.reset = this.reset.bind(this);
    this.recursive = this.recursive.bind(this);
    this.requestMetadata = this.requestMetadata.bind(this);
    this.filter = this.filter.bind(this);
    this.updateImageList = this.updateImageList.bind(this);
    this.setFilter = this.setFilter.bind(this);
    this.toggleTag = this.toggleTag.bind(this);
    this.setupDropdownToggle = this.setupDropdownToggle.bind(this);
    this.setupTagHandlers = this.setupTagHandlers.bind(this);
    this.setupClickHandlers = this.setupClickHandlers.bind(this);
    this.scrollFunction = this.scrollFunction.bind(this);
    this.topFunction = this.topFunction.bind(this);
    this.onLoad = this.onLoad.bind(this);

    this.init();
  }

  debounce(fn, delay) {
    let timeoutId;
    return (...args) => {
      clearTimeout(timeoutId);
      timeoutId = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  openSwipe(imgIndex) {
    const options = { index: imgIndex };
    const gallery = new PhotoSwipe(
      this.pswpElement,
      PhotoSwipeUI_Default,
      this.shown,
      options
    );
    gallery.init();
  }

  prefetch(imgIndex) {
    if (this.controllers[imgIndex]) {
      this.cancel(imgIndex);
    }
    const controller = new AbortController();
    const signal = controller.signal;
    this.controllers[imgIndex] = controller;
    const urlToFetch = this.items[imgIndex]?.src;
    if (urlToFetch) {
      fetch(urlToFetch, { method: "GET", signal }).catch(() => {});
    }
  }

  cancel(imgIndex) {
    if (this.controllers[imgIndex]) {
      this.controllers[imgIndex].abort();
      delete this.controllers[imgIndex];
    }
  }

  reset() {
    const content = document.documentElement.innerHTML;
    const title = document.title;
    const folders = document.querySelector(".folders");
    let path = window.location.origin + window.location.pathname;
    if (path.startsWith("null")) {
      path = window.location.protocol + "//" + path.substring(4);
    }

    if (folders) folders.style.display = "";
    document.getElementById("recursive").checked = false;
    document
      .querySelectorAll("#tagdropdown input.tagcheckbox:checked")
      .forEach((checkbox) => (checkbox.checked = false));
    window.history.replaceState(
      { html: content, pageTitle: title },
      "",
      path
    );
    this.requestMetadata();
  }

  async recursive() {
    const loc = new URL(window.location.href);
    const content = document.documentElement.innerHTML;
    const title = document.title;
    const isChecked = document.getElementById("recursive")?.checked;
    const folders = document.querySelector(".folders");

    if (!isChecked) {
      if (folders) folders.style.display = "";
      loc.searchParams.delete("recursive");
      window.history.replaceState({ html: content, pageTitle: title }, "", loc);
      this.requestMetadata();
      return;
    }

    if (folders) folders.style.display = "none";
    loc.searchParams.delete("recursive");
    loc.searchParams.append("recursive", true);
    window.history.replaceState({ html: content, pageTitle: title }, "", loc);

    const visited = new Set();
    const existingItems = new Set();
    const newItems = [];

    try {
      const response = await fetch(".metadata.json");
      if (!response.ok) throw new Error("Failed to fetch metadata");
      const data = await response.json();

      this.items = [];
      this.subfolders = data.subfolders || [];

      for (const image of Object.values(data.images || {})) {
        newItems.push(image);
        existingItems.add(image.src);
      }
    } catch {
      return;
    }

    const fetchFoldersRecursively = async (folderList) => {
      if (!Array.isArray(folderList)) return;
      const nextLevel = [];
      await Promise.all(
        folderList.map(async (folder) => {
          if (!folder || !folder.metadata || visited.has(folder.url)) return;
          visited.add(folder.url);
          try {
            const response = await fetch(folder.metadata);
            if (!response.ok) throw new Error();
            const data = await response.json();
            for (const image of Object.values(data.images || {})) {
              if (!existingItems.has(image.src)) {
                newItems.push(image);
                existingItems.add(image.src);
              }
            }
            if (Array.isArray(data.subfolders))
              nextLevel.push(...data.subfolders);
          } catch {}
        })
      );
      if (nextLevel.length > 0) await fetchFoldersRecursively(nextLevel);
    };

    await fetchFoldersRecursively(this.subfolders);
    this.items = [...newItems];
    this.filter();
  }

  requestMetadata() {
    const hash = window.location.hash;
    const searchParams = new URLSearchParams(window.location.search);
    fetch(".metadata.json")
      .then((response) => {
        if (!response.ok) throw new Error("Failed to fetch metadata");
        return response.json();
      })
      .then((data) => {
        this.items = Object.values(data.images || {});
        this.subfolders = data.subfolders || [];

        if (hash != "") {
          const selected = hash.replace("#", "").split(",");
          this.setFilter(selected);
        }
        if (searchParams.get("recursive") != null) {
          const recChk = document.getElementById("recursive");
          if (recChk) recChk.checked = true;
          this.recursive();
        } else {
          this.filter();
        }
      })
      .catch(() => {});
  }

  filter() {
    const searchParams = new URLSearchParams(window.location.search);
    this.shown = [];
    let path = decodeURIComponent(
      window.location.origin +
        window.location.pathname.replace("index.html", "")
    );
    if (path.startsWith("null")) {
      path = window.location.protocol + "//" + path.substring(4);
    }
    const selectedTags = [];

    document
      .querySelectorAll("#tagdropdown input.tagcheckbox:checked")
      .forEach((checkbox) => {
        let tag = checkbox.parentElement.id.trim().substring(1);
        if (checkbox.parentElement.parentElement.children.length > 1)
          tag += "|";
        selectedTags.push(tag);
      });

    const urltags = selectedTags.join(",");

    let isRecursiveChecked = false;
    try {
      isRecursiveChecked =
        document.getElementById("recursive")?.checked || false;
    } catch {}

    for (const item of this.items) {
      const tags = item.tags || [];
      const include = selectedTags.every((selected) => {
        const isParent = selected.endsWith("|");
        return isParent
          ? tags.some((t) => t.startsWith(selected))
          : tags.includes(selected);
      });

      if (include || selectedTags.length === 0) {
        if (!isRecursiveChecked) {
          if (decodeURIComponent(item.src.replace(item.name, "")) === path) {
            this.shown.push(item);
          }
        } else {
          this.shown.push(item);
        }
      }
    }
    this.updateImageList();
    window.location.hash = urltags;

    const pid = searchParams.get("pid") - 1;
    if (pid != -1) {
      this.openSwipe(pid);
    }
  }

  updateImageList() {
    const imagelist = document.getElementById("imagelist");
    if (!imagelist) return;
    let str = "";
    this.shown.forEach((item, index) => {
      str += `<div class="column"><figure><img src="${item.msrc}" data-index="${index}" /><figcaption class="caption">${item.name}`;
      if (item.tiff) str += ` <a href="${item.tiff}">TIFF</a>`;
      if (item.raw) str += ` <a href="${item.raw}">RAW</a>`;
      str += "</figcaption></figure></div>";
    });
    imagelist.innerHTML = str;
  }

  setFilter(selected) {
    document
      .querySelectorAll("#tagdropdown input.tagcheckbox")
      .forEach((checkbox) => {
        selected.forEach((tag) => {
          if (
            checkbox.parentElement.id
              .trim()
              .substring(1)
              .replace(" ", "%20") === tag
          ) {
            checkbox.checked = true;
          }
        });
      });
  }

  toggleTag(tagid) {
    const tag = document.getElementById(tagid);
    const ol = tag?.closest(".tagentry")?.querySelector(".tagentryparent");
    const svg = tag?.parentElement.querySelector(".tagtoggle svg");
    if (!ol || !svg) return;
    ol.classList.toggle("show");
    svg.style.transform = ol.classList.contains("show")
      ? "rotate(180deg)"
      : "rotate(0deg)";
  }

  setupDropdownToggle() {
    const toggleLink = document.getElementById("tagtogglelink");
    const dropdown = document.getElementById("tagdropdown");
    if (!toggleLink) return;

    toggleLink.addEventListener("click", (event) => {
      event.stopPropagation();
      const svg = toggleLink.querySelector("svg");
      dropdown.classList.toggle("show");
      if (svg)
        svg.style.transform = dropdown.classList.contains("show")
          ? "rotate(180deg)"
          : "rotate(0deg)";
      this.tagDropdownShown = dropdown.classList.contains("show");
    });

    document.addEventListener("click", (event) => {
      if (
        !dropdown.contains(event.target) &&
        !toggleLink.contains(event.target)
      ) {
        dropdown.classList.remove("show");
        this.tagDropdownShown = false;
        const svg = toggleLink.querySelector("svg");
        if (svg) svg.style.transform = "rotate(0deg)";
      }
    });
  }

  setupTagHandlers() {
    const tagContainer = document.getElementById("tagdropdown");
    if (!tagContainer) return;

    const debouncedFilter = this.debounce(this.filter, 150);
    tagContainer.addEventListener("change", debouncedFilter);

    tagContainer.addEventListener("click", (event) => {
      const toggle = event.target.closest(".tagtoggle");
      if (toggle) {
        event.stopPropagation();
        const tagid = toggle.dataset.toggleid;
        this.toggleTag(tagid);
      }
    });
  }

  setupClickHandlers() {
    const resetEl = document
      .getElementById("reset-filter")
      ?.querySelector("label");
    if (resetEl) resetEl.addEventListener("click", this.reset);

    const recurseEl = document.getElementById("recursive");
    if (recurseEl)
      recurseEl.addEventListener("change", this.debounce(this.recursive, 150));

    const totop = document.getElementById("totop");
    if (totop) totop.addEventListener("click", this.topFunction);

    const imagelist = document.getElementById("imagelist");
    if (imagelist) {
      imagelist.addEventListener("click", (event) => {
        const img = event.target.closest("img");
        if (!img || !img.dataset.index) return;
        const index = parseInt(img.dataset.index);
        if (!isNaN(index)) this.openSwipe(index);
      });

      imagelist.addEventListener("mouseover", (event) => {
        const img = event.target.closest("img");
        if (!img || !img.dataset.index) return;
        const index = parseInt(img.dataset.index);
        if (!isNaN(index)) this.prefetch(index);
      });

      imagelist.addEventListener("mouseleave", (event) => {
        const img = event.target.closest("img");
        if (!img || !img.dataset.index) return;
        const index = parseInt(img.dataset.index);
        if (!isNaN(index)) this.cancel(index);
      });
    }
  }

  scrollFunction() {
    const totopbutton = document.getElementById("totop");
    if (!totopbutton) return;
    if (
      document.body.scrollTop > 20 ||
      document.documentElement.scrollTop > 20
    ) {
      totopbutton.style.display = "block";
    } else {
      totopbutton.style.display = "none";
    }
  }

  topFunction() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  onLoad() {
    document.querySelectorAll(".tagtoggle").forEach((toggle) => {
      toggle.addEventListener("mouseup", (event) => {
        event.stopPropagation();
        const tagid = toggle.getAttribute("data-tagid");
        this.toggleTag(tagid);
      });
    });

    this.requestMetadata();
    this.setupDropdownToggle();
    this.setupTagHandlers();
    this.setupClickHandlers();

    window.addEventListener("scroll", this.scrollFunction);
  }

  init() {
    if (window.addEventListener) {
      window.addEventListener("load", this.onLoad, false);
    } else if (window.attachEvent) {
      window.attachEvent("onload", this.onLoad);
    }
  }
}
