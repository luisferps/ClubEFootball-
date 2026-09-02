#!/usr/bin/env node

import { createHash } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";
import { assertCardId, loadInput, uniqueCardIds } from "./card-image-extractor.mjs";

function parseArgs(argv) {
  const args = { registeredIds: [], registeredManifests: [], output: null, universe: null };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    const next = () => {
      const value = argv[++i];
      if (value == null) throw new Error(`valor ausente para ${token}`);
      return value;
    };
    if (token === "--universe") args.universe = next();
    else if (token === "--registered-manifest") args.registeredManifests.push(next());
    else if (token === "--registered-id") args.registeredIds.push(next());
    else if (token === "--output") args.output = next();
    else throw new Error(`argumento desconhecido: ${token}`);
  }
  if (!args.universe || !args.output || !args.registeredManifests.length) {
    throw new Error("informe --universe, --output e ao menos um --registered-manifest");
  }
  return args;
}

async function sha256(path) {
  const bytes = await readFile(resolve(path));
  return createHash("sha256").update(bytes).digest("hex");
}

export async function buildInventory(argv = process.argv.slice(2)) {
  const args = parseArgs(argv);
  const universe = uniqueCardIds(await loadInput(args.universe));
  const registeredParts = [];
  for (const manifest of args.registeredManifests) registeredParts.push(...await loadInput(manifest));
  registeredParts.push(...args.registeredIds.map(assertCardId));
  const registered = uniqueCardIds(registeredParts);
  const universeSet = new Set(universe);
  const registeredSet = new Set(registered);
  const registeredInUniverse = universe.filter((id) => registeredSet.has(id));
  const missing = universe.filter((id) => !registeredSet.has(id));
  const registeredOutsideUniverse = registered.filter((id) => !universeSet.has(id));
  const output = resolve(args.output);
  await mkdir(output, { recursive: true });
  await writeFile(resolve(output, "registered-in-universe.txt"), `${registeredInUniverse.join("\n")}\n`, "utf8");
  await writeFile(resolve(output, "missing.txt"), `${missing.join("\n")}\n`, "utf8");
  await writeFile(resolve(output, "registered-outside-universe.txt"), `${registeredOutsideUniverse.join("\n")}\n`, "utf8");
  const summary = {
    format: "clubefutebol-card-image-inventory-v1",
    generated_at_utc: new Date().toISOString(),
    matching_key: "card_id",
    universe: { path: resolve(args.universe), sha256: await sha256(args.universe), unique: universe.length },
    registered_manifests: await Promise.all(args.registeredManifests.map(async (path) => ({ path: resolve(path), sha256: await sha256(path) }))),
    registered_unique: registered.length,
    registered_in_universe: registeredInUniverse.length,
    registered_outside_universe: registeredOutsideUniverse.length,
    missing: missing.length,
    partition_exact: registeredInUniverse.length + missing.length === universe.length,
    overlap_missing_registered: missing.filter((id) => registeredSet.has(id)).length,
    files: {
      registered_in_universe: resolve(output, "registered-in-universe.txt"),
      missing: resolve(output, "missing.txt"),
      registered_outside_universe: resolve(output, "registered-outside-universe.txt")
    }
  };
  await writeFile(resolve(output, "summary.json"), `${JSON.stringify(summary, null, 2)}\n`, "utf8");
  console.log(JSON.stringify(summary));
  return summary;
}

if (import.meta.url === pathToFileURL(process.argv[1]).href) {
  buildInventory().catch((error) => {
    console.error(error.stack || error.message);
    process.exitCode = 1;
  });
}

