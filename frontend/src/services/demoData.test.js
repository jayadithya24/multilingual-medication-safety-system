import assert from "node:assert/strict";
import { after, test } from "node:test";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { handleDemoRequest } from "./demoData.js";
import { staticDemoAdapter } from "./demoApi.js";

const frontendRoot = fileURLToPath(new URL("../../", import.meta.url));
const originalFetch = globalThis.fetch;
const fetchedPaths = [];

globalThis.fetch = async (input) => {
  const pathname = new URL(String(input), "http://demo.local").pathname;
  fetchedPaths.push(pathname);
  const assetPath = path.join(frontendRoot, "public", pathname.replace(/^\/+/, ""));
  try {
    return new Response(await readFile(assetPath), { status: 200 });
  } catch {
    return new Response("Not found", { status: 404 });
  }
};

after(() => {
  globalThis.fetch = originalFetch;
});

test("the bundled catalog exposes the complete 100-medicine, 10-disease scope", async () => {
  const response = await handleDemoRequest({ url: "/neo4j/diseases", method: "get" });
  assert.equal(response.medicine_count, 100);
  assert.equal(response.disease_count, 10);
  assert.equal(response.diseases.length, 10);
});

test("multilingual medicine search uses the bundled Kannada and Tulu descriptions", async () => {
  const kannada = await handleDemoRequest({
    url: "/neo4j/search",
    method: "get",
    params: { term: "metformin", lang: "kn" },
  });
  const tulu = await handleDemoRequest({
    url: "/neo4j/search",
    method: "get",
    params: { term: "metformin", lang: "tulu" },
  });
  assert.ok(kannada.results[0].description.includes("ಮೆಟ್‌ಫಾರ್ಮಿನ್"));
  assert.ok(tulu.results[0].description.includes("ಮರ್ದ್"));
});

test("the medication graph is assembled locally from the CSV assets", async () => {
  const response = await handleDemoRequest({ url: "/neo4j/graph", method: "get" });
  assert.equal(response.source, "static_csv");
  assert.equal(response.nodes.filter((node) => node.type === "drug").length, 100);
  assert.ok(response.links.some((link) => link.relationship === "TREATS"));
  assert.ok(response.links.some((link) => link.relationship === "CAUSES"));
});

test("interaction lookup preserves conflicting dataset ratings for clinician review", async () => {
  const response = await handleDemoRequest({
    url: "/interaction",
    method: "get",
    params: { drug1: "Ibuprofen", drug2: "Methotrexate" },
  });
  assert.equal(response.status, "success");
  assert.equal(response.interaction.severity, "Review required");
  assert.deepEqual(response.interaction.source_severities, ["Moderate", "Severe"]);
  assert.equal(response.interaction.severity_clinically_validated, false);
});

test("the Vercel demo API adapter serves the static route without a backend", async () => {
  const response = await staticDemoAdapter({
    url: "/neo4j/diseases",
    method: "get",
    params: { lang: "en" },
  });
  assert.equal(response.status, 200);
  assert.equal(response.data.medicine_count, 100);
  assert.ok(fetchedPaths.every((pathname) => pathname.startsWith("/demo-data/")));
});

test("mutating endpoints explicitly reject changes in the read-only demo", async () => {
  await assert.rejects(
    staticDemoAdapter({
      url: "/patient-schedule",
      method: "post",
      data: { medicine_name: "Metformin" },
    }),
    (error) => error.response?.status === 405
      && error.response.data.detail.includes("read-only"),
  );
});
