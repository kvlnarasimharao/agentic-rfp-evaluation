from pathlib import Path
from rfp.database import connect, initialize

path = Path(__file__).resolve().parents[1] / "data" / "rfp.sqlite3"
conn = connect(path)
initialize(conn)
print(f"Seeded {path}")
