// Notes are placeholder-only for now (no backend / storage yet). When the
// notes API lands, replace this static list with a fetch and wire the admin
// upload in Notes.jsx to a real endpoint.
export const NOTE_SUBJECTS = [
  {
    id: "oops",
    label: "OOPS",
    blurb: "3rd sem — classes, inheritance, polymorphism, templates.",
    units: [
      "Unit 1 — OOP fundamentals, classes & objects",
      "Unit 2 — Constructors, destructors & polymorphism",
      "Unit 3 — Inheritance, pointers & virtual functions",
      "Unit 4 — Exceptions, templates & file handling",
    ],
  },
  {
    id: "os",
    label: "Operating Systems",
    blurb: "4th sem — processes, scheduling, deadlocks, memory, disk.",
    units: [
      "Unit 1 — Introduction to operating systems",
      "Unit 2 — Processes, scheduling & synchronization",
      "Unit 3 — Deadlocks & memory management",
      "Unit 4 — File systems & disk management",
    ],
  },
  {
    id: "cn",
    label: "Computer Networks",
    blurb: "OSI/TCP-IP, routing, transport, application protocols.",
    units: [
      "Unit 1 — Network models & physical layer",
      "Unit 2 — Data link layer & MAC",
      "Unit 3 — Network layer & routing",
      "Unit 4 — Transport layer (TCP/UDP)",
      "Unit 5 — Application layer protocols",
    ],
  },
  {
    id: "dbms",
    label: "DBMS",
    blurb: "ER model, SQL, normalization, transactions & concurrency.",
    units: [
      "Unit 1 — Introduction & ER model",
      "Unit 2 — Relational model & SQL",
      "Unit 3 — Normalization",
      "Unit 4 — Transactions & concurrency control",
    ],
  },
  {
    id: "se",
    label: "Software Engineering",
    blurb: "SDLC, process models, requirements, testing, management.",
    units: [
      "Unit 1 — Software process models",
      "Unit 2 — Requirements engineering",
      "Unit 3 — Design & architecture",
      "Unit 4 — Testing & project management",
    ],
  },
  {
    id: "dsa",
    label: "DSA Handwritten",
    blurb: "Arrays to graphs — quick-revision handwritten notes.",
    units: [
      "Arrays, strings & two pointers",
      "Linked lists, stacks & queues",
      "Recursion & backtracking",
      "Trees & binary search trees",
      "Graphs & shortest paths",
      "Dynamic programming",
    ],
  },
];
