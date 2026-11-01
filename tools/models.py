"""The reference models. Run build.py to regenerate the exchange files and previews."""

from __future__ import annotations

from oef import Model, Node, wrap

W, H = 160, 55  # default element size on a view
GAP = 15


def grid(elements: list[str], x: int, y: int, cols: int, w: int = W, h: int = H, gap: int = GAP) -> list[Node]:
    return [Node(e, x + (i % cols) * (w + gap), y + (i // cols) * (h + gap), w, h) for i, e in enumerate(elements)]


def on_view_of(view) -> set[str]:
    """Every element shown on a view, nested boxes included."""
    seen, stack = set(), list(view.nodes)
    while stack:
        node = stack.pop()
        seen.add(node.element)
        stack.extend(node.children)
    return seen


def shift(node: Node, dx: int, dy: int) -> None:
    node.x += dx
    node.y += dy
    for child in node.children:
        shift(child, dx, dy)


def container(element: str, x: int, y: int, children: list[str], cols: int, w: int = W, h: int = H,
              min_w: int = 0, title: str = "") -> Node:
    """A box holding a grid of child boxes, sized to fit them and its own title."""
    rows = (len(children) + cols - 1) // cols
    width = max(min_w, cols * (w + GAP) + GAP)
    header = 17 + 15 * len(wrap(title, max(8, (width - 16) // 7))) if title else 32
    inner = grid(children, x + GAP, y + header, cols, w, h)
    return Node(element, x, y, width, header + rows * (h + GAP) + 5, inner)


# ------------------------------------------------------------------------------------------------
# 1. Business capability map
# ------------------------------------------------------------------------------------------------

CAPABILITIES = {
    "Strategy and Governance": ["Strategic Planning", "Portfolio and Investment Management",
                                "Enterprise Architecture", "Performance Management"],
    "Customer Management": ["Marketing", "Sales", "Customer Onboarding", "Customer Service",
                            "Customer Insight"],
    "Product and Service Delivery": ["Product Management", "Service Design", "Order Management",
                                     "Fulfilment", "Billing"],
    "Operations": ["Procurement", "Supplier Management", "Asset Management", "Facilities Management"],
    "Finance": ["Financial Planning", "Accounting", "Treasury", "Financial Reporting"],
    "People": ["Workforce Planning", "Recruitment", "Learning and Development", "Payroll"],
    "Risk and Compliance": ["Risk Management", "Regulatory Compliance", "Information Security",
                            "Business Continuity", "Audit"],
    "Technology and Data": ["Data Management", "Application Management", "Infrastructure Management",
                            "Integration Management"],
}


def capability_map() -> Model:
    m = Model("capability-map", "Business Capability Map (starter)",
              "A two-level business capability map for a mid-sized organisation, independent of industry. "
              "Capabilities describe what the business does, never how or by whom, so the map stays stable "
              "while processes, teams and systems change underneath it. Rename, merge and extend the second "
              "level to match your organisation; keep the first level to roughly eight areas so it fits on "
              "one page for executives. Each capability carries two properties for a heat map: strategic "
              "importance and current maturity.")
    level1: dict[str, str] = {}
    level2: dict[str, list[str]] = {}
    for area, subs in CAPABILITIES.items():
        level1[area] = m.el("Capability", area, f"Level 1 capability area: {area}.")
        level2[area] = []
        for sub in subs:
            c = m.el("Capability", sub, "", strategic_importance="Not assessed", maturity_1_to_5="Not assessed")
            m.rel("Composition", level1[area], c)
            level2[area].append(c)

    v = m.view("Capability map", "Level 1 areas with their level 2 capabilities. Colour each capability "
               "by strategic importance or maturity to turn this into a heat map.", "Capability Map")
    x, y, col_h = 20, 20, 0
    for i, area in enumerate(CAPABILITIES):
        box = container(level1[area], x, y, level2[area], cols=1, w=170, h=45)
        v.nodes.append(box)
        col_h = max(col_h, box.h)
        x += box.w + GAP
        if i == 3:
            x, y, col_h = 20, y + col_h + GAP, 0

    # A value stream the capabilities serve: the usual way to show why a capability matters.
    stages = ["Attract Customer", "Win Order", "Onboard Customer", "Deliver Service", "Bill and Collect",
              "Retain Customer"]
    stream = m.el("ValueStream", "Acquire to Retain", "End-to-end value stream from first contact to repeat "
                  "business. Each stage is served by the capabilities it depends on.")
    stage_ids = []
    for s in stages:
        sid = m.el("ValueStream", s)
        m.rel("Composition", stream, sid)
        stage_ids.append(sid)
    for a, b in zip(stage_ids, stage_ids[1:]):
        m.rel("Flow", a, b)
    cap = {name: cid for area in level2.values() for cid in area
           for name in [m.elements[cid].name]}
    serves = {
        "Attract Customer": ["Marketing"],
        "Win Order": ["Sales", "Product Management"],
        "Onboard Customer": ["Customer Onboarding", "Regulatory Compliance"],
        "Deliver Service": ["Order Management", "Fulfilment", "Service Design"],
        "Bill and Collect": ["Billing", "Accounting"],
        "Retain Customer": ["Customer Service", "Customer Insight"],
    }
    vs = m.view("Value stream and supporting capabilities", "Which capabilities each stage of Acquire to "
                "Retain depends on. A low-maturity capability beside a critical stage is where investment "
                "pays back first.", "Value Stream")
    # One row per stage, its capabilities to the right, so no line crosses another box.
    y = 20
    for i, (stage, caps) in enumerate(serves.items()):
        height = len(caps) * 60 - 10
        vs.nodes.append(Node(stage_ids[i], 20, y, 190, max(50, height)))
        for j, cname in enumerate(caps):
            vs.nodes.append(Node(cap[cname], 300, y + j * 60, 200, 50))
            vs.connections.append(m.rel("Serving", cap[cname], stage_ids[i]))
        y += max(50, height) + 30
    vs.connections.extend(r.id for r in m.relationships if r.type == "Flow")
    return m


# ------------------------------------------------------------------------------------------------
# 2. Application portfolio rationalisation (TIME)
# ------------------------------------------------------------------------------------------------

def application_portfolio() -> Model:
    m = Model("application-portfolio", "Application Portfolio Rationalisation (starter)",
              "An application portfolio mapped to the business capabilities each application supports, "
              "scored with Gartner's TIME model: Tolerate, Invest, Migrate, Eliminate. Two applications "
              "realizing the same capability is the redundancy signal; an application nobody can map to a "
              "capability is the elimination signal. Replace the example applications with your own "
              "inventory and keep the properties filled in: they are what makes the portfolio decidable.")
    caps = {n: m.el("Capability", n) for n in [
        "Customer Relationship Management", "Sales", "Customer Service", "Financial Reporting",
        "Accounting", "Payroll", "Recruitment", "Data Management", "Document Management",
        "Integration Management"]}
    apps = [
        # name, capabilities, TIME, lifecycle, note
        ("CRM Platform", ["Customer Relationship Management", "Sales"], "Invest", "Active",
         "Strategic system of record for customers."),
        ("Legacy CRM", ["Customer Relationship Management"], "Migrate", "Phasing out",
         "Duplicates the CRM Platform; remaining users and data move there."),
        ("Service Desk", ["Customer Service"], "Tolerate", "Active",
         "Fit for purpose; no investment beyond upkeep."),
        ("ERP Finance", ["Accounting", "Financial Reporting"], "Invest", "Active",
         "Core finance platform."),
        ("Forecasting Spreadsheets", ["Financial Reporting"], "Eliminate", "Unmanaged",
         "End-user computing with no owner or controls; replace with ERP reporting."),
        ("HR Suite", ["Recruitment", "Payroll"], "Invest", "Active", "Single HR platform."),
        ("Payroll Bureau Portal", ["Payroll"], "Migrate", "Contract ending",
         "Payroll moves into the HR Suite when the bureau contract ends."),
        ("Data Warehouse", ["Data Management", "Financial Reporting"], "Tolerate", "Active",
         "Stable; review when the analytics platform decision is made."),
        ("File Shares", ["Document Management"], "Eliminate", "Unmanaged",
         "Uncontrolled document storage; content moves to the document platform."),
        ("Document Platform", ["Document Management"], "Invest", "Active", "Target document store."),
        ("Integration Platform", ["Integration Management"], "Invest", "Active",
         "All new interfaces go through the platform; point-to-point links are retired over time."),
        ("Departmental Ticket Tracker", [], "Eliminate", "Unmanaged",
         "Supports no business capability on the map; candidate for switch-off."),
    ]
    app_ids = {}
    for name, served, time, lifecycle, note in apps:
        a = m.el("ApplicationComponent", name, note, time=time, lifecycle=lifecycle, business_owner="",
                 annual_run_cost="")
        app_ids[name] = a
        for c in served:
            m.rel("Realization", a, caps[c])
    m.rel("Serving", app_ids["Integration Platform"], app_ids["CRM Platform"])
    m.rel("Serving", app_ids["Integration Platform"], app_ids["ERP Finance"])
    m.rel("Serving", app_ids["Integration Platform"], app_ids["HR Suite"])

    v = m.view("Applications by capability", "Each capability holds the applications that realize it. "
               "A capability holding two or more applications is overlap worth a decision; an application "
               "outside every capability supports nothing on the map.")
    orphan = m.el("Grouping", "Supports no mapped capability", "Applications that realize none of the "
                  "capabilities on the map.")
    for name, served, *_ in apps:
        if not served:
            m.rel("Aggregation", orphan, app_ids[name])
    boxes = []
    for cname in caps:
        members = [app_ids[n] for n, served, *_ in apps if cname in served]
        boxes.append(container(caps[cname], 0, 0, members, cols=1, w=200, h=45, title=cname))
    boxes.append(container(orphan, 0, 0, [app_ids[n] for n, served, *_ in apps if not served], cols=1,
                           w=200, h=45, title="Supports no mapped capability"))
    x, y, row_h = 20, 20, 0
    for i, box in enumerate(boxes):
        if i and i % 6 == 0:
            x, y, row_h = 20, y + row_h + GAP, 0
        shift(box, x - box.x, y - box.y)
        v.nodes.append(box)
        row_h = max(row_h, box.h)
        x += box.w + GAP

    groups = {}
    for t, doc in [("Invest", "Strategic and fit for purpose: fund and extend."),
                   ("Tolerate", "Adequate today: keep running, spend only on upkeep."),
                   ("Migrate", "The capability matters but this application does not: move to a target."),
                   ("Eliminate", "No longer needed: plan switch-off and data retention.")]:
        groups[t] = m.el("Grouping", t, doc)
    for name, _, time, *_ in apps:
        m.rel("Aggregation", groups[time], app_ids[name])
    tv = m.view("TIME quadrants", "The portfolio sorted into Tolerate, Invest, Migrate and Eliminate. "
                "Agree the quadrant with each business owner; the Migrate and Eliminate quadrants become "
                "the roadmap.")
    for i, t in enumerate(["Tolerate", "Invest", "Migrate", "Eliminate"]):
        members = [app_ids[n] for n, _, time, *_ in apps if time == t]
        tv.nodes.append(container(groups[t], 20 + (i % 2) * 410, 20 + (i // 2) * 260, members, cols=2,
                                  w=175, h=50, min_w=385))
    return m


# ------------------------------------------------------------------------------------------------
# 3. NIS2 risk-management measures
# ------------------------------------------------------------------------------------------------

NIS2_MEASURES = [
    ("a", "Risk analysis and information system security policies",
     "Policies on risk analysis and information system security.", "Information security risk assessment",
     "BusinessProcess"),
    ("b", "Incident handling", "Incident handling.", "Security incident response", "BusinessProcess"),
    ("c", "Business continuity and crisis management",
     "Business continuity, such as backup management and disaster recovery, and crisis management.",
     "Backup, disaster recovery and crisis management", "BusinessProcess"),
    ("d", "Supply chain security",
     "Supply chain security, including security-related aspects of the relationships with direct "
     "suppliers or service providers.", "Supplier security assessment", "BusinessProcess"),
    ("e", "Secure acquisition, development and maintenance",
     "Security in network and information systems acquisition, development and maintenance, including "
     "vulnerability handling and disclosure.", "Secure development and vulnerability management",
     "BusinessProcess"),
    ("f", "Effectiveness assessment",
     "Policies and procedures to assess the effectiveness of cybersecurity risk-management measures.",
     "Control effectiveness review", "BusinessProcess"),
    ("g", "Cyber hygiene and training", "Basic cyber hygiene practices and cybersecurity training.",
     "Security awareness and hygiene programme", "BusinessProcess"),
    ("h", "Cryptography and encryption", "Policies and procedures regarding the use of cryptography and, "
     "where appropriate, encryption.", "Key and certificate management", "ApplicationService"),
    ("i", "HR security, access control and asset management",
     "Human resources security, access control policies and asset management.",
     "Identity and access management", "ApplicationService"),
    ("j", "Multi-factor authentication and secured communications",
     "The use of multi-factor authentication or continuous authentication solutions, secured voice, "
     "video and text communications and secured emergency communication systems within the entity, "
     "where appropriate.", "Multi-factor authentication", "ApplicationService"),
]


def nis2() -> Model:
    m = Model("nis2-measures", "NIS2 Cybersecurity Risk-Management Measures (starter)",
              "The ten cybersecurity risk-management measures of Article 21(2) of the NIS2 Directive "
              "(EU) 2022/2555, the governance duty of Article 20 and the incident reporting stages of "
              "Article 23, each traced to the control that realizes it. Replace the example controls with "
              "your own processes and systems; a requirement left without a realizing control is a gap. "
              "This model is a structuring aid, not legal advice: confirm scope and national transposition "
              "with your compliance team.")
    driver = m.el("Driver", "NIS2 Directive (EU) 2022/2555",
                  "Applies to essential and important entities in the sectors of Annexes I and II, as "
                  "transposed into national law by member states from 18 October 2024.")
    board = m.el("Stakeholder", "Management body", "Approves the cybersecurity risk-management measures, "
                 "oversees their implementation and can be held liable for infringements (Article 20).")
    m.rel("Association", board, driver)
    goal = m.el("Goal", "Appropriate and proportionate cybersecurity risk management",
                "Article 21(1): technical, operational and organisational measures to manage the risks to "
                "the security of network and information systems, and to prevent or minimise the impact of "
                "incidents.")
    m.rel("Influence", driver, goal)
    art21 = m.el("Requirement", "Article 21(2) measures", "The minimum set of measures, based on an "
                 "all-hazards approach.")
    m.rel("Realization", art21, goal)
    reqs, controls = [], []
    for letter, short, text, control, ctype in NIS2_MEASURES:
        r = m.el("Requirement", f"21(2)({letter}) {short}", text)
        m.rel("Composition", art21, r)
        c = m.el(ctype, control, "Example control. Replace with the process or system that meets this "
                 "measure in your organisation.", control_owner="", evidence_location="")
        m.rel("Realization", c, r)
        reqs.append(r)
        controls.append(c)
    gov = m.el("Requirement", "Article 20 governance and training",
               "Management bodies approve the measures, oversee implementation and follow cybersecurity "
               "training; entities are encouraged to offer similar training to employees regularly.")
    m.rel("Realization", gov, goal)
    gov_ctl = m.el("BusinessProcess", "Board cyber risk oversight", "Example control: periodic board review "
                   "of cyber risk, measures and training records.", control_owner="", evidence_location="")
    m.rel("Realization", gov_ctl, gov)
    rep = m.el("Requirement", "Article 23 incident reporting",
               "Significant incidents are reported to the CSIRT or competent authority in stages: an early "
               "warning within 24 hours of becoming aware, an incident notification within 72 hours, and a "
               "final report within one month of the notification.")
    m.rel("Realization", rep, goal)
    rep_ctl = m.el("BusinessProcess", "Significant incident notification",
                   "Example control: classify incidents against the significance criteria and file the early "
                   "warning, notification and final report on time.", control_owner="", evidence_location="")
    m.rel("Realization", rep_ctl, rep)
    m.rel("Triggering", controls[1], rep_ctl)

    v = m.view("NIS2 measures and controls", "Each Article 21(2) measure with the control that realizes "
               "it, plus the governance and reporting duties. Fill in the owner and evidence location of "
               "every control; that pair is what an auditor asks for first.", "Motivation")
    v.nodes += [Node(board, 20, 20, 170, 55), Node(driver, 230, 20, 210, 55), Node(goal, 480, 20, 820, 55),
                Node(art21, 480, 120, 280, 50), Node(gov, 820, 120, 220, 55), Node(rep, 1080, 120, 220, 55),
                Node(gov_ctl, 820, 230, 220, 55), Node(rep_ctl, 1080, 230, 220, 55)]
    for i, (r, c) in enumerate(zip(reqs, controls)):
        x = 20 + (i % 5) * 245
        y = 330 + (i // 5) * 230
        v.nodes += [Node(r, x, y, 230, 80), Node(c, x, y + 125, 230, 60)]
    on_view = on_view_of(v)
    v.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view
                      and r.type not in ("Composition", "Triggering")]
    return m


# ------------------------------------------------------------------------------------------------
# 4. DORA: critical functions, ICT services and third parties
# ------------------------------------------------------------------------------------------------

def dora() -> Model:
    m = Model("dora-ict-map", "DORA Critical Functions and ICT Third-Party Map (starter)",
              "Maps critical or important functions to the ICT services that support them and the ICT "
              "third-party providers behind those services, alongside the five areas of the Digital "
              "Operational Resilience Act, Regulation (EU) 2022/2554, applicable since 17 January 2025. "
              "The function-to-service-to-provider chain is the backbone of the register of information "
              "on contractual arrangements (Article 28(3)) and of exit planning (Article 28(8)). Behind each "
              "provider sit the subcontractors that effectively underpin its service, ranked as the register's "
              "ICT service supply chain template (B_05.02 of Implementing Regulation (EU) 2024/2956) asks. "
              "This model is a structuring aid, not legal advice.")
    driver = m.el("Driver", "DORA Regulation (EU) 2022/2554")
    goal = m.el("Goal", "Digital operational resilience",
                "The ability to build, assure and review operational integrity and reliability by ensuring "
                "the full range of ICT capabilities needed to address the security of network and "
                "information systems.")
    m.rel("Influence", driver, goal)
    pillars = [
        ("ICT risk management", "Chapter II, Articles 5 to 16: an ICT risk-management framework owned by "
         "the management body, covering identification, protection, detection, response, recovery, "
         "learning and communication."),
        ("ICT incident management, classification and reporting", "Chapter III, Articles 17 to 23: a "
         "management process for ICT-related incidents, classification by the set criteria and reporting "
         "of major incidents to the competent authority."),
        ("Digital operational resilience testing", "Chapter IV, Articles 24 to 27: a risk-based testing "
         "programme, with threat-led penetration testing at least every three years for entities the "
         "competent authority identifies."),
        ("ICT third-party risk management", "Chapter V, Articles 28 to 44: third-party risk strategy, the "
         "register of information, pre-contract due diligence, mandatory contractual provisions and exit "
         "strategies."),
        ("Information sharing", "Chapter VI, Article 45: voluntary arrangements to share cyber threat "
         "information and intelligence."),
    ]
    pillar_ids = []
    for name, text in pillars:
        p = m.el("Requirement", name, text)
        m.rel("Realization", p, goal)
        pillar_ids.append(p)
    register = m.el("Requirement", "Register of information (Article 28(3))",
                    "A register, at entity, sub-consolidated and consolidated level, of all contractual "
                    "arrangements on the use of ICT services provided by ICT third-party service providers, "
                    "distinguishing those that support critical or important functions.")
    exit_req = m.el("Requirement", "Exit strategies (Article 28(8))",
                    "Exit strategies for ICT services supporting critical or important functions, tested "
                    "and documented in exit plans.")
    m.rel("Composition", pillar_ids[3], register)
    m.rel("Composition", pillar_ids[3], exit_req)

    functions = {
        "Payments processing": "Critical or important function: its disruption would materially impair "
                               "financial performance or the continuity of services.",
        "Customer account servicing": "Critical or important function.",
        "Regulatory reporting": "Important function: supports compliance with authorisation conditions.",
    }
    f_ids = {n: m.el("BusinessFunction", n, d, critical_or_important="Yes", recovery_time_objective="")
             for n, d in functions.items()}
    apps = {
        "Payments engine": ["Payments processing"],
        "Core banking platform": ["Payments processing", "Customer account servicing"],
        "Customer portal": ["Customer account servicing"],
        "Reporting platform": ["Regulatory reporting"],
    }
    a_ids = {}
    for name, served in apps.items():
        a = m.el("ApplicationComponent", name, "", ict_service_type="", data_location="")
        a_ids[name] = a
        for f in served:
            m.rel("Serving", a, f_ids[f])
    providers = {
        "Payments software vendor": ("Managed payments service", ["Payments engine"]),
        "Cloud infrastructure provider": ("Cloud hosting", ["Core banking platform", "Customer portal",
                                                            "Reporting platform"]),
    }
    p_rel = []
    for prov, (svc, supported) in providers.items():
        actor = m.el("BusinessActor", prov, "ICT third-party service provider, rank 1 in its ICT service "
                     "supply chain.", lei="", country="", substitutability="", rank="1")
        service = m.el("TechnologyService", svc, "ICT service provided by the third party.")
        contract = m.el("Contract", f"{svc} agreement", "Contractual arrangement recorded in the register of "
                        "information. Check the mandatory provisions of Article 30.", contract_reference="",
                        exit_plan_tested="")
        m.rel("Association", actor, contract)
        m.rel("Association", contract, service)
        p_rel.append((actor, contract, service))
        for app in supported:
            m.rel("Serving", service, a_ids[app])

    # The ICT service supply chain: subcontractors that effectively underpin each provider's service.
    # Rank follows the register (B_05.02): the direct provider is rank 1, its subcontractor rank 2, and
    # a subcontractor's own subcontractor rank 3. The data centre operator appears in both chains.
    by_name = {m.elements[a].name: (a, s) for a, _, s in p_rel}
    subcontractors = [
        # name, service, ICT service type (Annex III), recipient, rank, substitutability, documentation
        ("Payments hosting provider", "Managed hosting", "S17 Cloud services: IaaS",
         "Payments software vendor", "2", "Medium complexity in terms of substitutability",
         "Hosts the payments software vendor's managed service."),
        ("Network connectivity provider", "Network connectivity", "S10 Telecom carrier",
         "Payments software vendor", "2", "Easily substitutable",
         "Carries traffic between the payments software vendor and the payment schemes."),
        ("Managed security monitoring provider", "Security monitoring", "S04 ICT security management services",
         "Cloud infrastructure provider", "2", "Medium complexity in terms of substitutability",
         "Runs round-the-clock security monitoring for the cloud infrastructure provider."),
        ("Data centre operator", "Data centre colocation",
         "S07 ICT, facilities and hosting services (excluding Cloud services)",
         "Cloud infrastructure provider; Payments hosting provider", "2 (Cloud hosting); 3 (Managed payments service)",
         "Highly complex substitutability",
         "Operates the data centres used by both the cloud infrastructure provider and the payments hosting "
         "provider: a concentration that neither direct contract shows."),
    ]
    s_ids = {}
    for name, svc, ict_type, recipient, rank, subst, text in subcontractors:
        actor = m.el("BusinessActor", name, f"ICT subcontractor. {text} Record the date the provider last "
                     "confirmed this subcontracting arrangement.",
                     rank=rank, **{"Recipient of sub-contracted ICT services": recipient},
                     lei="", country="", ict_service_type=ict_type,
                     supports_critical_or_important_function="Yes", substitutability=subst,
                     last_confirmed_by_provider="")
        service = m.el("TechnologyService", svc, "ICT service delivered by the subcontractor.")
        m.rel("Association", actor, service)
        s_ids[name] = (actor, service)
    sub_of = {name: rec for name, _, _, rec, *_ in subcontractors}
    for name, (actor, service) in s_ids.items():
        for recipient in sub_of[name].split("; "):
            r_actor, r_service = by_name.get(recipient) or s_ids[recipient]
            m.rel("Serving", actor, r_actor, "subcontractor to")
            m.rel("Serving", service, r_service)

    v = m.view("Critical functions and ICT third parties", "Read top to bottom: a critical or important "
               "function, the applications that serve it, the ICT services they run on, and the "
               "third-party provider and contract behind each service. Every chain that ends in a single "
               "provider with no tested exit plan is a concentration risk to report.")
    v.nodes += [Node(f_ids[n], 20 + i * 280, 20, 250, 60) for i, n in enumerate(functions)]
    v.nodes += [Node(a_ids[n], 20 + i * 210, 160, 190, 55) for i, n in enumerate(apps)]
    for i, (actor, contract, service) in enumerate(p_rel):
        x = 20 + i * 430
        v.nodes += [Node(service, x, 300, 220, 55), Node(contract, x, 410, 220, 55), Node(actor, x, 520, 220, 55)]
    on_view = on_view_of(v)
    v.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]

    sv = m.view("ICT subcontracting chain", "Read top to bottom: a critical or important function, the "
                "applications that serve it, the provider's ICT service and contract, the rank 1 provider, and "
                "the subcontractors behind it with the services they deliver. The data centre operator serves "
                "both chains, at rank 2 behind the cloud infrastructure provider and rank 3 behind the payments "
                "software vendor: a concentration the direct contracts do not show.")
    pay, cloud = p_rel
    sv.nodes += [Node(f_ids["Payments processing"], 120, 20, 240, 60),
                 Node(f_ids["Customer account servicing"], 620, 20, 240, 60),
                 Node(f_ids["Regulatory reporting"], 960, 20, 240, 60)]
    sv.nodes += [Node(a_ids["Payments engine"], 220, 150, 180, 55),
                 Node(a_ids["Core banking platform"], 540, 150, 180, 55),
                 Node(a_ids["Customer portal"], 760, 150, 180, 55),
                 Node(a_ids["Reporting platform"], 1000, 150, 180, 55)]
    for (actor, contract, service), x in [(pay, 220), (cloud, 860)]:
        sv.nodes += [Node(service, x, 280, 180, 55), Node(contract, x, 390, 180, 55), Node(actor, x, 500, 180, 55)]
    for name, x, y in [("Network connectivity provider", 20, 620), ("Payments hosting provider", 420, 620),
                       ("Data centre operator", 640, 720), ("Managed security monitoring provider", 1060, 620)]:
        actor, service = s_ids[name]
        sv.nodes += [Node(service, x, 280, 180, 55), Node(actor, x, y, 180, 55)]
    on_view = on_view_of(sv)
    sv.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]

    pv = m.view("DORA requirement areas", "The five areas of the regulation, with the two third-party "
                "duties this model's map feeds directly.", "Motivation")
    pv.nodes += [Node(driver, 60, 20, 220, 55), Node(goal, 430, 20, 260, 55)]
    pv.nodes += [Node(p, 20 + i * 215, 260, 200, 80) for i, p in enumerate(pillar_ids)]
    pv.nodes += [Node(register, 560, 390, 200, 65), Node(exit_req, 780, 390, 200, 65)]
    on_view = on_view_of(pv)
    pv.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]
    return m


# ------------------------------------------------------------------------------------------------
# 5. Layered view: customer onboarding
# ------------------------------------------------------------------------------------------------

def layered_onboarding() -> Model:
    m = Model("layered-customer-onboarding", "Layered View: Customer Onboarding (starter)",
              "A complete business-to-technology slice for one process, customer onboarding with identity "
              "verification. It is the pattern most ArchiMate models are built from: who does the work, "
              "the process and the service it delivers, the application services and components that "
              "support it, the data they use, and the technology they run on. Copy the structure for any "
              "other process.")
    customer = m.el("BusinessActor", "Customer")
    applicant = m.el("BusinessRole", "Applicant")
    analyst = m.el("BusinessRole", "Onboarding analyst")
    m.rel("Assignment", customer, applicant)
    event = m.el("BusinessEvent", "Application received")
    steps = [m.el("BusinessProcess", n) for n in
             ["Capture application", "Verify identity", "Assess risk", "Open account"]]
    m.rel("Triggering", event, steps[0])
    for a, b in zip(steps, steps[1:]):
        m.rel("Triggering", a, b)
    m.rel("Assignment", analyst, steps[2])
    service = m.el("BusinessService", "Account opening")
    m.rel("Realization", steps[3], service)
    m.rel("Serving", service, applicant)
    record = m.el("BusinessObject", "Customer record")
    m.rel("Access", steps[3], record, access="Write")

    app_svcs = {
        "Application intake": "Capture application",
        "Identity verification": "Verify identity",
        "Risk scoring": "Assess risk",
        "Account provisioning": "Open account",
    }
    comps = {"Onboarding portal": ["Application intake"], "Identity verification service": ["Identity verification"],
             "Risk engine": ["Risk scoring"], "Core banking platform": ["Account provisioning"]}
    svc_ids = {}
    for svc, step in app_svcs.items():
        sid = m.el("ApplicationService", svc)
        svc_ids[svc] = sid
        m.rel("Serving", sid, steps[[m.elements[s].name for s in steps].index(step)])
    comp_ids = {}
    for comp, svcs in comps.items():
        cid = m.el("ApplicationComponent", comp)
        comp_ids[comp] = cid
        for s in svcs:
            m.rel("Realization", cid, svc_ids[s])
    data = m.el("DataObject", "Customer profile")
    m.rel("Access", comp_ids["Core banking platform"], data, access="Write")
    m.rel("Access", comp_ids["Risk engine"], data, access="Read")
    m.rel("Realization", data, record)

    cluster = m.el("Node", "Application cluster")
    db = m.el("Node", "Database server")
    runtime = m.el("SystemSoftware", "Container runtime")
    dbms = m.el("SystemSoftware", "Relational database")
    m.rel("Composition", cluster, runtime)
    m.rel("Composition", db, dbms)
    hosting = m.el("TechnologyService", "Container hosting")
    storage = m.el("TechnologyService", "Managed database")
    m.rel("Realization", runtime, hosting)
    m.rel("Realization", dbms, storage)
    for comp in ["Onboarding portal", "Risk engine", "Identity verification service"]:
        m.rel("Serving", hosting, comp_ids[comp])
    m.rel("Serving", storage, comp_ids["Core banking platform"])

    v = m.view("Customer onboarding: business to technology", "Business layer on top, application layer "
               "in the middle, technology layer at the bottom. Every arrow answers a question a change "
               "will raise: who uses this, what supports it, what does it run on.", "Layered")
    v.nodes += [Node(customer, 20, 20, 150, 50), Node(applicant, 200, 20, 150, 50),
                Node(service, 400, 20, 170, 50), Node(analyst, 640, 20, 170, 50), Node(record, 880, 20, 160, 50),
                Node(event, 20, 120, 150, 50)]
    v.nodes += [Node(s, 200 + i * 210, 120, 180, 50) for i, s in enumerate(steps)]
    v.nodes += [Node(svc_ids[s], 200 + i * 210, 250, 180, 50) for i, s in enumerate(app_svcs)]
    v.nodes += [Node(comp_ids[c], 200 + i * 210, 350, 180, 55) for i, c in enumerate(comps)]
    v.nodes += [Node(data, 1060, 250, 150, 55)]
    v.nodes += [Node(hosting, 300, 480, 180, 50), Node(storage, 720, 480, 180, 50),
                Node(cluster, 280, 580, 220, 110, [Node(runtime, 300, 620, 180, 50)]),
                Node(db, 700, 580, 220, 110, [Node(dbms, 720, 620, 180, 50)])]
    on_view = on_view_of(v)
    # Composition is shown by nesting the system software inside its node, not by a line.
    v.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view and r.type != "Composition"]
    return m



# ------------------------------------------------------------------------------------------------
# 6. One company, end to end: the model a company brain answers from
# ------------------------------------------------------------------------------------------------

def company_model() -> Model:
    m = Model("company-model", "One Company, End to End (starter)",
              "A small subscription business modelled end to end: what it is trying to achieve, the "
              "capabilities that deliver it, the applications behind them, the suppliers and contracts "
              "behind those, what each costs, who owns it and what could go wrong. Because every piece is "
              "connected, the model answers the questions people actually ask: what breaks if a system "
              "or supplier fails, what a capability really costs, and who has to act. Replace the example "
              "company with your own, starting from a spreadsheet of applications.")
    driver = m.el("Driver", "Customer churn above plan", "Monthly churn has run above plan for two quarters.")
    goal = m.el("Goal", "Keep monthly churn below 3%")
    m.rel("Influence", driver, goal)
    caps = {n: m.el("Capability", n) for n in ["Customer Service", "Billing", "Order Management",
                                                  "Customer Insight"]}
    apps = {
        "Customer Portal": ("Customer Service", "Head of Customer Success", "18,000"),
        "CRM Platform": ("Customer Insight", "Head of Customer Success", "42,000"),
        "Billing System": ("Billing", "Finance Director", "36,000"),
        "Order Management System": ("Order Management", "Operations Director", "55,000"),
        "Data Warehouse": ("Customer Insight", "Head of Data", "24,000"),
    }
    a = {}
    for name, (cap, owner, cost) in apps.items():
        a[name] = m.el("ApplicationComponent", name, "", owner=owner, annual_run_cost_gbp=cost)
        m.rel("Realization", a[name], caps[cap])
    m.rel("Serving", a["CRM Platform"], a["Customer Portal"])
    m.rel("Serving", a["Billing System"], a["Customer Portal"])
    m.rel("Serving", a["Order Management System"], a["Billing System"])
    m.rel("Serving", a["CRM Platform"], a["Data Warehouse"])
    owners = {o: m.el("BusinessRole", o) for o in sorted({o for _, o, _ in apps.values()})}
    for name, (_, owner, _) in apps.items():
        m.rel("Association", owners[owner], a[name], name="owns")
    cloud = m.el("TechnologyService", "Cloud hosting", "Hosts every application except the billing system.")
    billing_saas = m.el("TechnologyService", "Hosted billing platform",
                        "The billing system runs on the vendor's own platform.")
    for name in ["Customer Portal", "CRM Platform", "Order Management System", "Data Warehouse"]:
        m.rel("Serving", cloud, a[name])
    m.rel("Serving", billing_saas, a["Billing System"])
    suppliers = [("Cloud provider", cloud, "Cloud hosting agreement", "96,000", "Yes"),
                 ("Billing software vendor", billing_saas, "Billing subscription", "36,000", "No")]
    contracts, actors = {}, {}
    for supplier, service, contract, cost, exit_plan in suppliers:
        actors[supplier] = m.el("BusinessActor", supplier, "Supplier.")
        contracts[supplier] = m.el("Contract", contract, "", annual_cost_gbp=cost, exit_plan_tested=exit_plan,
                                   renewal_date="")
        m.rel("Association", actors[supplier], contracts[supplier])
        m.rel("Association", contracts[supplier], service)
    risk = m.el("Assessment", "Billing depends on one vendor with no tested exit plan",
                "If the billing vendor fails or exits, invoices stop and the customer portal cannot show "
                "account balances. Likelihood low, impact high.")
    m.rel("Association", risk, contracts["Billing software vendor"])
    m.rel("Influence", risk, goal)

    v = m.view("The company on one page", "Goal, capabilities, applications, suppliers and the risk that "
               "matters most, connected. Follow the lines down from any capability to see what it depends on.")
    # Billing sits in its own right-hand column because it is the one part not on the shared cloud;
    # the motivation column on the far right keeps the risk-to-goal line clear of everything else.
    v.nodes += [Node(caps["Customer Service"], 20, 20, 180, 50), Node(caps["Order Management"], 220, 20, 180, 50),
                Node(caps["Customer Insight"], 520, 20, 180, 50), Node(caps["Billing"], 860, 20, 180, 50)]
    for name, x in [("Customer Portal", 20), ("Order Management System", 220), ("CRM Platform", 420),
                    ("Data Warehouse", 620), ("Billing System", 860)]:
        v.nodes.append(Node(a[name], x, 150, 180, 55))
    v.nodes += [Node(cloud, 320, 290, 200, 50), Node(billing_saas, 840, 290, 220, 50)]
    for supplier, x in [("Cloud provider", 310), ("Billing software vendor", 840)]:
        v.nodes += [Node(contracts[supplier], x, 400, 220, 55), Node(actors[supplier], x, 510, 220, 50)]
    v.nodes += [Node(driver, 1120, 20, 220, 50), Node(goal, 1120, 150, 220, 50), Node(risk, 1120, 393, 220, 70)]
    on_view = on_view_of(v)
    # Application-to-application dependencies are drawn in the impact view, where they are the point.
    v.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view
                      and not (r.type == "Serving" and m.elements[r.source].type == "ApplicationComponent")]

    o = m.view("Who owns what", "Each application with its accountable owner and annual run cost, so "
               "an incident or a renewal always lands with a named role.")
    x = 20
    for role in owners:
        mine = [n for n, (_, ow, _) in apps.items() if ow == role]
        o.nodes.append(Node(owners[role], x, 20, 220 * len(mine) + 20 * (len(mine) - 1), 50))
        for name in mine:
            o.nodes.append(Node(a[name], x, 140, 220, 55))
            x += 240
    on_view = on_view_of(o)
    o.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view and r.name == "owns"]

    impact = m.view("What breaks if the billing vendor fails", "The chain an impact question walks: "
                    "supplier, contract, service, the billing system, the portal that depends on it, the "
                    "capabilities they realize, and the goal the risk puts in danger.")
    chain = [actors["Billing software vendor"], contracts["Billing software vendor"], billing_saas,
             a["Billing System"], a["Customer Portal"]]
    for i, el in enumerate(chain):
        impact.nodes.append(Node(el, 20 + i * 240, 260, 210, 55))
    impact.nodes += [Node(caps["Billing"], 740, 400, 200, 50), Node(caps["Customer Service"], 980, 400, 200, 50),
                     Node(risk, 260, 110, 330, 70), Node(goal, 700, 120, 220, 50)]
    on_view = on_view_of(impact)
    impact.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]
    return m


# ------------------------------------------------------------------------------------------------
# 7. ISO 22301 business continuity: clauses, impact analysis, strategies and dependencies
# ------------------------------------------------------------------------------------------------

ISO22301_CLAUSES = [
    # number, short title, summary in our own words, realizing control
    ("4", "Context of the organisation", "Know the organisation, its interested parties and their legal and "
     "regulatory requirements, and set the scope of the management system.",
     "BCMS scope and interested parties review"),
    ("5", "Leadership", "Top management commits to the management system, sets a business continuity policy "
     "and assigns roles, responsibilities and authorities.", "Business continuity policy approval"),
    ("6", "Planning", "Address risks and opportunities, set business continuity objectives with plans to "
     "achieve them, and plan changes to the management system.", "Continuity objectives planning"),
    ("7", "Support", "Provide resources, competence, awareness, communication and documented information.",
     "Continuity awareness and competence programme"),
    ("9", "Performance evaluation", "Monitor, measure, analyse and evaluate, run internal audits and hold "
     "management reviews.", "Internal audit and management review"),
    ("10", "Improvement", "Handle nonconformities with corrective action and improve the management system "
     "continually.", "Corrective action and improvement"),
]

ISO22301_OPERATION = [
    ("8.1", "Operational planning and control", "Plan, run and control the processes the management system "
     "needs, including outsourced processes and the supply chain.", "Supplier and outsourced process control"),
    ("8.2", "Business impact analysis and risk assessment", "Analyse the impact of disrupting each activity "
     "over time, set recovery priorities and objectives, and assess the risks of disruption.",
     "Business impact analysis"),
    ("8.3", "Business continuity strategies and solutions", "Identify, select and put in place the strategies "
     "and resources that meet the recovery objectives.", "Continuity strategy selection"),
    ("8.4", "Business continuity plans and procedures", "Set up a response structure, warning and "
     "communication arrangements, and documented plans for response and recovery.",
     "Incident management team"),
    ("8.5", "Exercise programme", "Exercise and test the strategies and plans on a schedule, and act on "
     "what the exercises show.", "Exercise and test programme"),
    ("8.6", "Evaluation of business continuity documentation and capabilities", "Evaluate whether the "
     "impact analysis, risk assessment, strategies, plans and suppliers' capabilities remain suitable and "
     "effective.", "Continuity plan and supplier capability review"),
]


def iso22301() -> Model:
    m = Model("iso22301-business-continuity", "ISO 22301 Business Continuity (starter)",
              "A business continuity management system (BCMS) traced from the requirements of ISO 22301:2019 "
              "(clauses 4 to 10) to the work that meets them, and from there to an example organisation's "
              "prioritised activities. Each activity carries its recovery time objective, maximum tolerable "
              "period of disruption, recovery point objective and minimum business continuity objective, set "
              "by the business impact analysis, and is linked to the applications, technology, people and "
              "suppliers it depends on and to the continuity strategy and plan that protect it. Because every "
              "dependency is connected, the model answers what stops, and how soon it must be back, when a "
              "system or supplier fails. Clause numbers and titles are given for reference only; read the "
              "requirements in the standard itself. Replace the example online retailer with your own "
              "activities and recovery objectives.")
    driver = m.el("Driver", "ISO 22301:2019 Business continuity management systems",
                  "The international standard for a business continuity management system, read with "
                  "Amendment 1:2024 on climate action changes. Certification is against clauses 4 to 10.")
    board = m.el("Stakeholder", "Top management", "Owns the business continuity policy and objectives, and "
                 "reviews the management system at planned intervals.")
    m.rel("Association", board, driver)
    goal = m.el("Goal", "Keep prioritised activities within their recovery objectives",
                "Continue delivering products and services at an acceptable, agreed capacity during a "
                "disruption, and recover them within the agreed time.")
    m.rel("Influence", driver, goal)
    bcms = m.el("Requirement", "ISO 22301 requirements (clauses 4 to 10)",
                "The requirements a certified management system must meet.")
    m.rel("Realization", bcms, goal)
    clause, control = {}, {}
    for num, title, text, ctl in ISO22301_CLAUSES:
        clause[num] = m.el("Requirement", f"Clause {num}: {title}", text)
        m.rel("Composition", bcms, clause[num])
    clause["8"] = m.el("Requirement", "Clause 8: Operation", "Plan and run the business continuity "
                       "processes: impact analysis, risk assessment, strategies, plans, exercises and evaluation.")
    m.rel("Composition", bcms, clause["8"])
    for num, title, text, ctl in ISO22301_OPERATION:
        clause[num] = m.el("Requirement", f"{num} {title}", text)
        m.rel("Composition", clause["8"], clause[num])
    for num, _, _, ctl in ISO22301_CLAUSES + ISO22301_OPERATION:
        kind = "BusinessActor" if num == "8.4" else "BusinessProcess"
        control[num] = m.el(kind, ctl, "Example control. Replace with the process, team or record that meets "
                            "this clause in your organisation.", control_owner="", evidence_location="")
        m.rel("Realization", control[num], clause[num])
    risk_assessment = m.el("BusinessProcess", "Continuity risk assessment", "Identifies the risks of "
                           "disruption to prioritised activities and the resources they need, and decides how "
                           "to treat them.", control_owner="", evidence_location="")
    m.rel("Realization", risk_assessment, clause["8.2"])

    # The example organisation: an online retailer and its prioritised activities.
    activities = [
        # name, RTO, MTPD, RPO, MBCO, owner
        ("Take customer orders", "4 hours", "24 hours", "15 minutes",
         "Website orders accepted at half of normal volume", "Head of E-commerce"),
        ("Dispatch orders", "24 hours", "3 days", "1 hour", "Priority orders dispatched next day",
         "Operations Director"),
        ("Take customer payments", "4 hours", "24 hours", "No lost transactions",
         "Card payments taken for every accepted order", "Finance Director"),
        ("Answer customer enquiries", "24 hours", "5 days", "24 hours",
         "Email and phone enquiries answered within two working days", "Head of Customer Service"),
    ]
    act = {}
    for name, rto, mtpd, rpo, mbco, owner in activities:
        act[name] = m.el("BusinessProcess", name, "Prioritised activity. Recovery objectives set by the business "
                         "impact analysis and agreed by top management.", activity_owner=owner,
                         recovery_time_objective=rto, maximum_tolerable_period_of_disruption=mtpd,
                         recovery_point_objective=rpo, minimum_business_continuity_objective=mbco,
                         last_impact_analysis="")
        m.rel("Association", control["8.2"], act[name], "sets recovery objectives for")

    apps = {
        "E-commerce platform": ["Take customer orders"],
        "Order management system": ["Take customer orders", "Dispatch orders"],
        "Warehouse management system": ["Dispatch orders"],
        "Payment gateway": ["Take customer payments"],
        "Customer service desk": ["Answer customer enquiries"],
    }
    app = {}
    for name, served in apps.items():
        app[name] = m.el("ApplicationComponent", name, "", recovery_time_objective="", recovery_point_objective="")
        for a in served:
            m.rel("Serving", app[name], act[a])
    team = m.el("BusinessActor", "Warehouse team", "Staff who pick, pack and hand over parcels at the "
                "distribution centre.", minimum_staffing="")
    m.rel("Assignment", team, act["Dispatch orders"])
    site = m.el("Location", "Distribution centre", "The single site that stores and dispatches stock.")
    cloud = m.el("TechnologyService", "Cloud hosting", "Runs the e-commerce platform and the order management "
                 "system in one primary region.")
    server = m.el("Node", "Warehouse server", "On-site server running the warehouse management system.")
    delivery = m.el("BusinessService", "Parcel delivery", "Collection and delivery of customer parcels.")
    m.rel("Serving", cloud, app["E-commerce platform"])
    m.rel("Serving", cloud, app["Order management system"])
    m.rel("Serving", server, app["Warehouse management system"])
    m.rel("Serving", delivery, act["Dispatch orders"])
    m.rel("Aggregation", site, server)
    m.rel("Aggregation", site, team)

    suppliers = [
        # supplier, contract, what the contract covers, exit plan tested
        ("Cloud provider", "Cloud hosting agreement", cloud, "No"),
        ("Courier", "Courier agreement", delivery, "No"),
        ("Payment service provider", "Payment services agreement", app["Payment gateway"], "Yes"),
        ("Service desk vendor", "Service desk subscription", app["Customer service desk"], "No"),
    ]
    sup, con = {}, {}
    for supplier, contract, covers, exit_plan in suppliers:
        sup[supplier] = m.el("BusinessActor", supplier, "Supplier.", supplier_continuity_capability_assessed="")
        con[supplier] = m.el("Contract", contract, "", exit_plan_tested=exit_plan, renewal_date="")
        m.rel("Association", sup[supplier], con[supplier])
        m.rel("Association", con[supplier], covers)
    single = m.el("Assessment", "Orders stop if the cloud region fails",
                  "The e-commerce platform and the order management system share one cloud region and one "
                  "provider, so a regional outage stops order taking and dispatch together. Fail-over to the "
                  "secondary region has not been exercised.")
    m.rel("Association", single, con["Cloud provider"])
    m.rel("Influence", single, goal)

    strategies = [
        # strategy, activities it protects, plan
        ("Fail over to the secondary cloud region", ["Take customer orders", "Dispatch orders"],
         "Website and order recovery plan"),
        ("Take phone orders on a manual form", ["Take customer orders"], "Website and order recovery plan"),
        ("Switch to the standby courier", ["Dispatch orders"], "Dispatch continuity plan"),
        ("Route payments to the secondary provider", ["Take customer payments"], "Payments continuity plan"),
        ("Answer enquiries from home on the cloud service desk", ["Answer customer enquiries"],
         "Customer service continuity plan"),
    ]
    strat, plan = {}, {}
    for name, protects, plan_name in strategies:
        strat[name] = m.el("BusinessProcess", name, "Continuity strategy chosen to meet the recovery objectives "
                           "of the activities it protects.", last_exercised="")
        m.rel("Realization", strat[name], clause["8.3"])
        for a in protects:
            m.rel("Association", strat[name], act[a], "protects")
        if plan_name not in plan:
            plan[plan_name] = m.el("BusinessObject", plan_name, "Documented response and recovery plan.",
                                   plan_owner="", last_reviewed="")
            m.rel("Realization", plan[plan_name], clause["8.4"])
        m.rel("Access", strat[name], plan[plan_name], access="Read")

    # View 1: the clauses and the controls that realize them.
    v = m.view("BCMS requirements by clause", "Clauses 4 to 10 of ISO 22301, with clause 8 opened into its six "
               "operational subclauses, each with the control that realizes it. Fill in the owner and evidence "
               "location of every control; that pair is what a certification auditor asks for first.",
               "Motivation")
    v.nodes += [Node(board, 20, 20, 170, 55), Node(driver, 230, 20, 230, 55), Node(goal, 500, 20, 800, 55),
                Node(bcms, 750, 120, 300, 50)]
    for i, num in enumerate(["4", "5", "6", "7", "9", "10"]):
        x = 20 + i * 215
        v.nodes += [Node(clause[num], x, 230, 200, 70), Node(control[num], x, 360, 200, 60)]
    ops = ["8.1", "8.2", "8.3", "8.4", "8.5", "8.6"]
    box = container(clause["8"], 20, 480, [clause[n] for n in ops], cols=6, w=200, h=85,
                    title="Clause 8: Operation")
    v.nodes.append(box)
    y = box.y + box.h + 55
    for i, num in enumerate(ops):
        v.nodes.append(Node(control[num], 35 + i * 215, y, 200, 60))
    on_view = on_view_of(v)
    v.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view and r.type != "Composition"]

    # View 2: what each prioritised activity depends on.
    d = m.view("Prioritised activities and their dependencies", "Read top to bottom: each prioritised activity "
               "with its recovery objectives, the applications and services it needs, what they run on, and the "
               "contract and supplier behind each. Any activity whose chain ends in a supplier with no tested "
               "exit plan, or in a single site, cannot recover faster than that supplier or site.")
    d.nodes += [Node(team, 400, 20, 220, 50)]
    for name, x in [("Take customer orders", 100), ("Dispatch orders", 400), ("Take customer payments", 770),
                    ("Answer customer enquiries", 1020)]:
        d.nodes.append(Node(act[name], x, 130, 220, 60))
    for name, x in [("E-commerce platform", 20), ("Order management system", 220),
                    ("Warehouse management system", 420)]:
        d.nodes.append(Node(app[name], x, 280, 180, 55))
    d.nodes += [Node(delivery, 620, 280, 180, 55), Node(app["Payment gateway"], 820, 280, 180, 55),
                Node(app["Customer service desk"], 1060, 280, 180, 55)]
    d.nodes += [Node(cloud, 110, 410, 200, 50), Node(site, 400, 395, 220, 120, [Node(server, 420, 435, 180, 55)])]
    for supplier, x, y in [("Cloud provider", 110, 520), ("Courier", 620, 410), ("Payment service provider", 820, 410),
                           ("Service desk vendor", 1060, 410)]:
        d.nodes += [Node(con[supplier], x, y, 200 if x == 110 else 180, 55),
                    Node(sup[supplier], x, y + 110, 200 if x == 110 else 180, 55)]
    on_view = on_view_of(d)
    # The site holds the server and the team by nesting and by placement; no aggregation lines needed.
    d.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view and r.type != "Aggregation"]

    # View 3: strategies and plans for each activity.
    s = m.view("Continuity strategies and plans", "The business impact analysis sets the recovery objectives of "
               "each prioritised activity; each activity is protected by one or more continuity strategies, and "
               "each strategy is carried out from a documented plan. An activity with no strategy, or a plan "
               "never exercised, is the gap to close first.")
    s.nodes.append(Node(control["8.2"], 20, 300, 200, 60))
    for name, y in [("Take customer orders", 100), ("Dispatch orders", 230), ("Take customer payments", 380),
                    ("Answer customer enquiries", 530)]:
        s.nodes.append(Node(act[name], 320, y, 220, 60))
    for name, y in [("Take phone orders on a manual form", 20), ("Fail over to the secondary cloud region", 120),
                    ("Switch to the standby courier", 250), ("Route payments to the secondary provider", 380),
                    ("Answer enquiries from home on the cloud service desk", 530)]:
        s.nodes.append(Node(strat[name], 650, y, 240, 60))
    for name, y in [("Website and order recovery plan", 75), ("Dispatch continuity plan", 255),
                    ("Payments continuity plan", 383), ("Customer service continuity plan", 533)]:
        s.nodes.append(Node(plan[name], 1000, y, 220, 55))
    on_view = on_view_of(s)
    s.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]

    # View 4: the impact question walked end to end.
    w = m.view("What breaks if the cloud provider fails", "The chain an impact question walks: supplier, "
               "contract, hosting service, the two applications on it, the prioritised activities they serve "
               "with their recovery objectives, and the strategy that is meant to bring them back.")
    chain = [sup["Cloud provider"], con["Cloud provider"], cloud]
    for i, el in enumerate(chain):
        w.nodes.append(Node(el, 20 + i * 230, 300, 200, 55))
    w.nodes += [Node(app["E-commerce platform"], 720, 220, 200, 55),
                Node(app["Order management system"], 720, 380, 200, 55),
                Node(act["Take customer orders"], 1000, 220, 220, 55),
                Node(act["Dispatch orders"], 1000, 380, 220, 55),
                Node(strat["Fail over to the secondary cloud region"], 1300, 290, 220, 70),
                Node(single, 250, 100, 300, 70), Node(goal, 700, 20, 300, 55)]
    on_view = on_view_of(w)
    w.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]
    return m


# ------------------------------------------------------------------------------------------------
# 8. UK Cyber Essentials: five technical control themes applied to the in-scope estate
# ------------------------------------------------------------------------------------------------

CYBER_ESSENTIALS = [
    # theme, what it requires (paraphrased from the NCSC requirements), controls: (name, estate categories)
    ("Firewalls", "Every in-scope device sits behind a correctly configured boundary or software firewall. "
     "Default administrator passwords are changed, the administration interface is not reachable from the "
     "internet without a documented need and MFA or an IP allow list, unauthenticated inbound connections "
     "are blocked by default, and every inbound rule is approved, documented with its business need and "
     "removed when no longer needed.",
     [("Boundary firewall rule management", ["Network boundary"]),
      ("Software firewalls on laptops", ["End user devices"])]),
    ("Secure configuration", "Unnecessary accounts and software are removed or disabled, default or "
     "guessable passwords are changed, auto-run is disabled, users are authenticated before reaching "
     "organisational data or services, and devices lock with a PIN, password or biometric protected "
     "against brute force.",
     [("Hardened standard builds", ["End user devices", "Servers"]),
      ("Secure cloud configuration baseline", ["Cloud services"])]),
    ("Security update management", "All software is licensed and supported, unsupported software is "
     "removed or isolated, automatic updates are on where possible, and updates fixing critical or high "
     "risk vulnerabilities (CVSS v3 7 or above, or unrated by the vendor) are applied within 14 days of "
     "release.",
     [("Security updates within 14 days", ["Network boundary", "End user devices", "Servers"]),
      ("Supported software register", ["End user devices", "Servers"])]),
    ("User access control", "Accounts are created through an approval process, use unique credentials, "
     "are removed when no longer needed and carry only the privileges the role needs. Administrative "
     "work uses separate accounts, MFA is used wherever available and is always used for cloud services, "
     "and passwords are protected against guessing.",
     [("Account lifecycle and separate admin accounts", ["Servers", "Cloud services"]),
      ("Multi-factor authentication", ["Cloud services"])]),
    ("Malware protection", "Every in-scope device runs an active, up-to-date malware protection mechanism: "
     "anti-malware software that blocks malicious code and websites, or application allow-listing that "
     "only lets approved, signed applications run.",
     [("Anti-malware on Windows and macOS", ["End user devices", "Servers"]),
      ("Application allow-listing on mobiles", ["End user devices"])]),
]

CE_ESTATE = {
    # category: [(name, type, properties)]
    "Network boundary": [
        ("Office boundary firewall", "Device", {"operating_system_or_version": "Firmware version",
                                                "supported_until": ""}),
        ("Office wireless access points", "Device", {"operating_system_or_version": "Firmware version",
                                                     "supported_until": ""}),
    ],
    "End user devices": [
        ("Office desktops", "Device", {"operating_system_or_version": "", "supported_until": ""}),
        ("Staff laptops", "Device", {"operating_system_or_version": "", "supported_until": ""}),
        ("Company mobile phones", "Device", {"operating_system_or_version": "", "supported_until": ""}),
        ("Personal phones with work email", "Device", {"operating_system_or_version": "",
                                                       "supported_until": ""}),
    ],
    "Servers": [
        ("Office file server", "Node", {"operating_system_or_version": "", "supported_until": ""}),
        ("Cloud virtual servers (IaaS)", "Node", {"cloud_service_type": "IaaS", "controls_implemented_by":
                                                  "Firewalls, secure configuration, updates and malware "
                                                  "protection: shared with the provider; user access: your organisation"}),
    ],
    "Cloud services": [
        ("Office suite and email (SaaS)", "ApplicationComponent",
         {"cloud_service_type": "SaaS", "controls_implemented_by": "Firewalls, updates and malware "
          "protection: provider; secure configuration: shared; user access: your organisation"}),
        ("Accounting system (SaaS)", "ApplicationComponent",
         {"cloud_service_type": "SaaS", "controls_implemented_by": "Firewalls, updates and malware "
          "protection: provider; secure configuration: shared; user access: your organisation"}),
        ("Client portal hosting (PaaS)", "TechnologyService",
         {"cloud_service_type": "PaaS", "controls_implemented_by": "Firewalls and malware protection: "
          "provider, sometimes shared; secure configuration and updates: shared; user access: your organisation"}),
    ],
}

CE_OUT_OF_SCOPE = [
    ("Home broadband routers not supplied by the firm", "Device",
     "Out of scope. Laptops used at home rely on their software firewall instead."),
    ("Phones used only for calls, texts and MFA apps", "Device",
     "Out of scope: devices used only for native voice, native text or MFA applications."),
    ("Bespoke code of the client portal", "Artifact",
     "Out of scope: bespoke and custom web application components. Covered by secure development practice."),
]


def cyber_essentials() -> Model:
    m = Model("cyber-essentials", "UK Cyber Essentials (starter)",
              "The five technical control themes of Cyber Essentials, the UK government-backed scheme run by "
              "the National Cyber Security Centre, each realized by example controls that are applied to the "
              "in-scope estate: network boundary, end user devices, servers and cloud services. It follows "
              "Cyber Essentials: Requirements for IT Infrastructure v3.3 (April 2026); Cyber Essentials Plus "
              "assesses the same requirements with hands-on technical verification. Requirements are "
              "paraphrased; the NCSC document is the reference. Replace the example professional services "
              "firm's estate with your own asset register: every in-scope device and cloud service needs "
              "each theme that applies to it covered by a control.")
    driver = m.el("Driver", "Cyber Essentials: Requirements for IT Infrastructure v3.3",
                  "Published by the NCSC in April 2026. Certification is awarded by a Certification Body "
                  "against an agreed scope.")
    goal = m.el("Goal", "Protection against common internet-based attacks",
                "Prevent the large majority of commodity cyber attacks: phishing, password guessing, and "
                "exploitation of known vulnerabilities and default settings.")
    m.rel("Influence", driver, goal)
    scope = m.el("Requirement", "Agreed scope boundary",
                 "The whole IT infrastructure, or a separately managed sub-set, defined by business unit, "
                 "network boundary and physical location and agreed with the Certification Body. End user "
                 "devices must be included, and cloud services that hold organisational data or services can "
                 "never be excluded.")
    m.rel("Realization", scope, goal)

    in_scope = m.el("Grouping", "In scope", "Devices and services that can accept inbound connections from "
                    "the internet, make outbound connections over it, or control data flows between the two.")
    category, estate = {}, {}
    for cat, items in CE_ESTATE.items():
        category[cat] = m.el("Grouping", cat)
        m.rel("Aggregation", in_scope, category[cat])
        for name, kind, props in items:
            estate[name] = m.el(kind, name, "", asset_owner="", **props)
            m.rel("Aggregation", category[cat], estate[name])
    out_scope = m.el("Grouping", "Out of scope", "Excluded by the scheme's scope rules. Record why each item "
                     "is out of scope; the assessor will ask.")
    outside = []
    for name, kind, doc in CE_OUT_OF_SCOPE:
        outside.append(m.el(kind, name, doc))
        m.rel("Aggregation", out_scope, outside[-1])

    themes, controls = [], []
    for theme, text, ctls in CYBER_ESSENTIALS:
        t = m.el("Requirement", theme, text)
        m.rel("Realization", t, goal)
        mine = []
        for name, applies in ctls:
            c = m.el("BusinessProcess", name, "Example control. Replace with the process or tool that meets "
                     "this theme in your organisation.", control_owner="", evidence_location="",
                     applies_to="; ".join(applies))
            m.rel("Realization", c, t)
            for cat in applies:
                m.rel("Association", c, category[cat], "applied to")
            mine.append(c)
        themes.append(t)
        controls.append(mine)

    # View 1: the five themes and the controls that realize them.
    v = m.view("Five control themes and their controls", "Each technical control theme with the example "
               "controls that realize it. Fill in the owner and evidence location of every control: the "
               "assessment questions ask for exactly this.", "Motivation")
    v.nodes += [Node(driver, 20, 20, 230, 60), Node(goal, 20, 340, 230, 70), Node(scope, 20, 640, 230, 70)]
    for i, (t, mine) in enumerate(zip(themes, controls)):
        y = 40 + i * 150
        v.nodes.append(Node(t, 340, y, 240, 70))
        v.nodes += [Node(mine[0], 680, y - 25, 260, 55), Node(mine[1], 680, y + 45, 260, 55)]
    on_view = on_view_of(v)
    v.connections += [r.id for r in m.relationships if r.source in on_view and r.target in on_view]

    # View 2: which controls apply to which part of the estate.
    order = ["Boundary firewall rule management", "Security updates within 14 days",
             "Software firewalls on laptops", "Application allow-listing on mobiles", "Hardened standard builds",
             "Anti-malware on Windows and macOS", "Supported software register",
             "Account lifecycle and separate admin accounts", "Secure cloud configuration baseline",
             "Multi-factor authentication"]
    by_name = {m.elements[c].name: c for mine in controls for c in mine}
    e = m.view("Controls applied to the in-scope estate", "Each control and the part of the estate it is "
               "applied to. Every device and cloud service in a category must be covered by the controls drawn "
               "to that category; one left out is the finding an assessor raises.")
    e.nodes += [Node(by_name[n], 20 + i * 165, 20, 150, 70) for i, n in enumerate(order)]
    # Each category sits under the controls drawn to it, so the lines stay short.
    for cat, x, cols, w in [("Network boundary", 20, 1, 230), ("End user devices", 378, 2, 200),
                            ("Servers", 920, 1, 230), ("Cloud services", 1370, 1, 230)]:
        kids = [estate[n] for n, *_ in CE_ESTATE[cat]]
        e.nodes.append(container(category[cat], x, 330, kids, cols=cols, w=w, h=50, title=cat))
    on_view = on_view_of(e)
    e.connections += [r.id for r in m.relationships
                      if r.source in on_view and r.target in on_view and r.type == "Association"]

    # View 3: the scope boundary.
    s = m.view("Scope boundary", "What the assessment covers and what it leaves out, with the reason for each "
               "exclusion recorded in the model.")
    x = 35
    boxes = []
    for cat, items in CE_ESTATE.items():
        box = container(category[cat], x, 75, [estate[n] for n, *_ in items], cols=1, w=210, h=50, title=cat)
        boxes.append(box)
        x += box.w + GAP
    tallest = max(b.h for b in boxes)
    s.nodes.append(Node(in_scope, 20, 20, x - 20 + 5, tallest + 75, boxes))
    s.nodes.append(container(out_scope, x + 30, 20, outside, cols=1, w=230, h=55, title="Out of scope"))
    s.nodes.append(Node(scope, x + 30, 20 + 32 + 3 * 70 + 40, 260, 90))
    return m


ALL = [capability_map, application_portfolio, nis2, dora, layered_onboarding, company_model, iso22301, cyber_essentials]


# ------------------------------------------------------------------------------------------------
# Spreadsheet editions for bulk import into a portfolio tool (columns follow Iyene's import fields)
# ------------------------------------------------------------------------------------------------

def capability_rows() -> list[dict[str, str]]:
    rows = []
    for i, (area, subs) in enumerate(CAPABILITIES.items(), 1):
        code = f"C{i:02d}"
        rows.append({"name": area, "code": code, "level": "1", "parent_code": "",
                     "description": f"Level 1 capability area: {area}.", "strategic_importance": "",
                     "current_maturity_level": ""})
        for j, sub in enumerate(subs, 1):
            rows.append({"name": sub, "code": f"{code}.{j:02d}", "level": "2", "parent_code": code,
                         "description": "", "strategic_importance": "", "current_maturity_level": ""})
    return rows


def application_rows() -> list[dict[str, str]]:
    model = application_portfolio()
    rows = []
    for e in model.elements.values():
        if e.type != "ApplicationComponent":
            continue
        served = [model.elements[r.target].name for r in model.relationships
                  if r.source == e.id and r.type == "Realization"]
        rows.append({"name": e.name, "type": "service", "description": e.doc,
                     "business_capabilities": "; ".join(served), "time": e.props["Time"],
                     "lifecycle": e.props["Lifecycle"], "vendor": "", "business_owner": ""})
    return rows
