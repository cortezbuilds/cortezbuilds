# Developer beliefs — working draft

## Why I build

I want to change what it means to be a mainstream developer. The old picture—a person whose value is measured by how well they translate an algorithm into code—never described me. I was never especially good at that exercise. What draws me to development is the chance to make a possible future visible, put a working piece of it in people's hands, and learn what happens.

I picture software as a field of possible timelines, almost holographic: several paths in view before one is made tangible. A small, complete slice pulls one possibility into reach and lets it meet reality. Provenance is the thread through those timelines: what we saw, what we assumed, what we chose, what we ran, and what changed. It lets us return, revise, or branch again. That is how we steer a flexible process without pretending we knew the answer all along.

Too much of what I call mainstream development feels like dev daycare: sharp people are given narrow tickets, technical puzzles, and long approval chains while the question of what anyone can do with the result is kept somewhere else. I am often mistaken for the developer who wants difficult optimizations even if they never reach a user or make any money. What excites me is a technical capability that lets people do something they did not know to ask for. I want developers to own that whole arc, from possibility to experience.

The counterexample is a rider choosing a route. A live alert about a disruption lets them change course while another route is still possible; tomorrow's perfectly validated report can only explain what happened. Real-time data turns information from a staged publication into a living account of a changing world. The backend may stream or poll; the user cares that the change reaches them in time to matter.

That experience still needs timestamps, validation, late arrivals, and corrections. Batch processing made sense under earlier constraints and still earns its place for backfills, audits, and large bounded transformations. Choosing it by habit when a user's decision has an expiry time is the unmanaged abstraction. Transforming a hundred terabytes in one heroic job is a one-rep max. Making each consequential change usable as it arrives is the fifty-pound lift done well, over and over.

I want room for people, myself included, to fuck up and recover. Irreversible actions deserve hard edges. For the rest, use fast local tests, small changes, rehearsed restores from permission-scoped backups across independent failure modes, observable deployments, and clear rollback paths. Make failure detectable, containable, and quick to rebuild from. An outage has a cost. So does a team too frightened to move. Speed is earned through recovery, small changes, and evidence, not bravado alone.


## Sources and limits

“Mainstream development” is my description of a work culture, not a research category or a judgment about every developer. The sources below speak to feedback, process, productivity, and safety; they do not establish that enterprise developers are less capable or that outages always pay for themselves. The quantum and timeline language above is an image for branching choices; the record of a choice should be grounded in ordinary, checkable evidence.

- [DORA 2019](https://dora.dev/research/2019/dora-report/) discusses speed and stability together, smaller changes, automation, and peer review.
- [DORA 2024](https://dora.dev/research/2024/dora-report/) connects unstable priorities with productivity and burnout and examines AI in software delivery.
- [The SPACE of Developer Productivity](https://www.microsoft.com/en-us/research/publication/the-space-of-developer-productivity-theres-more-to-it-than-you-think/) explains why activity alone is a poor measure of a developer's contribution.
- [Microsoft and Vista's developer survey](https://www.microsoft.com/en-us/research/wp-content/uploads/2023/05/BestOfBothWorlds.pdf#page=7) reports meetings, inefficient processes, and unclear goals among developers' reported barriers.
- [DevEx: What Actually Drives Productivity?](https://www.michaelagreiler.com/wp-content/uploads/2024/06/DevEx-WhatDrivesProductivity.pdf) frames developer experience through feedback loops, cognitive load, and flow.
- [GTFS Realtime service-alert guidance](https://gtfs.org/resources/mobilitydata-recommendations/gtfs-realtime-service-alerts/intro/) describes how trip planners can use disruption alerts to avoid suggesting affected services. The rider example above is an illustration, not a report of a particular transit system.
- [Transport for London's Unified API](https://tfl.gov.uk/info-for/open-data-users/unified-api) describes why flat-file arrival data becomes stale quickly and how a live user-facing view can combine streams and polling.
- [The Dataflow Model](https://research.google/pubs/the-dataflow-model-a-practical-approach-to-balancing-correctness-latency-and-cost-in-massive-scale-unbounded-out-of-order-data-processing/) explains the tradeoffs among correctness, latency, and cost when data can arrive late or be revised.
- [Apache Flink's batch and streaming execution guidance](https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/datastream/execution_mode/) distinguishes continuous unbounded work from bounded jobs where batch optimizations remain useful.
