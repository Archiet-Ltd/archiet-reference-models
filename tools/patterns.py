"""Cloud and SaaS architecture patterns, vendor-neutral. Run build.py to regenerate them."""

from __future__ import annotations

from oef import Model, Node
from models import on_view_of

W, H = 180, 55


def put(view, placements) -> None:
    """Place elements on a view: (element, x, y) or (element, x, y, w, h) or a ready Node."""
    for p in placements:
        view.nodes.append(p if isinstance(p, Node) else Node(p[0], p[1], p[2], *(p[3:] or (W, H))))


def connect(m: Model, view, skip: tuple[str, ...] = ("Aggregation", "Composition")) -> None:
    on_view = on_view_of(view)
    view.connections += [r.id for r in m.relationships
                         if r.source in on_view and r.target in on_view and r.type not in skip]


def group(m: Model, view, grouping: str, x: int, y: int, w: int, members: list[str], cols: int = 1,
          h: int = H) -> None:
    """A dashed grouping box holding its members, which it aggregates."""
    rows = (len(members) + cols - 1) // cols
    inner_w = (w - 20 * (cols + 1)) // cols
    children = [Node(e, x + 20 + (i % cols) * (inner_w + 20), y + 38 + (i // cols) * (h + 15), inner_w, h)
                for i, e in enumerate(members)]
    for e in members:
        m.rel("Aggregation", grouping, e)
    view.nodes.append(Node(grouping, x, y, w, 38 + rows * (h + 15) + 5, children))


# ------------------------------------------------------------------------------------------------
# 1. Multi-tenant SaaS
# ------------------------------------------------------------------------------------------------

def multi_tenant_saas() -> Model:
    m = Model("multi-tenant-saas", "Multi-Tenant SaaS",
              "One application serving many customer organisations (tenants) from shared infrastructure, "
              "with tenant isolation enforced in the data layer. Standard tenants share a pooled database "
              "protected by row-level security; premium or regulated tenants get a dedicated database. The "
              "tenant catalog records where every tenant lives, so the same code serves both.")
    users = m.el("BusinessActor", "Tenant users", "People from many customer organisations using one product.")
    identity = m.el("ApplicationComponent", "Identity and tenant resolution",
                    "Signs users in and stamps every token with the tenant it belongs to. Nothing downstream "
                    "trusts a tenant id from the request body.")
    gateway = m.el("ApplicationComponent", "API gateway",
                   "Single entry point. Validates the token, applies per-tenant rate limits so one noisy "
                   "tenant cannot starve the rest, and passes tenant context on.")
    admin = m.el("ApplicationComponent", "Tenant administration and billing",
                 "Sign-up, plans, seats and usage metering per tenant.")
    app = m.el("ApplicationComponent", "Application services",
               "Stateless business logic. Every call carries tenant context; no service holds tenant state.")
    workers = m.el("ApplicationComponent", "Background workers",
                   "Asynchronous jobs, queued per tenant so one tenant's backlog does not delay another's.")
    dal = m.el("ApplicationComponent", "Tenant-aware data access",
               "The one place tenant isolation is enforced: sets the tenant on every connection and routes "
               "each tenant to its pooled or dedicated store using the tenant catalog.")
    platform = m.el("Node", "Container platform", "Runs the stateless services and scales them horizontally.")
    dbsvc = m.el("TechnologyService", "Managed relational database")
    queue = m.el("TechnologyService", "Message queue")
    pooled = m.el("Grouping", "Standard tenants: pooled")
    silo = m.el("Grouping", "Premium tenants: dedicated")
    shared = m.el("DataObject", "Shared database with row-level security",
                  "Every row carries a tenant id and the database itself refuses cross-tenant reads.")
    dedicated = m.el("DataObject", "Dedicated tenant database",
                     "One database per tenant, for data residency, contractual isolation or very large tenants.")
    catalog = m.el("DataObject", "Tenant catalog", "Tenant, plan, region and which store holds its data.")

    m.rel("Serving", gateway, users)
    m.rel("Serving", identity, gateway)
    m.rel("Serving", gateway, admin)
    m.rel("Serving", gateway, app)
    m.rel("Serving", dal, app)
    m.rel("Serving", dal, workers)
    m.rel("Serving", queue, app)
    m.rel("Serving", queue, workers)
    m.rel("Serving", platform, app)
    m.rel("Serving", dbsvc, dal)
    for d in (shared, dedicated, catalog):
        m.rel("Access", dal, d, access="ReadWrite")
    m.rel("Access", admin, catalog, access="ReadWrite")

    v = m.view("Multi-tenant SaaS", "Tenant context flows from the token through every layer; isolation is "
               "enforced once, in the data access layer.")
    put(v, [(users, 300, 20), (identity, 20, 140), (gateway, 300, 140), (admin, 860, 140),
             (platform, 20, 270), (app, 300, 270), (queue, 580, 270),
             (dbsvc, 20, 400), (dal, 300, 400), (workers, 580, 400), (catalog, 860, 530)])
    group(m, v, pooled, 20, 530, 300, [shared])
    group(m, v, silo, 360, 530, 300, [dedicated])
    connect(m, v)
    m.guide = {
        "use": ["You sell one product to many organisations and need each one's data kept apart.",
                "You want the cost profile of shared infrastructure, with an upgrade path to dedicated "
                "isolation for customers who pay or are required to have it."],
        "tradeoffs": ["Pooled tenants are cheap to run but a defect in isolation exposes everyone, so "
                      "isolation lives in one component and the database enforces it as well.",
                      "Dedicated databases are simple to reason about but multiply migrations, backups and "
                      "monitoring by the number of tenants.",
                      "Per-tenant rate limits and queues are what stop one busy customer slowing all others."],
        "ifiok": "Describe your product and its tenancy rules in a spec, and Ifiok generates the services, "
                 "tenant-aware data layer and APIs in the stack you choose.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 2. Event-driven architecture
# ------------------------------------------------------------------------------------------------

def event_driven() -> Model:
    m = Model("event-driven", "Event-Driven Architecture",
              "Services announce what happened as events and other services react, instead of calling each "
              "other directly. The producer writes the event to an outbox in the same transaction as its own "
              "data, so an event is never lost and never published for a change that did not happen.")
    order_svc = m.el("ApplicationComponent", "Order service")
    place = m.el("ApplicationProcess", "Place order")
    outbox = m.el("DataObject", "Outbox", "Written in the same database transaction as the order; a relay "
                  "publishes from it to the event stream.")
    event = m.el("ApplicationEvent", "Order placed")
    payload = m.el("DataObject", "Order placed event (versioned schema)",
                   "Consumers depend on the schema, not on the producer. Additive changes only; breaking "
                   "changes get a new version.")
    m.rel("Assignment", order_svc, place)
    m.rel("Access", place, outbox, access="Write")
    m.rel("Triggering", place, event)
    m.rel("Access", event, payload)
    consumers = [("Inventory service", "Reserve stock"), ("Notification service", "Send confirmation"),
                 ("Analytics service", "Update sales figures")]
    comps, procs = [], []
    for comp_name, proc_name in consumers:
        c = m.el("ApplicationComponent", comp_name)
        p = m.el("ApplicationProcess", proc_name, "Idempotent: processing the same event twice has no "
                 "further effect, because delivery is at least once.")
        m.rel("Assignment", c, p)
        m.rel("Triggering", event, p)
        comps.append(c)
        procs.append(p)

    v = m.view("Event flow", "One business event, published once, handled independently by every service "
               "that cares about it.")
    put(v, [(order_svc, 20, 20), (place, 20, 150), (outbox, 20, 280), (event, 300, 150), (payload, 300, 280)])
    for i, (c, p) in enumerate(zip(comps, procs)):
        put(v, [(p, 580, 20 + i * 130), (c, 860, 20 + i * 130)])
    connect(m, v)

    stream = m.el("TechnologyService", "Event streaming", "Durable, ordered, replayable event log.")
    broker = m.el("Node", "Broker cluster")
    dlq = m.el("Artifact", "Dead-letter queue", "Events a consumer could not process, kept for inspection "
               "and replay instead of blocking the stream.")
    m.rel("Realization", broker, stream)
    for c in [order_svc, *comps]:
        m.rel("Serving", stream, c)
    m.rel("Access", stream, dlq)
    r = m.view("Runtime platform", "Every service connects to one event streaming service; none connects "
               "to another directly.")
    put(r, [(order_svc, 20, 20), *[(c, 260 + i * 240, 20) for i, c in enumerate(comps)],
            (stream, 380, 160), (broker, 380, 290), (dlq, 700, 290)])
    connect(m, r)
    m.guide = {
        "use": ["Several services need to react to the same business change.",
                "You want teams to add new consumers without changing the producer.",
                "You need an auditable, replayable history of what happened."],
        "tradeoffs": ["Consistency becomes eventual: the inventory is reserved shortly after the order, not "
                      "in the same transaction. Design the user experience for that.",
                      "Delivery is at least once, so every consumer must be idempotent.",
                      "Flows are harder to follow than direct calls; trace ids on every event are not "
                      "optional."],
        "ifiok": "Specify your entities and the events between them, and Ifiok generates the producers, "
                 "consumers and outbox handling in the stack you choose.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 3. API gateway and microservices
# ------------------------------------------------------------------------------------------------

def microservices() -> Model:
    m = Model("api-gateway-microservices", "API Gateway and Microservices",
              "A product split into independently deployable services, each owning its own data, behind one "
              "API gateway. Clients see a single API; teams ship their service without coordinating a "
              "release with everyone else.")
    customers = m.el("BusinessActor", "Customers")
    web = m.el("ApplicationComponent", "Web front end")
    mobile = m.el("ApplicationComponent", "Mobile app")
    gateway = m.el("ApplicationComponent", "API gateway", "Routing, authentication, rate limiting and request "
                   "shaping for each client. No business logic.")
    idp = m.el("ApplicationComponent", "Identity provider")
    services = ["Catalogue service", "Order service", "Payment service", "Customer account service"]
    stores = ["Catalogue database", "Order database", "Payment ledger", "Customer database"]
    svc_ids, db_ids = [], []
    for s, d in zip(services, stores):
        sid = m.el("ApplicationComponent", s)
        did = m.el("DataObject", d, "Owned by one service. Other services ask that service; they never read "
                   "its database.")
        m.rel("Access", sid, did)
        m.rel("Serving", sid, gateway)
        svc_ids.append(sid)
        db_ids.append(did)
    m.rel("Serving", web, customers)
    m.rel("Serving", mobile, customers)
    m.rel("Serving", gateway, web)
    m.rel("Serving", gateway, mobile)
    m.rel("Serving", idp, gateway)
    m.rel("Serving", svc_ids[2], svc_ids[1])

    v = m.view("Services behind one gateway", "Each service owns its data; the gateway is the only way in.")
    put(v, [(customers, 380, 20), (web, 200, 130), (mobile, 560, 130), (gateway, 380, 250), (idp, 760, 250)])
    for i, (s, d) in enumerate(zip(svc_ids, db_ids)):
        put(v, [(s, 20 + i * 240, 380), (d, 20 + i * 240, 500)])
    connect(m, v)
    m.guide = {
        "use": ["Several teams work on one product and are slowed by a shared release.",
                "Parts of the product have very different scaling or reliability needs."],
        "tradeoffs": ["Every network hop adds latency and a new way to fail; budget for timeouts, retries "
                      "and tracing from the first service.",
                      "Data owned per service means reports and joins across services need their own design, "
                      "usually events into a reporting store.",
                      "A small team with one product is usually faster with a well-structured single "
                      "application; split when the organisation, not the code, demands it."],
        "ifiok": "Ifiok generates each service from one specification, so the boundaries, contracts and "
                 "gateway routes stay consistent when you change the design.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 4. Serverless web application
# ------------------------------------------------------------------------------------------------

def serverless() -> Model:
    m = Model("serverless-web-app", "Serverless Web Application",
              "A web application with no servers to manage: static front end on a content delivery network, "
              "an HTTP API backed by functions, and managed data stores. You pay for requests, not idle "
              "capacity.")
    users = m.el("BusinessActor", "Users")
    cdn = m.el("TechnologyService", "Content delivery network")
    bundle = m.el("Artifact", "Web app bundle", "Static HTML, JavaScript and assets.")
    api = m.el("ApplicationComponent", "HTTP API", "Managed API endpoint that authenticates requests and "
               "invokes functions.")
    orders_fn = m.el("ApplicationComponent", "Order functions", "One small function per operation.")
    image_fn = m.el("ApplicationComponent", "Image processing function",
                    "Runs when a file lands in object storage, not when a user waits.")
    runtime = m.el("TechnologyService", "Function runtime")
    orders = m.el("DataObject", "Orders table", "Managed key-value store, designed around access patterns.")
    images = m.el("DataObject", "Uploaded images", "Object storage.")
    m.rel("Serving", cdn, users)
    m.rel("Access", cdn, bundle, access="Read")
    m.rel("Serving", api, users)
    m.rel("Serving", orders_fn, api)
    m.rel("Serving", runtime, orders_fn)
    m.rel("Serving", runtime, image_fn)
    m.rel("Access", orders_fn, orders)
    m.rel("Access", image_fn, images)

    v = m.view("Serverless web application", "Static front end, functions behind an API, managed storage.")
    put(v, [(users, 260, 20), (cdn, 20, 140), (api, 260, 140), (bundle, 20, 270), (orders_fn, 260, 270),
            (runtime, 470, 270, 150, H), (image_fn, 660, 270), (orders, 260, 400), (images, 660, 400)])
    connect(m, v)
    m.guide = {
        "use": ["Traffic is spiky or unpredictable and idle capacity would be wasted.",
                "A small team wants to ship without running servers."],
        "tradeoffs": ["Cold starts add latency to the first request after a quiet period.",
                      "Cost per request is low but grows linearly; at high steady load, containers are often "
                      "cheaper.",
                      "Each function is simple; the system of many functions needs the same tracing and "
                      "deployment discipline as microservices."],
        "ifiok": "Ifiok generates the API and its handlers from your specification in the stack you choose, "
                 "ready to deploy behind a managed API.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 5. Modern data platform
# ------------------------------------------------------------------------------------------------

def data_platform() -> Model:
    m = Model("data-platform", "Modern Data Platform",
              "Operational data flows in from source systems, lands unchanged in a raw zone, is cleaned and "
              "modelled into a curated zone, and is served through one semantic layer so every report uses "
              "the same definitions. A catalog records where every dataset came from.")
    sources = [m.el("ApplicationComponent", n) for n in ["CRM", "ERP", "Product event stream"]]
    ingest = m.el("ApplicationComponent", "Ingestion pipelines", "Copies source data in on a schedule or as a "
                  "stream, without changing it.")
    raw = m.el("DataObject", "Raw zone", "Source data exactly as received, kept so any result can be rebuilt.")
    transform = m.el("ApplicationComponent", "Transformation jobs", "Tested, version-controlled models that "
                     "clean, join and conform the data.")
    curated = m.el("DataObject", "Curated zone", "Conformed, documented tables that people may rely on.")
    semantic = m.el("ApplicationComponent", "Semantic layer", "One definition of revenue, customer and churn "
                    "for every tool.")
    bi = m.el("ApplicationComponent", "Dashboards and reports")
    ml = m.el("ApplicationComponent", "Machine learning")
    catalog = m.el("ApplicationComponent", "Data catalog and lineage", "Who owns each dataset, where it came "
                   "from and what depends on it.")
    for s in sources:
        m.rel("Flow", s, ingest)
    m.rel("Access", ingest, raw, access="Write")
    m.rel("Flow", ingest, transform)
    m.rel("Access", transform, raw, access="Read")
    m.rel("Access", transform, curated, access="Write")
    m.rel("Access", semantic, curated, access="Read")
    m.rel("Serving", semantic, bi)
    m.rel("Access", ml, curated, access="Read")
    m.rel("Serving", catalog, ingest)
    m.rel("Access", catalog, curated, access="Read")

    v = m.view("Data platform", "Sources to raw to curated to one semantic layer, with lineage throughout.")
    put(v, [(sources[0], 20, 20), (sources[1], 20, 130), (sources[2], 20, 240), (ingest, 280, 130),
            (raw, 540, 20), (transform, 540, 130), (curated, 540, 240), (semantic, 800, 240), (bi, 1060, 240),
            (ml, 800, 360), (catalog, 280, 360)])
    connect(m, v)
    m.guide = {
        "use": ["Reports disagree because each one calculates the same figure its own way.",
                "Analysts and machine learning need the same trusted data."],
        "tradeoffs": ["Keeping raw data costs storage but makes every result reproducible.",
                      "A semantic layer is extra work up front and the only lasting fix for conflicting "
                      "numbers.",
                      "Without named owners in the catalog, curated data decays back into raw data."],
        "ifiok": "Ifiok generates the operational applications whose data feeds this platform, with the "
                 "entities and events defined once in the specification.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 6. Zero-trust access
# ------------------------------------------------------------------------------------------------

def zero_trust() -> Model:
    m = Model("zero-trust-access", "Zero-Trust Access",
              "No request is trusted because of where it comes from. Every request to an internal application "
              "passes an access proxy, which asks a policy engine to decide using the user's identity, the "
              "health of their device and the sensitivity of the application, every time.")
    user = m.el("BusinessActor", "Employee or contractor")
    device = m.el("Device", "Managed device")
    proxy = m.el("ApplicationComponent", "Access proxy", "Policy enforcement point: the only route to "
                 "internal applications.")
    apps = m.el("ApplicationComponent", "Internal applications", "Not reachable from the network directly.")
    pdp = m.el("ApplicationComponent", "Policy engine", "Policy decision point: allows, denies or asks for "
               "step-up authentication, per request.")
    idp = m.el("ApplicationComponent", "Identity provider", "Strong, phishing-resistant multi-factor "
               "authentication.")
    posture = m.el("ApplicationComponent", "Device posture service", "Is the device managed, patched and "
                   "encrypted right now?")
    siem = m.el("ApplicationComponent", "Security monitoring", "Every decision is logged and analysed.")
    principles = m.el("Grouping", "Principles")
    ps = [m.el("Principle", n) for n in ["Never trust the network", "Verify every request",
                                          "Least privilege, granted just in time"]]
    m.rel("Association", user, device)
    m.rel("Serving", proxy, user)
    m.rel("Serving", apps, proxy)
    m.rel("Serving", pdp, proxy)
    m.rel("Serving", idp, pdp)
    m.rel("Serving", posture, pdp)
    m.rel("Association", posture, device)
    m.rel("Flow", pdp, siem)

    v = m.view("Zero-trust access", "Identity, device and policy decide every request; the network decides "
               "nothing.")
    put(v, [(user, 20, 20), (device, 20, 140), (proxy, 300, 20), (apps, 580, 20), (posture, 20, 260),
            (pdp, 300, 260), (idp, 580, 260), (siem, 300, 390)])
    group(m, v, principles, 580, 380, 420, ps, cols=1, h=40)
    connect(m, v)
    m.guide = {
        "use": ["Staff work from anywhere and a VPN grants far more access than any one person needs.",
                "You must show auditors who accessed what, from which device, and why it was allowed."],
        "tradeoffs": ["Policies need owners; a policy engine nobody maintains drifts back to allow-all.",
                      "Device posture checks need managed devices, which is a rollout of its own.",
                      "Moving application by application behind the proxy is slower than a big switch and "
                      "far safer."],
        "ifiok": "Applications Ifiok generates take identity from a token on every request, so they sit "
                 "behind an access proxy without changes.",
    }
    return m


# ------------------------------------------------------------------------------------------------
# 7. Multi-region resilience
# ------------------------------------------------------------------------------------------------

def multi_region() -> Model:
    m = Model("multi-region-resilience", "Multi-Region Resilience (active-passive)",
              "The application runs in a primary region with a warm standby in a second region. The database "
              "replicates continuously; if the primary region fails, traffic routing moves users to the "
              "standby. Recovery time and recovery point are stated as requirements and tested.")
    users = m.el("BusinessActor", "Users")
    routing = m.el("TechnologyService", "Global traffic routing", "Health-checked DNS or anycast that sends "
                   "users to the healthy region.")
    region_a = m.el("Location", "Region A (primary)")
    region_b = m.el("Location", "Region B (standby)")
    app_a = m.el("Node", "Application cluster A")
    db_a = m.el("Node", "Primary database")
    app_b = m.el("Node", "Application cluster B", "Running at reduced size; scales up on failover.")
    db_b = m.el("Node", "Standby database", "Continuously replicated replica, promoted on failover.")
    rto = m.el("Requirement", "Recovery time objective: 15 minutes")
    rpo = m.el("Requirement", "Recovery point objective: under 1 minute of data")
    m.rel("Serving", routing, users)
    m.rel("Serving", routing, app_a)
    m.rel("Serving", routing, app_b)
    m.rel("Serving", db_a, app_a)
    m.rel("Serving", db_b, app_b)
    m.rel("Flow", db_a, db_b, name="replication")
    m.rel("Realization", routing, rto)
    m.rel("Realization", db_b, rpo)
    for loc, members in ((region_a, (app_a, db_a)), (region_b, (app_b, db_b))):
        for e in members:
            m.rel("Aggregation", loc, e)

    v = m.view("Two regions, one standby", "Continuous replication to a standby region, with traffic routing "
               "that fails over when the primary is unhealthy.")
    put(v, [(users, 400, 20), (routing, 400, 130), (rto, 760, 130),
            Node(region_a, 20, 250, 300, 260, [Node(app_a, 80, 300, W, H), Node(db_a, 80, 420, W, H)]),
            Node(region_b, 560, 250, 300, 260, [Node(app_b, 620, 300, W, H), Node(db_b, 620, 420, W, H)]),
            (rpo, 590, 570, 240, 55)])
    connect(m, v)
    m.guide = {
        "use": ["An outage of one cloud region would cost more than running a standby.",
                "Regulators or customers require a tested recovery plan with stated recovery times."],
        "tradeoffs": ["Active-passive is simpler and cheaper; active-active removes failover time but needs "
                      "conflict handling for writes in two places.",
                      "Asynchronous replication means the last seconds of writes can be lost; that number is "
                      "your recovery point.",
                      "A failover that has never been rehearsed will not work on the day. Test it on a "
                      "schedule."],
        "ifiok": "Ifiok generates stateless application code, which is what lets a standby region take over "
                 "without code changes.",
    }
    return m


PATTERNS = [multi_tenant_saas, event_driven, microservices, serverless, data_platform, zero_trust, multi_region]
