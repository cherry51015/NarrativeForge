# NarrativeForge

**NarrativeForge** is an **AI-powered automated book publication workflow** that integrates web scraping, AI-assisted writing, human-in-the-loop reviews, and reinforcement learning–based refinement.  
Originally designed as a technical evaluation task, this project has been extended into a personal project exploring **AI-driven narrative generation, editing, and publication workflows.**

---

## 🚀 Features

- **📖 Web Scraping & Screenshots**
  - Extracts chapter content from sources like [Wikisource](https://en.wikisource.org/wiki/The_Gates_of_Morning/Book_1/Chapter_1)
  - Captures clean screenshots for reference using Playwright

- **🤖 AI Writing & Review**
  - AI **Writer Agent** spins raw content into new drafts
  - AI **Reviewer Agent** refines drafts with improvements in style, coherence, and readability
  - Multiple iteration cycles supported

- **👨‍💻 Human-in-the-Loop**
  - Writers, reviewers, and editors can intervene at each stage
  - Supports iterative editing and decision-making
  - Reinforcement Learning–based reward model aligns AI outputs with human feedback

- **🔎 Agentic API & Semantic Search**
  - Exposes a **FastAPI backend** for agent coordination
  - Provides voice interaction & versioning support
  - Embeddings stored in **ChromaDB** for semantic retrieval and version control

- **🎯 RL-Based Reward System**
  - Reinforcement learning methods guide both content generation and retrieval
  - Ensures consistent quality and alignment across multiple iterations

---

## 🗂️ Project Structure
NarrativeForge/
│
├── ai_pipeline/ # Core AI agents and pipeline orchestration
│ ├── ai_pipeline.py
│ └── init.py
│
├── fastapi_server/ # API endpoints for agents and HITL interactions
│ ├── main.py
│ └── chromadb_utils.py
│
├── scraping/ # Web scraping utilities
│ └── scrape_chapter.py
│
├── data/ # Sample scraped data, AI outputs, and embeddings
│ ├── chromadb/ # ChromaDB persistence
│ ├── content.txt
│ ├── writer.txt
│ ├── reviewer.txt
│ └── screenshots
│
├── hitl/ # Human-in-the-loop orchestration
│ └── hitl_pipeline.py
│
├── run_pipeline.py # Entry point to run the full workflow
├── requirements.txt # Dependencies
└── README.md # Project documentation (this file)

---

## ⚙️ Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cherry51015/NarrativeForge.git
   cd NarrativeForge
Set up a virtual environment (recommended)

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Mac/Linux
venv\Scripts\activate      # On Windows
Install dependencies

bash
Copy
Edit
pip install -r requirements.txt
▶️ Usage
Scrape a chapter

bash
Copy
Edit
python scraping/scrape_chapter.py
Run the AI pipeline

bash
Copy
Edit
python run_pipeline.py
Start the API server

bash
Copy
Edit
uvicorn fastapi_server.main:app --reload
Access the API at http://127.0.0.1:8000

📊 Roadmap
 Integrate RLHF-style reward model for iterative improvements

 Add voice interaction agent

 Extend semantic search to cross-book datasets

 Add proper evaluation metrics for AI writing

🤝 Contributing
Contributions are welcome! Please fork the repository, create a branch, and submit a pull request.

📜 License
This project is for educational and research purposes only.
The developer retains full ownership of the code.
No commercial use intended.

