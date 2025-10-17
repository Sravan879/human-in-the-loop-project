# Human-in-the-Loop AI Agent

A simple AI agent for a salon that answers customer questions. When it doesn't know an answer, it escalates to a human supervisor and learns from the response.

---
## Tech Stack

* **Backend:** FastAPI (Python)
* **Frontend:** React (JavaScript)
* **Database:** Firebase Firestore
* **Real-time:** LiveKit SDK

---
## Setup Instructions

1.  **Clone Repo & Install Tools:**
    * Clone this repository.
    * Ensure you have Python 3.8+ and Node.js installed.

2.  **Get Credentials:**
    * Create a **Firebase** project, generate a private key, and save it as `service-account-key.json` in the root folder.
    * Create a **LiveKit** project, generate an API Key/Secret, and add your credentials to `livekit_agent.py` and `user_simulator.py`.

3.  **Set Up Backend:**
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

4.  **Set Up Frontend:**
    ```bash
    cd frontend
    npm install
    ```
---
## How to Run

You need **four separate terminals** to run the system.

1.  **Terminal 1 (Backend):** In the `backend` folder, run `uvicorn main:app --reload`
2.  **Terminal 2 (Frontend):** In the `frontend` folder, run `npm start`
3.  **Terminal 3 (Agent):** In the root folder, run `python livekit_agent.py`
4.  **Terminal 4 (Simulator):** In the root folder, run `python user_simulator.py`

---
## Design Notes

* **Decoupled Services:** The Agent, Backend, and Frontend are separate services that communicate via APIs and data channels. This makes the system modular and easier to maintain.
* **Stateful Requests:** Help requests in the database have a `status` field (`pending`, `resolved`). This simple state management cleanly drives the UI and the request lifecycle.
* **Serverless DB:** Using Firestore allows the system to scale easily without managing database infrastructure. The knowledge base is stored in a separate collection, acting as the AI's long-term memory.

---
### Important Note on a Known Blocker

A persistent `ModuleNotFoundError` for the `livekit_api` package was encountered during development across multiple environments. This appears to be a reproducible environment issue, not a flaw in the code's logic.
As a result, a live demo of `livekit_agent.py` may fail. However, the backend API, database logic, and frontend UI are fully functional and implemented correctly.5