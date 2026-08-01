GRAPH_RAG_PROMPT = "Gunakan graph untuk menghubungkan topic, concept, source, note, task, goal, roadmap, dan research brief."

GRAPH_RAG_V3_PROMPT = (
    "GraphRAG V3 (tri-store: SQLite kanonis + Neo4j + FAISS). "
    "Cari konteks lintas topic/concept/source/note/task/goal dengan graph_v3_search "
    "(hybrid: lexical + semantic + struktur). Tambah pengetahuan lewat "
    "graph_v3_upsert_node lalu hubungkan dengan graph_v3_link — sebut node via "
    "(node_type, title), identitas dihitung otomatis. Sertakan provenance untuk klaim "
    "penting. Kemiripan semantik BUKAN bukti relasi; jangan buat edge tanpa dasar. "
    "graph_v3_neighborhood/graph_v3_path untuk eksplorasi struktural. "
    "graph_v3_rebuild destruktif ke projeksi dan wajib approval admin."
)

