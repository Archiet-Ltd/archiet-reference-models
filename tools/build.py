"""Regenerate every model's exchange file and view previews, and validate them against the schema."""

import csv
from pathlib import Path

from lxml import etree

from models import ALL, application_rows, capability_rows
from oef import slug
from patterns import PATTERNS

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = etree.XMLSchema(etree.parse(str(Path(__file__).parent / "xsd" / "archimate3_Diagram.xsd")))


def pattern_readme(model) -> str:
    g = model.guide
    views = "\n".join(f"![{v.name}]({slug(v.name)}.svg)\n" for v in model.views)
    use = "\n".join(f"- {x}" for x in g["use"])
    trade = "\n".join(f"- {x}" for x in g["tradeoffs"])
    return (f"# {model.name}\n\n{model.doc}\n\n{views}\n"
            f"## Use it when\n\n{use}\n\n"
            f"## Trade-offs\n\n{trade}\n\n"
            f"## Files\n\n"
            f"- `{model.ident}.xml`: the model in ArchiMate Open Exchange format, for Archi, Sparx, "
            f"BiZZdesign and Entelim.\n"
            f"- `*.svg`: the diagrams above.\n\n"
            f"## Build it\n\n{g['ifiok']} [Start free with Ifiok](https://ifiok.archiet.ai).\n")


for build, area in [(b, "models") for b in ALL] + [(b, "patterns") for b in PATTERNS]:
    model = build()
    folder = ROOT / area / model.ident
    folder.mkdir(parents=True, exist_ok=True)
    xml_path = folder / f"{model.ident}.xml"
    xml_path.write_text(model.to_xml(), encoding="utf-8")
    SCHEMA.assertValid(etree.parse(str(xml_path)))
    for view in model.views:
        (folder / f"{slug(view.name)}.svg").write_text(model.to_svg(view), encoding="utf-8")
    if area == "patterns":
        (folder / "README.md").write_text(pattern_readme(model), encoding="utf-8")
    print(f"{model.ident}: {len(model.elements)} elements, {len(model.relationships)} relationships, "
          f"{len(model.views)} views, schema valid")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


write_csv(ROOT / "models" / "capability-map" / "capability-map.csv", capability_rows())
write_csv(ROOT / "models" / "application-portfolio" / "application-portfolio.csv", application_rows())
print("spreadsheet editions written")
