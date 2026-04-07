import sqlite3
import os

db_path = 'instance/agencei.db'
if not os.path.exists(db_path):
    db_path = 'agencei.db'

print(f"Atualizando banco de dados em: {db_path}")

try:
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Adicionar a coluna de status na table evento
    c.execute("ALTER TABLE evento ADD COLUMN status VARCHAR(20) DEFAULT 'agendado' NOT NULL;")
    conn.commit()
    print("✅ Coluna 'status' adicionada com sucesso na tabela evento!")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("⚠️ A coluna já existia.")
    else:
        print(f"❌ Erro SQLite: {e}")
except Exception as e:
    print(f"❌ Erro inesperado: {e}")
finally:
    if 'conn' in locals():
        conn.close()
