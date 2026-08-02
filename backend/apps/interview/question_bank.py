# ai-service/question_bank.py
"""
Question bank for the AI Mock Interview.

SYLLABUS_SUBJECTS -> subjective/conceptual topics taken from the
B.Tech CSE 3rd & 4th semester syllabus PDFs:
  - 3rd Sem : Object Oriented Programming
  - 4th Sem : Operating Systems, DBMS, Computer Networks, Software Engineering

STRIVER_A2Z -> DSA problems referenced from Striver's A2Z DSA sheet,
organised step-wise the same way the sheet is.

The interview router randomly samples (subject -> unit -> topic) for
subjective questions and (step -> problem) for DSA questions, then asks
Gemini to frame the actual interview question around that topic.
"""

# ---------------------------------------------------------------------------
# CORE CS SUBJECTS (from 3rd & 4th sem syllabus PDFs)
# ---------------------------------------------------------------------------

SYLLABUS_SUBJECTS = {
    "Object Oriented Programming": {
        "source": "CSE 3rd Sem Syllabus",
        "units": {
            "Unit 1 - OOP Fundamentals, Classes & Objects": [
                "Procedural vs Object Oriented programming paradigms",
                "Characteristics of OOP: abstraction, encapsulation, inheritance, polymorphism",
                "Data hiding and access specifiers (private, public, protected)",
                "Classes and objects: defining classes, member functions, arrays of objects",
                "Static data members and static member functions",
                "Friend functions and friend classes",
            ],
            "Unit 2 - Constructors, Destructors & Polymorphism": [
                "Constructors: default, parameterized and copy constructors",
                "Constructor overloading and destructors",
                "Shallow copy vs deep copy",
                "Function overloading and compile-time polymorphism",
                "Operator overloading: rules, unary and binary operators",
                "Type conversion between basic and user-defined types",
            ],
            "Unit 3 - Inheritance, Pointers & Virtual Functions": [
                "Types of inheritance: single, multiple, multilevel, hierarchical, hybrid",
                "Diamond problem and virtual base classes",
                "Order of constructor and destructor calls in derived classes",
                "this pointer and pointers to objects",
                "Virtual functions and runtime polymorphism (dynamic binding)",
                "Pure virtual functions and abstract classes",
            ],
            "Unit 4 - Exception Handling, Templates & File Handling": [
                "Exception handling: try, catch, throw, multiple catch blocks",
                "Rethrowing exceptions and catch-all handlers",
                "Function templates and class templates (generic programming)",
                "File streams: ifstream, ofstream, fstream and file modes",
                "Reading and writing objects to files",
                "Interfaces vs abstract classes (Java perspective)",
            ],
        },
    },
    "Operating Systems": {
        "source": "CSE 4th Sem Syllabus",
        "units": {
            "Unit 1 - Introduction to OS": [
                "Functions and services of an operating system",
                "Types of OS: batch, multiprogramming, time-sharing, real-time, distributed",
                "OS structures: monolithic, layered, microkernel",
                "System calls and their types",
                "User mode vs kernel mode",
            ],
            "Unit 2 - Processes, Scheduling & Synchronization": [
                "Process concept, process states and the Process Control Block (PCB)",
                "Context switching",
                "Threads: user-level vs kernel-level, benefits of multithreading",
                "CPU scheduling criteria and algorithms: FCFS, SJF, SRTF, Round Robin, Priority",
                "Critical section problem and Peterson's solution",
                "Semaphores, mutex locks and monitors",
                "Classical problems: producer-consumer, readers-writers, dining philosophers",
            ],
            "Unit 3 - Deadlocks & Memory Management": [
                "Necessary conditions for deadlock and resource allocation graph",
                "Deadlock prevention, avoidance (Banker's algorithm), detection and recovery",
                "Contiguous memory allocation, internal and external fragmentation",
                "Paging and segmentation",
                "Virtual memory and demand paging",
                "Page replacement algorithms: FIFO, LRU, Optimal; Belady's anomaly",
                "Thrashing and the working set model",
            ],
            "Unit 4 - File Systems & Disk Management": [
                "File concepts, attributes, operations and access methods",
                "Directory structures",
                "File allocation methods: contiguous, linked, indexed",
                "Free space management",
                "Disk scheduling algorithms: FCFS, SSTF, SCAN, C-SCAN, LOOK",
                "Protection and security basics in OS",
            ],
        },
    },
    "Database Management Systems": {
        "source": "CSE 4th Sem Syllabus",
        "units": {
            "Unit 1 - Introduction & ER Model": [
                "DBMS vs file system, advantages of DBMS",
                "Three-level architecture and data independence",
                "Data models: hierarchical, network, relational",
                "ER model: entities, attributes, relationship types, cardinality",
                "Keys: super key, candidate key, primary key, foreign key",
                "Converting ER diagrams to relational tables",
            ],
            "Unit 2 - Relational Model & SQL": [
                "Relational algebra: select, project, join, set operations, division",
                "Types of joins: inner, outer, natural, self join",
                "SQL: DDL, DML, DCL and TCL commands",
                "Integrity constraints in SQL",
                "Nested subqueries and correlated subqueries",
                "Aggregate functions, GROUP BY and HAVING",
                "Views and their uses",
            ],
            "Unit 3 - Normalization": [
                "Functional dependencies and Armstrong's axioms",
                "Attribute closure and canonical cover",
                "Lossless join and dependency preserving decomposition",
                "Normal forms: 1NF, 2NF, 3NF and BCNF",
                "Multivalued dependencies and 4NF",
                "Anomalies removed by normalization",
            ],
            "Unit 4 - Transactions, Concurrency & Indexing": [
                "Transactions and ACID properties",
                "Transaction states and schedules",
                "Serializability: conflict and view serializability",
                "Lock-based protocols and Two-Phase Locking (2PL)",
                "Timestamp-based concurrency control and deadlock handling",
                "Log-based recovery and checkpoints",
                "Indexing: B-tree and B+ tree, hashing",
            ],
        },
    },
    "Computer Networks": {
        "source": "CSE 4th Sem Syllabus",
        "units": {
            "Unit 1 - Introduction & Physical Layer": [
                "Network types: LAN, MAN, WAN and network topologies",
                "OSI reference model: layers and their functions",
                "TCP/IP model and comparison with OSI",
                "Guided and unguided transmission media",
                "Circuit switching vs packet switching vs message switching",
            ],
            "Unit 2 - Data Link Layer": [
                "Framing techniques",
                "Error detection: parity, checksum, CRC",
                "Error correction: Hamming code",
                "Flow control: stop-and-wait, sliding window",
                "Go-Back-N vs Selective Repeat ARQ",
                "Multiple access protocols: ALOHA, CSMA/CD, CSMA/CA",
                "Ethernet and MAC addressing",
            ],
            "Unit 3 - Network Layer": [
                "IPv4 addressing: classful and classless (CIDR)",
                "Subnetting and supernetting",
                "IPv4 vs IPv6",
                "ARP, RARP, ICMP and DHCP",
                "Routing algorithms: distance vector and link state",
                "Count-to-infinity problem",
                "Congestion control basics at network layer",
            ],
            "Unit 4 - Transport & Application Layer": [
                "UDP vs TCP: headers, features and use cases",
                "TCP three-way handshake and connection termination",
                "TCP flow control and congestion control: slow start, AIMD",
                "Port numbers and sockets",
                "DNS: how domain name resolution works",
                "HTTP vs HTTPS, FTP, SMTP, POP3 and IMAP",
                "Basics of network security: firewalls and encryption",
            ],
        },
    },
    "Software Engineering": {
        "source": "CSE 4th Sem Syllabus",
        "units": {
            "Unit 1 - Introduction & Process Models": [
                "Software characteristics and the software crisis",
                "SDLC phases",
                "Waterfall model: strengths and weaknesses",
                "Prototype and incremental models",
                "Spiral model and risk handling",
                "Agile methodology: Scrum and Extreme Programming basics",
                "Choosing a process model for a given project",
            ],
            "Unit 2 - Requirements Engineering": [
                "Requirement elicitation techniques",
                "Functional vs non-functional requirements",
                "SRS document: structure and characteristics of a good SRS",
                "Use case diagrams",
                "Data Flow Diagrams (DFD) and levels of DFD",
                "Decision tables and decision trees",
            ],
            "Unit 3 - Design & Project Management": [
                "Cohesion and its types",
                "Coupling and its types; why high cohesion low coupling",
                "Modularity, top-down vs bottom-up design",
                "Function-oriented vs object-oriented design",
                "UML diagrams: class, sequence, activity",
                "Cost estimation: COCOMO model, function points",
                "Project scheduling: Gantt charts and PERT",
                "Risk management",
            ],
            "Unit 4 - Testing & Maintenance": [
                "Verification vs validation",
                "Levels of testing: unit, integration, system, acceptance",
                "Black box testing: boundary value analysis, equivalence partitioning",
                "White box testing: path testing, cyclomatic complexity",
                "Regression testing and debugging",
                "Types of software maintenance",
                "Software quality standards: ISO 9000, CMM levels",
            ],
        },
    },
}

# ---------------------------------------------------------------------------
# DSA - STRIVER A2Z SHEET (step-wise problems)
# ---------------------------------------------------------------------------

STRIVER_A2Z = {
    "Step 3 - Arrays": [
        "Two Sum",
        "Sort an array of 0s, 1s and 2s (Dutch National Flag)",
        "Majority Element (> n/2 times)",
        "Kadane's Algorithm - Maximum Subarray Sum",
        "Best Time to Buy and Sell Stock",
        "Rotate Array by K places",
        "Next Permutation",
        "Longest Consecutive Sequence",
        "Set Matrix Zeroes",
        "Rotate Matrix by 90 degrees",
        "Spiral Traversal of Matrix",
        "3 Sum",
        "Merge Overlapping Intervals",
        "Find the Repeating and Missing Number",
        "Count Inversions in an Array",
    ],
    "Step 4 - Binary Search": [
        "Search in Rotated Sorted Array",
        "Find Minimum in Rotated Sorted Array",
        "Single Element in a Sorted Array",
        "Find Peak Element",
        "Koko Eating Bananas",
        "Aggressive Cows",
        "Allocate Minimum Number of Pages (Book Allocation)",
        "Median of Two Sorted Arrays",
    ],
    "Step 5 - Strings": [
        "Reverse Words in a String",
        "Longest Palindromic Substring",
        "String to Integer (atoi)",
        "Longest Common Prefix",
        "Valid Anagram",
        "Sort Characters by Frequency",
    ],
    "Step 6 - Linked List": [
        "Reverse a Linked List",
        "Find Middle of Linked List",
        "Detect a Cycle in Linked List (Floyd's algorithm)",
        "Find the Starting Point of the Loop",
        "Merge Two Sorted Linked Lists",
        "Remove Nth Node from End",
        "Add Two Numbers represented as Linked Lists",
        "Check if Linked List is Palindrome",
        "Reverse Nodes in K-Group",
        "LRU Cache design",
    ],
    "Step 7 - Recursion & Backtracking": [
        "Print all Subsequences / Subsets",
        "Combination Sum",
        "Permutations of an Array",
        "N-Queens Problem",
        "Sudoku Solver",
        "Rat in a Maze",
        "Word Search in a Grid",
        "Palindrome Partitioning",
    ],
    "Step 8 - Bit Manipulation": [
        "Check, Set and Clear the i-th bit",
        "Count the Number of Set Bits",
        "Single Number (every other element appears twice)",
        "XOR of Numbers in a Range",
        "Power Set using Bit Manipulation",
    ],
    "Step 9 - Stacks & Queues": [
        "Valid Parentheses",
        "Implement Min Stack",
        "Infix to Postfix Conversion",
        "Next Greater Element",
        "Trapping Rain Water",
        "Largest Rectangle in a Histogram",
        "Sliding Window Maximum",
        "Stock Span Problem",
        "Implement Queue using Stacks",
    ],
    "Step 10 - Sliding Window & Two Pointers": [
        "Longest Substring Without Repeating Characters",
        "Max Consecutive Ones III",
        "Longest Repeating Character Replacement",
        "Binary Subarrays with Sum",
        "Minimum Window Substring",
        "Fruit Into Baskets",
    ],
    "Step 11 - Heaps": [
        "Kth Largest Element in an Array",
        "Merge K Sorted Lists",
        "Top K Frequent Elements",
        "Task Scheduler",
        "Find Median from Data Stream",
    ],
    "Step 12 - Greedy": [
        "N Meetings in One Room",
        "Fractional Knapsack",
        "Job Sequencing Problem",
        "Jump Game",
        "Minimum Number of Platforms",
        "Non-overlapping Intervals",
    ],
    "Step 13 - Binary Trees": [
        "Tree Traversals (Inorder, Preorder, Postorder, Level Order)",
        "Height of a Binary Tree",
        "Check if Tree is Balanced",
        "Diameter of a Binary Tree",
        "Maximum Path Sum",
        "Zig-Zag (Spiral) Traversal",
        "Top View / Bottom View of Binary Tree",
        "Lowest Common Ancestor in Binary Tree",
        "Construct Tree from Inorder and Preorder",
        "Serialize and Deserialize a Binary Tree",
    ],
    "Step 14 - Binary Search Trees": [
        "Search in a BST",
        "Validate a BST",
        "Kth Smallest Element in BST",
        "Lowest Common Ancestor in BST",
        "Two Sum in a BST",
        "Recover a BST with two swapped nodes",
    ],
    "Step 15 - Graphs": [
        "BFS and DFS Traversal",
        "Number of Islands",
        "Rotten Oranges",
        "Detect Cycle in Undirected Graph",
        "Detect Cycle in Directed Graph",
        "Check if Graph is Bipartite",
        "Topological Sort (Kahn's Algorithm)",
        "Course Schedule",
        "Dijkstra's Algorithm",
        "Bellman-Ford Algorithm",
        "Minimum Spanning Tree (Prim's / Kruskal's)",
        "Disjoint Set (Union-Find)",
        "Kosaraju's Algorithm (Strongly Connected Components)",
    ],
    "Step 16 - Dynamic Programming": [
        "Climbing Stairs",
        "House Robber",
        "Grid Unique Paths",
        "Minimum Path Sum in Grid",
        "Subset Sum Problem",
        "Partition Equal Subset Sum",
        "0/1 Knapsack",
        "Coin Change",
        "Longest Common Subsequence",
        "Edit Distance",
        "Longest Increasing Subsequence",
        "Best Time to Buy and Sell Stock with Cooldown",
        "Matrix Chain Multiplication",
    ],
    "Step 17 - Tries": [
        "Implement Trie (Insert, Search, StartsWith)",
        "Maximum XOR of Two Numbers in an Array",
        "Number of Distinct Substrings using Trie",
    ],
}

ALL_SUBJECTS = list(SYLLABUS_SUBJECTS.keys())
ALL_DSA_STEPS = list(STRIVER_A2Z.keys())
