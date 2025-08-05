# relativity-faq-bot

small 🐍 project that scrapes **relativityone release notes**, builds a local
vector index and serves a chatbot that answers questions strictly from that
source.  
if the answer isn’t in the notes the bot asks for contact details and logs
them to a google sheet.

---

## table of contents
1. [features](#features)  
2. [tech stack](#tech-stack)  
3. [project layout](#project-layout)  
4. [quick start](#quick-start)  
5. [env vars](#env-vars)  
6. [google sheets oauth](#google-sheets-oauth)  
7. [refreshing the index](#refresh-the-vector-index)  
8. [docker](#docker)  
9. [test cases](#test-cases)

---

## features
* **scraper**: pulls the html table at  
  `https://help.relativity.com/RelativityOne/Content/What_s_New/Release_notes.htm`
* **local embeddings**: `sentence-transformers/all-MiniLM-L6-v2`
* **vector store**: faiss `IndexFlatIP` (cosine)  
  → `data/faiss_index.bin` + enriched `chunks_emb.json`
* **retrieval-only answers** (no llms) + 2-step guard  
  (similarity threshold + keyword overlap)
* **streamlit chat ui**
* **contact flow** → name/email/org saved to google sheets via oauth

---

## tech stack
| layer | choice |
|-------|--------|
| scraping | beautifulsoup4 / requests |
| embeddings | sentence-transformers (384-d) |
| vector db | faiss cpu |
| backend | plain python helpers |
| ui | streamlit + chat component |
| contact storage | gspread (oauth desktop) |

---

## project layout
```

relativity_faq_bot/  
├─ data/ # scraped html, csv, vectors  
│ ├─ release_notes.html  
│ ├─ release_notes.csv  
│ ├─ chunks.json  
│ ├─ chunks_emb.json  
│ └─ faiss_index.bin  
├─ src/  
│ ├─ scrape.py # pulls & segments table  
│ ├─ build_index.py # embeddings + faiss  
│ ├─ qa.py # retrieval logic  
│ ├─ sheets.py # google sheets helper  
│ └─ app.py # streamlit ui  
├─ gcp_client_oauth.json # oauth client (git-ignored)  
├─ token.json # oauth token (git-ignored)  
├─ .env  
└─ requirements.txt

````

---

## quick start

```bash
git clone https://github.com/<your>/<repo>.git
cd relativity_faq_bot
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 1) scrape + build index
python src/scrape.py
python src/build_index.py

# 2) (first time) generate oauth token
python gen_gcp_token.py        # opens browser, creates token.json

# 3) run the ui
streamlit run src/app.py
````

open [http://localhost:8501](http://localhost:8501/) and start asking.

---
## env vars

put these in `.env` (already `.gitignore`d):

| var               | example                 | notes                                  |
| ----------------- | ----------------------- | -------------------------------------- |
| `GS_CLIENT_OAUTH` | `gcp_client_oauth.json` | oauth client json path                 |
| `GS_TOKEN`        | `token.json`            | where gspread stores the refresh token |
| `GSHEET_ID`       | `1AbCdEFgHi...`         | id of the sheet to log contacts        |

---

## google sheets oauth

1. **gcp console** → enable **google sheets api**
    
2. **credentials** → _oauth client id_ → _desktop_ → download json
    
3. save as `gcp_client_oauth.json` in repo root
    
4. `python gen_gcp_token.py` → browser login → creates `token.json`
    
5. put the sheet id in `.env` and make sure your gmail owns the sheet  
    (or has editor access).
    

---

## refresh the vector index

```
./refresh_index.sh   # wrapper: scrape → build_index
```

schedule it in `cron` or gh-actions if you want weekly updates.

---
## test cases

|#|user question|expected ui behaviour|sheet row?|
|---|---|---|---|
|1|_when was the cost explorer enhancement released?_|bot returns release from 2024-09-10|no|
|2|_what was added to air for review on 2025-04-21?_|bot returns note about max job size increase|no|
|3|_does relativity integrate with jira cloud out of the box?_|bot can’t find answer → asks for contact → you submit form|yes|
|4|_is there a dark mode ui for relativityone?_|same as #3 (contact flow)|yes|

check the google sheet after #3 and #4 – two new rows with your test data.