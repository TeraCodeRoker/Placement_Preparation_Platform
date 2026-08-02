// The `topic` string is what the MCQ backend expects (it interpolates it into
// the Gemini prompt). Labels/blurbs are for the UI only.
export const SUBJECTS = [
  {
    id: "oops",
    label: "OOPS",
    topic: "Object Oriented Programming",
    blurb: "Encapsulation, inheritance, polymorphism, constructors, virtual functions.",
  },
  {
    id: "os",
    label: "Operating Systems",
    topic: "Operating Systems",
    blurb: "Processes, scheduling, synchronization, deadlocks, memory & paging.",
  },
  {
    id: "cn",
    label: "Computer Networks",
    topic: "Computer Networks",
    blurb: "OSI/TCP-IP, routing, transport, addressing, application protocols.",
  },
  {
    id: "dbms",
    label: "DBMS",
    topic: "Database Management Systems",
    blurb: "ER model, SQL, joins, normalization, transactions, indexing.",
  },
];

export const DIFFICULTIES = [
  { id: "easy", label: "Easy" },
  { id: "medium", label: "Medium" },
  { id: "hard", label: "Hard" },
  { id: "mixed", label: "Mixed" },
];

export const QUESTION_COUNTS = [5, 10, 15, 20];
