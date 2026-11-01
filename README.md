# Archiet Reference Models

Free, standards-based enterprise architecture starter models. Each one is a complete ArchiMate 3.2
model you can open in your modelling tool, adapt to your organisation and use the same day.

Every model ships in the ArchiMate Model Exchange File Format (Open Exchange), and is validated
against The Open Group's published schema. It comes with diagram previews and, where it helps, a
spreadsheet edition for bulk import.

From [Archiet](https://archiet.ai), the Architecture Intelligence Platform.

## The models

| Model | What it gives you | Views |
|---|---|---|
| [Business Capability Map](models/capability-map) | 8 capability areas and 35 capabilities for a services business, plus an "Acquire to Retain" value stream showing which capabilities serve each stage. Each capability carries strategic importance and maturity fields ready to score. | Capability map; value stream and supporting capabilities |
| [Application Portfolio](models/application-portfolio) | 12 example applications mapped to the capabilities they support, each with TIME classification (Tolerate, Invest, Migrate, Eliminate), lifecycle, owner and run cost. Applications that support nothing show up on their own. | Applications by capability; TIME quadrants |
| [NIS2 Measures and Controls](models/nis2-measures) | The ten cybersecurity risk-management measures of NIS2 Article 21(2), each realized by an example control. Also covers Article 20 management-body duties and Article 23 incident reporting (24 hours, 72 hours, one month). | NIS2 measures and controls |
| [DORA ICT Third-Party Map](models/dora-ict-map) | Critical functions traced to the applications, ICT services, contracts and providers behind them, and on to the subcontractors behind each provider: the chain DORA's register of information (Article 28(3)) and exit strategies (Article 28(8)) ask for. Each subcontractor carries the register's supply-chain fields (rank, recipient of sub-contracted ICT services, LEI, country, ICT service type, substitutability) and the date the provider last confirmed it, and a data centre operator shared by both chains shows the concentration risk that only the subcontracting layer reveals. | Critical functions and ICT third parties; ICT subcontracting chain; DORA requirement areas |
| [Layered Customer Onboarding](models/layered-customer-onboarding) | One end-to-end example from business process through application services and components down to the technology they run on. A clear teaching model for how ArchiMate's layers connect. | Business to technology |
| [One Company, End to End](models/company-model) | A small subscription business modelled whole: goal, capabilities, applications, owners, costs, suppliers, contracts and the risk that matters most. Built so impact questions have answers: what breaks if a supplier fails, and who has to act. | The company on one page; who owns what; what breaks if the billing vendor fails |
| [ISO 22301 Business Continuity](models/iso22301-business-continuity) | The business continuity management system of ISO 22301 by clause (4 to 10, with clause 8 opened into its six operational subclauses), each realized by an example control. An example online retailer's prioritised activities carry their recovery time objective, maximum tolerable period of disruption, recovery point objective and minimum business continuity objective, and link to the applications, sites, people and suppliers they depend on and to the strategies and plans that protect them, so what stops when a system or supplier fails has an answer. | BCMS requirements by clause; prioritised activities and their dependencies; continuity strategies and plans; what breaks if the cloud provider fails |
| [UK Cyber Essentials](models/cyber-essentials) | The five technical control themes of the NCSC's Requirements for IT Infrastructure (firewalls, secure configuration, security update management, user access control and malware protection), each realized by example controls applied to the in-scope estate: network boundary, end user devices, servers and cloud services. Cloud services record whether each control is implemented by you, the provider or both, and the scope view shows what is out of scope and why. | Five control themes and their controls; controls applied to the in-scope estate; scope boundary |
| [EU AI Act with ISO/IEC 42001](models/eu-ai-act-iso42001) | An AI system inventory sorted into the AI Act's risk tiers (prohibited, high-risk, limited risk, minimal risk and general-purpose AI models), each system recording the organisation's role as provider, deployer or both and the basis for its classification. The provider and deployer obligations follow article by article (Articles 5, 9 to 15, 17, 26, 27, 50, 53, 72 and 73), each traced to the ISO/IEC 42001 clause process or Annex A control area that meets it. | AI system inventory and risk classification; AI Act obligations and ISO 42001 controls; ISO 42001 AI management system |

## Cloud and SaaS architecture patterns

Vendor-neutral patterns for the systems most teams are building now. Each comes with its model, its
diagrams, when to use it and the trade-offs that decide whether it is right for you.

| Pattern | The problem it solves |
|---|---|
| [Multi-Tenant SaaS](patterns/multi-tenant-saas) | Serve many customer organisations from one product, with pooled and dedicated isolation tiers. |
| [Event-Driven Architecture](patterns/event-driven) | Let services react to business events without calling each other, with no lost or phantom events. |
| [API Gateway and Microservices](patterns/api-gateway-microservices) | Split a product into independently deployable services that each own their data. |
| [Serverless Web Application](patterns/serverless-web-app) | Run a web application with no servers to manage and no idle capacity to pay for. |
| [Modern Data Platform](patterns/data-platform) | Give every report and model the same trusted numbers, with lineage back to the source. |
| [Zero-Trust Access](patterns/zero-trust-access) | Decide every request on identity, device and policy instead of network location. |
| [Multi-Region Resilience](patterns/multi-region-resilience) | Survive the loss of a cloud region within stated recovery time and recovery point. |

## Use them with

**Archi, Sparx Enterprise Architect, BiZZdesign and other ArchiMate tools.** Import the `.xml` file
from any model folder using the tool's Open Exchange import. Elements, relationships, properties,
folders and diagrams all come across.

**[Iyene](https://archiet.ai)**, Archiet's application portfolio and capability intelligence.
The capability map and the application portfolio each have a spreadsheet edition (`.csv`) laid out
for Iyene's bulk import. Capabilities keep their hierarchy through parent codes. Each application
row lists the capabilities it supports, ready for mapping in Iyene's capability view. Iyene then
works out TIME classifications for your real portfolio.

**[Entelim](https://entelim.org)**, the open-source company brain. Import any model through
Architecture, Import. Entelim builds a connected graph from it that you can query and explore. The
"One Company, End to End" model is designed for exactly this: replace the example company with your
own and every question about cost, ownership and impact has a path to follow.

**[Etione](https://archiet.ai)**, Archiet's AI modelling studio. Use the diagrams here as the starting
point for your own views in ArchiMate, C4, UML or BPMN.

**[Ifiok](https://ifiok.archiet.ai)**, which turns a specification into production code. Once the
architecture is agreed, Ifiok builds it.

## Make them yours

1. Pick the model closest to your question.
2. Rename the example elements to your own and delete what does not apply.
3. Fill in the properties: owner, cost, maturity, evidence location. These are what make a model
   answer questions instead of just drawing boxes.
4. Keep it current. A model that is six months stale gets ignored; one that is maintained becomes the
   place decisions are made.

## What is inside each folder

- `<model>.xml`: the model in Open Exchange format.
- `*.svg`: a preview of each diagram.
- `<model>.csv`: the spreadsheet edition, where there is one.

## Build from source

The models are generated by a small Python toolkit in `tools/`, so they stay consistent and every
relationship is checked against the ArchiMate 3.2 rules before it is written.

```
pip install lxml
python tools/build.py
```

The build writes every model, validates each one against the Open Exchange schema and redraws the
previews.

## Contributing

Corrections and new models are welcome. Open an issue describing the model or the fix. A good new
model answers one real question an architect gets asked, and stays small enough to adapt in an
afternoon.

## Licence

The models and previews are licensed under
[Creative Commons Attribution 4.0](https://creativecommons.org/licenses/by/4.0/). The build toolkit
is licensed under the MIT licence. The ArchiMate exchange schemas in `tools/xsd` belong to The Open
Group and are included unchanged so the build can validate offline.

ArchiMate is a registered trademark of The Open Group.
