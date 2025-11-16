# GEO RAG Workshop

Generative Engine Optimization with Structured Data + RAG

This workshop teaches how generative engines decide what to retrieve, what to trust, and why structured data matters more than classical SEO signals.
Your mission is to enrich recipe documents with structured metadata and build better retrieval behavior using LlamaIndex.

The only file you modify is:
```
solution.py
```

Everything else in the repo provides the environment, workflow, and benchmarking harness.



## 🎯 Goal

Turn messy recipe pages into structured, machine-friendly knowledge.
Make the retriever prefer your structured recipe over dozens of noisy, high-authority pages.

You’ll do this by:
	-	parsing JSON-LD
	-	promoting structured fields into metadata
	-	extracting ingredients and instructions
	-	generating structured TextNode snippets
	-	shaping the retriever toward GEO signals (fact density, structure, information gain)

After your changes, the benchmark should show that the system consistently retrieves the local structured page first, not the noisy web clones.


## 🧩 Project Structure
```
.
├── solution.py          # The only file you edit
├── geo_rag/             # Pipeline, loaders, retriever logic
├── workshop/            # Benchmarking + debug tools
├── run.sh               # Full benchmark runner
├── debug.sh             # Quick-loop debugging (live reload)
└── README.md
```

## ⚙️ Requirements

You need:
	-	Python 3.10+
	-	Docker Desktop (or Docker Engine)
	-	A working internet connection the first time you pull the container

The workshop itself runs inside Docker to keep everyone’s environment identical.

We provide a venv for local helper tools, but you do not need to install or manage system dependencies manually.


## 🗄️ Database Helper Scripts

Use `scripts/db.sh` to manage the Postgres + pgvector container outside of the runners:

```
scripts/db.sh start   # build image if needed and start the container
scripts/db.sh stop    # stop/remove the container
scripts/db.sh status  # exit 0 if running, 1 otherwise
scripts/db.sh wait    # block until pg_isready succeeds
```

Both `run.sh` and `debug.sh` automatically call these commands. They start the database if it is not running and, once they finish, stop it only if they launched it. If you prefer to keep Postgres running between commands, start it yourself (`scripts/db.sh start`) before invoking the runners.



## 🐍 Python Environment 

To setup the virtual environment you can run 
```
sh setup.sh
```

or if you want to do it manually, you can run 
```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Not required for the main benchmarks.



## 🔍 Running the Full Benchmark

When you’re ready to see whether your structured extraction works, run:
```
sh run.sh
```

This builds the retrieval index, runs a battery of GEO-focused questions, and shows how many times your structured local document appears in the top 3 results.
`run.sh` also ensures the database container is up via `scripts/db.sh` and gracefully stops it afterward when appropriate.

At the end, you’ll see something like:
```
Correct local documents in top 3: 55
Score: 96.43
```

Your job is to push this score up by improving the structured metadata you extract.



## 🧪 Debugging & Live Feedback Loop

During development, you’ll want faster iteration.

Run:
```
sh debug.sh
```
This lets you modify solution.py and immediately test retrieval behavior without rebuilding everything.
It auto-starts/stops the Postgres container in the same way as `run.sh`.

Use this to:
	•	inspect JSON-LD output
	•	print your ingredient parsing
	•	validate snippet structure
	•	test instructions extraction
	•	verify metadata enrichment

Once things look good, switch back to run.sh to run the full benchmark.



## 🛠️ What You Need to Implement (in `solution.py`)

Inside process_node, you will:
	1.	Load JSON-LD for the recipe page.
	2.	Identify schema types (Recipe, Article, HowTo, etc.).
	3.	Promote structured fields into node.metadata (name, times, author…).
	4.	Parse ingredients into canonical objects (name, quantity, unit, modifier).
	5.	Emit ingredient-level TextNodes that will get their own embeddings.
	6.	Extract instructions and convert them into step-level snippets.
	7.	Set prioritization metadata so structured content outranks noisy pages.
	8.	Return all structured snippets, letting the pipeline embed them.

The benchmark will reveal whether your structured extraction meaningfully improves retrieval.



## 📚 Concepts You’ll Learn
	-	Why generative engines prefer structured data
	-	How JSON-LD shapes retrieval
	-	How fact density and information gain influence large models
	-	Why “authority” and backlinks are not enough
	-	How to design retrieval pipelines for precise grounding
	-	Practical GEO (Generative Engine Optimization)



## 🏁 Finishing the Workshop

You’re done when:
	-	Your enriched recipe beats noise pages in most queries
	-	Benchmark score climbs significantly
	-	Retrieval becomes precise (ingredient queries hit your structured nodes)
	-	You see the retriever prefer structure over authority

At that point, you’ve built a concrete intuition for what GEO actually rewards.
