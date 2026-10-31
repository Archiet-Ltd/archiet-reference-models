"""Build ArchiMate 3.1 models in the Open Group Exchange Format, with SVG previews.

Each model is described in Python (see models.py); this module turns that description into an
exchange-format file any conforming tool can import (Archi, Sparx, BiZZdesign, Etione) and an SVG
of every view for readers who want to see the model before they download it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from xml.sax.saxutils import escape

NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

# Layer of each element type, used for organisation folders and preview colours.
LAYER = {
    **{t: "Strategy" for t in ["Resource", "Capability", "ValueStream", "CourseOfAction"]},
    **{t: "Business" for t in ["BusinessActor", "BusinessRole", "BusinessCollaboration", "BusinessInterface",
                                "BusinessProcess", "BusinessFunction", "BusinessInteraction", "BusinessEvent",
                                "BusinessService", "BusinessObject", "Contract", "Representation", "Product"]},
    **{t: "Application" for t in ["ApplicationComponent", "ApplicationCollaboration", "ApplicationInterface",
                                   "ApplicationFunction", "ApplicationInteraction", "ApplicationProcess",
                                   "ApplicationEvent", "ApplicationService", "DataObject"]},
    **{t: "Technology" for t in ["Node", "Device", "SystemSoftware", "TechnologyCollaboration",
                                  "TechnologyInterface", "Path", "CommunicationNetwork", "TechnologyFunction",
                                  "TechnologyProcess", "TechnologyInteraction", "TechnologyEvent",
                                  "TechnologyService", "Artifact"]},
    **{t: "Motivation" for t in ["Stakeholder", "Driver", "Assessment", "Goal", "Outcome", "Principle",
                                  "Requirement", "Constraint", "Meaning", "Value"]},
    **{t: "Implementation & Migration" for t in ["WorkPackage", "Deliverable", "ImplementationEvent",
                                                  "Plateau", "Gap"]},
    **{t: "Other" for t in ["Grouping", "Location"]},
}

FILL = {
    "Strategy": "#F5DEAA", "Business": "#FFFFB5", "Application": "#B5FFFF", "Technology": "#C9E7B7",
    "Motivation": "#CCCCFF", "Implementation & Migration": "#FFE0E0", "Other": "#FFFFFF",
}

# Short type captions for the preview (the exchange file carries the real type).
CAPTION = {
    "BusinessActor": "actor", "BusinessEvent": "event", "BusinessRole": "role", "BusinessProcess": "process",
    "BusinessFunction": "function", "BusinessService": "service", "BusinessObject": "object",
    "ApplicationComponent": "component", "ApplicationService": "app service", "DataObject": "data",
    "Node": "node", "SystemSoftware": "system software", "TechnologyService": "tech service",
    "Artifact": "artifact", "Capability": "capability", "ValueStream": "value stream",
    "Stakeholder": "stakeholder", "Driver": "driver", "Goal": "goal", "Outcome": "outcome",
    "Requirement": "requirement", "Principle": "principle", "Constraint": "constraint",
    "Assessment": "assessment", "Grouping": "", "Contract": "contract", "Product": "product",
    "ApplicationEvent": "event", "ApplicationProcess": "process", "ApplicationInterface": "interface",
    "Location": "location", "Device": "device", "CommunicationNetwork": "network",
}


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass
class Element:
    id: str
    type: str
    name: str
    doc: str = ""
    props: dict[str, str] = field(default_factory=dict)


@dataclass
class Relationship:
    id: str
    type: str
    source: str
    target: str
    name: str = ""
    access: str = ""


@dataclass
class Node:
    element: str
    x: int
    y: int
    w: int
    h: int
    children: list["Node"] = field(default_factory=list)
    id: str = ""


@dataclass
class View:
    id: str
    name: str
    doc: str
    viewpoint: str = ""
    nodes: list[Node] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)  # relationship ids


class Model:
    def __init__(self, ident: str, name: str, doc: str):
        self.ident, self.name, self.doc = ident, name, doc
        self.elements: dict[str, Element] = {}
        self.relationships: list[Relationship] = []
        self.views: list[View] = []
        self.property_names: list[str] = []

    # --- content -------------------------------------------------------------------------------
    def el(self, type_: str, name: str, doc: str = "", **props: str) -> str:
        if type_ not in LAYER:
            raise ValueError(f"unknown element type {type_}")
        ident = f"id-{slug(type_)}-{slug(name)}"
        if ident in self.elements:
            raise ValueError(f"duplicate element {type_} {name}")
        for key in props:
            label = key.replace("_", " ").capitalize()
            if label not in self.property_names:
                self.property_names.append(label)
        self.elements[ident] = Element(ident, type_, name, doc,
                                       {k.replace("_", " ").capitalize(): v for k, v in props.items()})
        return ident

    def rel(self, type_: str, source: str, target: str, name: str = "", access: str = "") -> str:
        for end in (source, target):
            if end not in self.elements:
                raise ValueError(f"relationship end {end} is not an element")
        check_relationship(type_, self.elements[source].type, self.elements[target].type)
        ident = f"id-rel-{len(self.relationships) + 1:03d}"
        self.relationships.append(Relationship(ident, type_, source, target, name, access))
        return ident

    def view(self, name: str, doc: str, viewpoint: str = "") -> View:
        v = View(f"id-view-{slug(name)}", name, doc, viewpoint)
        self.views.append(v)
        return v

    # --- output --------------------------------------------------------------------------------
    def to_xml(self) -> str:
        out = ['<?xml version="1.0" encoding="UTF-8"?>',
               f'<model xmlns="{NS}" xmlns:xsi="{XSI}" identifier="id-{self.ident}" '
               f'xsi:schemaLocation="{NS} http://www.opengroup.org/xsd/archimate/3.1/archimate3_Diagram.xsd">',
               f'  <name xml:lang="en">{escape(self.name)}</name>',
               f'  <documentation xml:lang="en">{escape(self.doc)}</documentation>']
        prop_ids = {name: f"propid-{i + 1}" for i, name in enumerate(self.property_names)}
        out.append("  <elements>")
        for e in self.elements.values():
            out.append(f'    <element identifier="{e.id}" xsi:type="{e.type}">')
            out.append(f'      <name xml:lang="en">{escape(e.name)}</name>')
            if e.doc:
                out.append(f'      <documentation xml:lang="en">{escape(e.doc)}</documentation>')
            if e.props:
                out.append("      <properties>")
                for k, v in e.props.items():
                    out.append(f'        <property propertyDefinitionRef="{prop_ids[k]}">'
                               f'<value xml:lang="en">{escape(v)}</value></property>')
                out.append("      </properties>")
            out.append("    </element>")
        out.append("  </elements>")
        if self.relationships:
            out.append("  <relationships>")
            for r in self.relationships:
                extra = f' accessType="{r.access}"' if r.access else ""
                out.append(f'    <relationship identifier="{r.id}" source="{r.source}" target="{r.target}" '
                           f'xsi:type="{r.type}"{extra}>')
                if r.name:
                    out.append(f'      <name xml:lang="en">{escape(r.name)}</name>')
                out.append("    </relationship>")
            out.append("  </relationships>")
        out.append("  <organizations>")
        for layer in dict.fromkeys(LAYER.values()):
            members = [e.id for e in self.elements.values() if LAYER[e.type] == layer]
            if members:
                out.append(f'    <item><label xml:lang="en">{escape(layer)}</label>')
                out.extend(f'      <item identifierRef="{m}"/>' for m in members)
                out.append("    </item>")
        if self.relationships:
            out.append('    <item><label xml:lang="en">Relations</label>')
            out.extend(f'      <item identifierRef="{r.id}"/>' for r in self.relationships)
            out.append("    </item>")
        out.append('    <item><label xml:lang="en">Views</label>')
        out.extend(f'      <item identifierRef="{v.id}"/>' for v in self.views)
        out.append("    </item>")
        out.append("  </organizations>")
        if prop_ids:
            out.append("  <propertyDefinitions>")
            for name, pid in prop_ids.items():
                out.append(f'    <propertyDefinition identifier="{pid}" type="string">'
                           f'<name xml:lang="en">{escape(name)}</name></propertyDefinition>')
            out.append("  </propertyDefinitions>")
        out.append("  <views>")
        out.append("    <diagrams>")
        for v in self.views:
            vp = f' viewpoint="{v.viewpoint}"' if v.viewpoint else ""
            out.append(f'      <view identifier="{v.id}" xsi:type="Diagram"{vp}>')
            out.append(f'        <name xml:lang="en">{escape(v.name)}</name>')
            out.append(f'        <documentation xml:lang="en">{escape(v.doc)}</documentation>')
            node_of: dict[str, str] = {}
            counter = [0]

            def emit(node: Node, depth: int) -> None:
                counter[0] += 1
                node.id = f"{v.id}-n{counter[0]}"
                node_of.setdefault(node.element, node.id)
                pad = "  " * (depth + 4)
                fill = hex_rgb(FILL[LAYER[self.elements[node.element].type]])
                out.append(f'{pad}<node identifier="{node.id}" elementRef="{node.element}" xsi:type="Element" '
                           f'x="{node.x}" y="{node.y}" w="{node.w}" h="{node.h}">')
                out.append(f'{pad}  <style><fillColor r="{fill[0]}" g="{fill[1]}" b="{fill[2]}"/>'
                           f'<lineColor r="92" g="92" b="92"/></style>')
                for child in node.children:
                    emit(child, depth + 1)
                out.append(f"{pad}</node>")

            for n in v.nodes:
                emit(n, 0)
            rel_by_id = {r.id: r for r in self.relationships}
            for i, rid in enumerate(v.connections, 1):
                r = rel_by_id[rid]
                if r.source not in node_of or r.target not in node_of:
                    raise ValueError(f"view {v.name}: connection {rid} has an end not on the view")
                out.append(f'        <connection identifier="{v.id}-c{i}" relationshipRef="{rid}" '
                           f'xsi:type="Relationship" source="{node_of[r.source]}" target="{node_of[r.target]}"/>')
            out.append("      </view>")
        out.append("    </diagrams>")
        out.append("  </views>")
        out.append("</model>")
        return "\n".join(out) + "\n"

    def to_svg(self, v: View) -> str:
        boxes: dict[str, tuple[int, int, int, int]] = {}
        rects: list[str] = []

        def walk(node: Node) -> None:
            e = self.elements[node.element]
            boxes.setdefault(node.element, (node.x, node.y, node.w, node.h))
            grouping = e.type == "Grouping"
            fill = "none" if grouping else FILL[LAYER[e.type]]
            dash = ' stroke-dasharray="6 4"' if grouping else ""
            rects.append(f'<rect x="{node.x}" y="{node.y}" width="{node.w}" height="{node.h}" rx="4" '
                         f'fill="{fill}" stroke="#5c5c5c"{dash}/>')
            caption = CAPTION.get(e.type, e.type)
            top = bool(node.children) or grouping
            lines = wrap(e.name, max(8, (node.w - 16) // 7))
            # Centre the label in the space above the type caption, which sits in the bottom 12px.
            label_y = node.y + 18 if top else node.y + (node.h - 10) / 2 - (len(lines) - 1) * 7.5 + 4
            for i, line in enumerate(lines):
                rects.append(f'<text x="{node.x + node.w / 2}" y="{label_y + i * 15}" text-anchor="middle" '
                             f'font-weight="{600 if top else 400}">{escape(line)}</text>')
            if caption:
                rects.append(f'<text x="{node.x + node.w - 5}" y="{node.y + node.h - 5}" text-anchor="end" '
                             f'class="cap">{escape(caption)}</text>')
            for child in node.children:
                walk(child)

        for n in v.nodes:
            walk(n)
        lines = []
        rel_by_id = {r.id: r for r in self.relationships}
        for rid in v.connections:
            r = rel_by_id[rid]
            (sx, sy), (tx, ty) = edge_points(boxes[r.source], boxes[r.target])
            if r.type == "Access" and r.access == "Read":
                (sx, sy), (tx, ty) = (tx, ty), (sx, sy)  # a read points from the data to the reader
            style = {"Serving": "", "Realization": ' stroke-dasharray="5 3"', "Influence": ' stroke-dasharray="2 3"',
                     "Access": ' stroke-dasharray="1 3"', "Triggering": "", "Flow": ' stroke-dasharray="6 3"'}
            marker = {"Serving": "open", "Realization": "hollow", "Triggering": "solid", "Flow": "solid",
                      "Access": "open", "Influence": "open"}.get(r.type, "")
            end = f' marker-end="url(#{marker})"' if marker else ""
            lines.append(f'<line x1="{sx:.0f}" y1="{sy:.0f}" x2="{tx:.0f}" y2="{ty:.0f}" stroke="#444"'
                         f'{style.get(r.type, "")}{end}/>')
        width = max(x + w for x, y, w, h in boxes.values()) + 20
        height = max(y + h for x, y, w, h in boxes.values()) + 20
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
                f'viewBox="0 0 {width} {height}" font-family="Segoe UI, Helvetica, Arial, sans-serif" font-size="12">'
                '<style>.cap{font-size:9px;fill:#555}</style>'
                '<defs>'
                '<marker id="open" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
                '<path d="M0,0 L9,5 L0,10" fill="none" stroke="#444"/></marker>'
                '<marker id="hollow" markerWidth="12" markerHeight="12" refX="11" refY="6" orient="auto">'
                '<path d="M0,0 L11,6 L0,12 z" fill="#fff" stroke="#444"/></marker>'
                '<marker id="solid" markerWidth="10" markerHeight="10" refX="9" refY="5" orient="auto">'
                '<path d="M0,0 L9,5 L0,10 z" fill="#444"/></marker>'
                '</defs>'
                f'<rect width="{width}" height="{height}" fill="#ffffff"/>'
                + "".join(rects) + "".join(lines) + "</svg>\n")


def hex_rgb(color: str) -> tuple[int, int, int]:
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


def wrap(text: str, width: int) -> list[str]:
    words, lines, line = text.split(), [], ""
    for word in words:
        if line and len(line) + 1 + len(word) > width:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + ([line] if line else [])


def edge_points(a, b):
    """Points where the straight line between two box centres leaves each box."""
    def centre(r):
        return r[0] + r[2] / 2, r[1] + r[3] / 2

    def clip(r, towards):
        cx, cy = centre(r)
        dx, dy = towards[0] - cx, towards[1] - cy
        if dx == 0 and dy == 0:
            return cx, cy
        scale = min(r[2] / 2 / abs(dx) if dx else float("inf"), r[3] / 2 / abs(dy) if dy else float("inf"))
        return cx + dx * scale, cy + dy * scale

    return clip(a, centre(b)), clip(b, centre(a))


# The ArchiMate 3.1 relationships these models use, by (relationship, source type, target type).
# Checked on every rel() call so a model can never ship a relationship the specification forbids.
_STRUCT = {"BusinessActor", "BusinessRole", "ApplicationComponent", "Node", "SystemSoftware", "Device"}
_BEHAVIOUR = {"BusinessProcess", "BusinessFunction", "BusinessService", "ApplicationService",
              "ApplicationFunction", "ApplicationProcess", "TechnologyService", "TechnologyFunction"}
_PASSIVE = {"BusinessObject", "DataObject", "Artifact", "Contract"}
_CORE = _STRUCT | _BEHAVIOUR | _PASSIVE
ALLOWED = {
    ("Composition", "Capability", "Capability"), ("Composition", "ValueStream", "ValueStream"),
    ("Serving", "Capability", "ValueStream"), ("Serving", "Capability", "Capability"),
    ("Triggering", "ValueStream", "ValueStream"), ("Flow", "ValueStream", "ValueStream"),
    ("Assignment", "BusinessActor", "BusinessRole"), ("Assignment", "BusinessRole", "BusinessProcess"),
    ("Assignment", "BusinessRole", "BusinessFunction"), ("Assignment", "ApplicationComponent", "ApplicationFunction"),
    ("Realization", "BusinessProcess", "BusinessService"), ("Realization", "ApplicationComponent", "ApplicationService"),
    ("Realization", "ApplicationFunction", "ApplicationService"), ("Realization", "Node", "TechnologyService"),
    ("Realization", "SystemSoftware", "TechnologyService"), ("Realization", "Artifact", "ApplicationComponent"),
    ("Realization", "DataObject", "BusinessObject"),
    ("Serving", "BusinessService", "BusinessActor"), ("Serving", "BusinessService", "BusinessRole"),
    ("Serving", "ApplicationService", "BusinessProcess"), ("Serving", "ApplicationService", "BusinessFunction"),
    ("Serving", "ApplicationComponent", "ApplicationComponent"), ("Serving", "TechnologyService", "ApplicationComponent"),
    ("Serving", "BusinessActor", "BusinessFunction"), ("Serving", "BusinessActor", "BusinessActor"),
    ("Serving", "ApplicationComponent", "BusinessFunction"), ("Serving", "ApplicationComponent", "BusinessProcess"),
    ("Serving", "TechnologyService", "BusinessFunction"),
    ("Triggering", "BusinessProcess", "BusinessProcess"), ("Triggering", "BusinessEvent", "BusinessProcess"),
    ("Access", "BusinessProcess", "BusinessObject"), ("Access", "ApplicationComponent", "DataObject"),
    ("Access", "ApplicationFunction", "DataObject"), ("Access", "ApplicationService", "DataObject"),
    ("Composition", "Node", "SystemSoftware"), ("Assignment", "Node", "Artifact"),
    ("Assignment", "SystemSoftware", "Artifact"),
    ("Influence", "Driver", "Goal"), ("Influence", "Assessment", "Goal"), ("Association", "Stakeholder", "Driver"),
    ("Association", "Driver", "Assessment"), ("Realization", "Requirement", "Goal"),
    ("Realization", "Requirement", "Outcome"), ("Realization", "Outcome", "Goal"),
    ("Composition", "Requirement", "Requirement"), ("Aggregation", "Requirement", "Requirement"),
    ("Association", "BusinessActor", "Contract"), ("Association", "Contract", "ApplicationComponent"),
    ("Association", "Contract", "TechnologyService"),
    ("Assignment", "BusinessActor", "BusinessProcess"),
    ("Serving", "ApplicationComponent", "BusinessActor"), ("Serving", "ApplicationComponent", "BusinessRole"),
    ("Serving", "ApplicationInterface", "BusinessActor"), ("Serving", "Node", "ApplicationComponent"),
    ("Serving", "Node", "Node"), ("Serving", "TechnologyService", "Node"),
    ("Serving", "ApplicationService", "ApplicationComponent"), ("Serving", "Device", "BusinessActor"),
    ("Serving", "TechnologyService", "BusinessActor"),
    ("Composition", "ApplicationComponent", "ApplicationInterface"),
    ("Composition", "ApplicationComponent", "ApplicationComponent"),
    ("Assignment", "ApplicationComponent", "ApplicationProcess"),
    ("Triggering", "ApplicationProcess", "ApplicationEvent"), ("Triggering", "ApplicationEvent", "ApplicationProcess"),
    ("Access", "ApplicationProcess", "DataObject"), ("Access", "ApplicationEvent", "DataObject"),
    ("Realization", "Artifact", "DataObject"), ("Realization", "Device", "TechnologyService"),
    ("Access", "TechnologyService", "Artifact"), ("Access", "Node", "Artifact"),
}


def check_relationship(rel: str, source: str, target: str) -> None:
    if (rel, source, target) in ALLOWED:
        return
    if rel == "Association":
        return  # ArchiMate permits an association between any two elements
    if rel in ("Flow", "Triggering") and source in _STRUCT | _BEHAVIOUR and target in _STRUCT | _BEHAVIOUR and LAYER[source] == LAYER[target]:
        return  # dynamic relationships between active structure or behaviour in one layer
    if rel == "Aggregation" and source == "Location":
        return  # a location may aggregate anything placed there
    if rel == "Aggregation" and source == "Grouping":
        return  # a grouping may aggregate any concept
    if rel == "Realization" and source in _CORE and target in {"Requirement", "Capability", "Principle", "Constraint"}:
        return  # core elements realize requirements and capabilities
    if rel == "Realization" and source == "Resource" and target == "Capability":
        return
    raise ValueError(f"{rel} from {source} to {target} is not in the allowed set")
