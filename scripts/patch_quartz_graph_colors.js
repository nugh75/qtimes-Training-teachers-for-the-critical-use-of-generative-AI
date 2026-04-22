"use strict";

const fs = require("fs");
const path = require("path");

const target = path.join(
  process.cwd(),
  "quartz",
  "components",
  "scripts",
  "graph.inline.ts",
);

let text = fs.readFileSync(target, "utf8");

const replacement = `  // classify slugs so Quartz Graph View can use cohort-aware colors
  const GROUP_COLORS = {
    studenti: "#2563EB",
    insegnantiAttuali: "#0F766E",
    insegnantiFuturi: "#B45309",
    corpusStudenti: "#60A5FA",
    corpusInsegnantiAttuali: "#34D399",
    corpusInsegnantiFuturi: "#F59E0B",
    wikiMeta: "#7C3AED",
    other: computedStyleMap["--gray"],
    tag: computedStyleMap["--tertiary"],
  }

  function groupForNodeId(id: string): keyof typeof GROUP_COLORS {
    const slugId = id.toLowerCase()
    if (slugId.startsWith("tags/")) return "tag"

    if (slugId.startsWith("01-wiki/studenti/studenti")) return "studenti"
    if (slugId.startsWith("01-wiki/insegnanti-attuali")) return "insegnantiAttuali"
    if (slugId.startsWith("01-wiki/insegnanti-futuri")) return "insegnantiFuturi"
    if (slugId.startsWith("01-wiki/")) return "wikiMeta"

    if (slugId.startsWith("02-corpus/studenti_")) return "corpusStudenti"
    if (slugId.startsWith("02-corpus/insegnanti_attuali_")) return "corpusInsegnantiAttuali"
    if (slugId.startsWith("02-corpus/insegnanti_futuri_")) return "corpusInsegnantiFuturi"

    return "other"
  }

  // calculate color
  const color = (d: NodeData) => {
    const isCurrent = d.id === slug
    if (isCurrent) {
      return computedStyleMap["--secondary"]
    }

    const group = groupForNodeId(d.id)
    return GROUP_COLORS[group] ?? GROUP_COLORS.other
  }

  function nodeRadius(d: NodeData) {`;

const pattern =
  /  \/\/ calculate color[\s\S]*?  function nodeRadius\(d: NodeData\) \{/m;

if (!pattern.test(text)) {
  throw new Error("Could not find color block in graph.inline.ts");
}

text = text.replace(pattern, replacement);
fs.writeFileSync(target, text);
console.log("Patched Quartz Graph View colors in graph.inline.ts");
