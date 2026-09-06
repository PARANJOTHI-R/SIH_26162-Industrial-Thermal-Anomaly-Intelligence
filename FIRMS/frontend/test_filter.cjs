const fs = require('fs');
const investigations = JSON.parse(fs.readFileSync('temp_inv.json')).investigations;

const candidates = investigations.filter((item) => {
    if (item.is_investigation_candidate === true) return true;
    if (item.is_investigation_candidate === false) return false;
    // Fallback heuristic if backend field absent
    const behavior = String(item.behavior_state ?? "").toUpperCase();
    const sourceClass = String(item.source_class ?? "").toUpperCase();
    if (behavior === "NORMAL" || behavior === "INSUFFICIENT_HISTORY") return false;
    if (sourceClass === "AGRICULTURAL" || sourceClass === "FOREST_NATURAL") return false;
    return behavior === "WATCH" || behavior === "UNUSUAL";
});

console.log("Total investigations:", investigations.length);
console.log("Candidates:", candidates.length);
