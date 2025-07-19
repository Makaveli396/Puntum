import sqlite3
import threading
import json
import datetime

# Usar threading.Lock para operaciones thread-safe
db_lock = threading.Lock()
conn = sqlite3.connect("cinebot.db", check_same_thread=False)
cur = conn.cursor()

# Crear tablas si no existen
def init_database():
    with db_lock:
        try:
            # Tabla de usuarios existente
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY, 
                    username TEXT, 
                    points INTEGER, 
                    count INTEGER
                )
            """)
            
            # Nueva tabla para retos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS challenges (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week_start DATE,
                    title TEXT,
                    description TEXT,
                    hashtag TEXT,
                    bonus_points INTEGER,
                    validation_rule TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Nueva tabla para reacciones
            cur.execute("""
                CREATE TABLE IF NOT EXISTS reactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id INTEGER,
                    user_id INTEGER,
                    reaction_type TEXT,
                    points_awarded INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Nueva tabla para estadísticas avanzadas
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_reviews INTEGER DEFAULT 0,
                    total_recommendations INTEGER DEFAULT 0,
                    total_critiques INTEGER DEFAULT 0,
                    challenges_completed INTEGER DEFAULT 0,
                    reactions_received INTEGER DEFAULT 0,
                    streak_days INTEGER DEFAULT 0,
                    last_activity DATE,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            conn.commit()
            print("[DEBUG] Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"[ERROR] inicializando BD: {e}")

# Inicializar al importar
init_database()

def add_points(user_id, username, pts):
    """Agregar puntos a un usuario"""
    with db_lock:
        try:
            cur.execute("SELECT points, count FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()
            if row:
                cur.execute("UPDATE users SET points=points+?, count=count+1 WHERE id=?", (pts, user_id))
            else:
                cur.execute("INSERT INTO users (id, username, points, count) VALUES (?, ?, ?, 1)", 
                           (user_id, username, pts))
            
            # Actualizar estadísticas
            update_user_activity(user_id)
            conn.commit()
            
        except Exception as e:
            print(f"[ERROR] agregando puntos: {e}")

def get_user_stats(user_id):
    """Obtener estadísticas de un usuario"""
    with db_lock:
        try:
            cur.execute("SELECT username, points, count FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()
            if row:
                return {"username": row[0], "points": row[1], "count": row[2]}
            return None
        except Exception as e:
            print(f"[ERROR] obteniendo stats: {e}")
            return None

def get_top10():
    """Obtener top 10 usuarios por puntos"""
    with db_lock:
        try:
            cur.execute("SELECT username, points FROM users ORDER BY points DESC LIMIT 10")
            return cur.fetchall()
        except Exception as e:
            print(f"[ERROR] obteniendo top10: {e}")
            return []

def set_challenge(challenge_data):
    """Guardar nuevo reto semanal"""
    with db_lock:
        try:
            week_start = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
            
            # Eliminar reto anterior de esta semana si existe
            cur.execute("DELETE FROM challenges WHERE week_start = ?", (week_start,))
            
            # Insertar nuevo reto
            cur.execute("""
                INSERT INTO challenges (week_start, title, description, hashtag, bonus_points, validation_rule)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                week_start,
                challenge_data['title'],
                challenge_data['description'], 
                challenge_data['hashtag'],
                challenge_data['bonus_points'],
                json.dumps(challenge_data.get('validation', {}))
            ))
            
            conn.commit()
            print(f"[DEBUG] Reto guardado: {challenge_data['title']}")
            
        except Exception as e:
            print(f"[ERROR] guardando reto: {e}")

def get_current_challenge():
    """Obtener reto actual de la semana"""
    with db_lock:
        try:
            week_start = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
            
            cur.execute("""
                SELECT title, description, hashtag, bonus_points, validation_rule 
                FROM challenges 
                WHERE week_start = ?
                ORDER BY created_at DESC 
                LIMIT 1
            """, (week_start,))
            
            row = cur.fetchone()
            if row:
                return {
                    'title': row[0],
                    'description': row[1],
                    'hashtag': row[2],
                    'bonus_points': row[3],
                    'validation': json.loads(row[4]) if row[4] else {}
                }
            return None
            
        except Exception as e:
            print(f"[ERROR] obteniendo reto actual: {e}")
            return None

def add_reaction(message_id, user_id, reaction_type, points):
    """Registrar reacción y puntos asociados"""
    with db_lock:
        try:
            # Verificar si ya existe reacción de este usuario a este mensaje
            cur.execute("""
                SELECT id FROM reactions 
                WHERE message_id = ? AND user_id = ? AND reaction_type = ?
            """, (message_id, user_id, reaction_type))
            
            if cur.fetchone():
                print(f"[DEBUG] Reacción duplicada ignorada: {user_id} -> {message_id}")
                return False
            
            # Insertar nueva reacción
            cur.execute("""
                INSERT INTO reactions (message_id, user_id, reaction_type, points_awarded)
                VALUES (?, ?, ?, ?)
            """, (message_id, user_id, reaction_type, points))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] agregando reacción: {e}")
            return False

def update_user_activity(user_id):
    """Actualizar última actividad del usuario"""
    with db_lock:
        try:
            today = datetime.date.today()
            cur.execute("""
                INSERT OR REPLACE INTO user_stats (user_id, last_activity)
                VALUES (?, ?)
            """, (user_id, today))
            
        except Exception as e:
            print(f"[ERROR] actualizando actividad: {e}")

def get_user_advanced_stats(user_id):
    """Obtener estadísticas avanzadas de usuario"""
    with db_lock:
        try:
            cur.execute("""
                SELECT u.username, u.points, u.count,
                       COALESCE(s.total_reviews, 0) as reviews,
                       COALESCE(s.total_recommendations, 0) as recommendations,
                       COALESCE(s.total_critiques, 0) as critiques,
                       COALESCE(s.challenges_completed, 0) as challenges,
                       COALESCE(s.reactions_received, 0) as reactions,
                       COALESCE(s.streak_days, 0) as streak
                FROM users u
                LEFT JOIN user_stats s ON u.id = s.user_id
                WHERE u.id = ?
            """, (user_id,))
            
            row = cur.fetchone()
            if row:
                return {
                    'username': row[0],
                    'points': row[1], 
                    'total_messages': row[2],
                    'reviews': row[3],
                    'recommendations': row[4],
                    'critiques': row[5],
                    'challenges_completed': row[6],
                    'reactions_received': row[7],
                    'streak_days': row[8]
                }
            return None
            
        except Exception as e:
            print(f"[ERROR] obteniendo stats avanzadas: {e}")
            return None

def close_connection():
    """Cerrar conexión de BD (para limpieza)"""
    global conn
    if conn:
        conn.close()
        print("[DEBUG] Conexión BD cerrada")
