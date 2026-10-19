/* Pure repository URL mapping shared by the browser and node:test. */
(function (root) {
  "use strict";
  const decode = (value) => { try { return decodeURIComponent(value); } catch { return value; } };
  function parseRoute(hash) {
    const [page, ...fragment] = hash.replace(/^#\/?/, "").split("#");
    return { id: decode(page) || "home", fragment: decode(fragment.join("#")) };
  }
  const normalizeHeading = (value) => value.replace(/-+/g, "-");
  function resolveLink(href, currentId, docs, repo) {
    href = href.trim();
    if (/^(https?:|mailto:|tel:)/i.test(href) || href.startsWith("//")) return href;
    if (/^[a-z][a-z\d+.-]*:/i.test(href)) return null;
    if (href.startsWith("#/")) return href;
    const [beforeHash, ...parts] = href.split("#");
    const fragment = parts.length ? "#" + parts.join("#") : "";
    if (!beforeHash) return "#/" + currentId + fragment;
    const source = docs[currentId]?.source || "README.md";
    const isDirectory = !source.split("/").at(-1).includes(".");
    const base = isDirectory ? source + "/" : source.slice(0, source.lastIndexOf("/") + 1);
    const raw = decode(beforeHash.split("?")[0]);
    const segments = [];
    for (const part of (raw.startsWith("/") ? raw.slice(1) : base + raw).split("/")) {
      if (part === "..") segments.pop();
      else if (part && part !== ".") segments.push(part);
    }
    const path = segments.join("/");
    const canonical = (value) => value.replace(/\/?README\.md$/i, "").replace(/\/$/, "");
    if (!canonical(path)) return "#/home" + fragment;
    for (const [id, doc] of Object.entries(docs)) {
      if (doc.source && canonical(doc.source) === canonical(path)) return "#/" + id + fragment;
    }
    const directory = raw.endsWith("/") || !segments.at(-1)?.includes(".");
    return repo + (directory ? "/tree/main/" : "/blob/main/") +
      segments.map(encodeURIComponent).join("/") + fragment;
  }
  const api = { parseRoute, resolveLink, normalizeHeading };
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  else root.RepoLinks = api;
})(globalThis);
