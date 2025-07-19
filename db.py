import sqlite3
import threading
import json
import datetime

# Usar threading.Lock para operaciones thread-safe
db_lock = threading.Lock()
conn = sqlite3.connect("cinebot.db", check_same_thread=False)
cur = conn.cursor()

# Sistema de niveles
LEVELS = [
    {"name": "🎞️ Espectador Ocasional", "min_points": 0, "emoji": "🎞️"},
    {"name": "📺 Aficionado al Séptimo Arte", "min_points": 50, "emoji": "📺"},
    {"name": "🎬 Proyector de Barrio", "min_points": 100, "emoji": "🎬"},
    {"name": "🎭 Crítico Emergente", "min_points": 250, "emoji": "🎭"},
    {"name": "🎪 Curador de Festivales", "min_points": 400, "emoji": "🎪"},
    {"name": "📽️ Director Honorario", "min_points": 600, "emoji": "📽️"},
    {"name": "🏆 Cinéfilo de Oro", "min_points": 1000, "emoji": "🏆"},
    {"name": "👑 Maestro del Cine", "min_points": 1500, "emoji": "👑"},
    {"name": "🌟 Leyenda Viviente", "min_points": 2500, "emoji": "🌟"}
]

def get_user_level(points):
    """Obtiene el nivel actual del usuario basado en sus puntos"""
    current_level = LEVELS[0]
    for level in LEVELS:
        if points >= level["min_points"]:
            current_level = level
        else:
            break
    return current_level

def get_next_level(points):
    """Obtiene el siguiente nivel y puntos necesarios"""
    for level in LEVELS:
        if points < level["min_points"]:
            return level, level["min_points"] - points
    return None, 0

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
                    count INTEGER,
                    current_level TEXT DEFAULT '🎞️ Espectador Ocasional',
                    level_notifications INTEGER DEFAULT 1
                )
            """)
            
            # Tabla de configuración del bot
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bot_config (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
                    validation_type TEXT,
                    validation_params TEXT,
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
                    level_up_notifications INTEGER DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Tabla para completions de retos
            cur.execute("""
                CREATE TABLE IF NOT EXISTS challenge_completions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    challenge_title TEXT,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    week_start DATE,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            
            # Agregar columnas nuevas si no existen (para usuarios existentes)
            try:
                cur.execute("ALTER TABLE users ADD COLUMN current_level TEXT DEFAULT '🎞️ Espectador Ocasional'")
                cur.execute("ALTER TABLE users ADD COLUMN level_notifications INTEGER DEFAULT 1")
            except sqlite3.OperationalError:
                pass  # Columnas ya existen
            
            conn.commit()
            print("[DEBUG] Base de datos inicializada correctamente")
            
        except Exception as e:
            print(f"[ERROR] inicializando BD: {e}")

# Inicializar al importar
init_database()

def add_points(user_id, username, pts):
    """Agregar puntos a un usuario y verificar level up"""
    with db_lock:
        try:
            cur.execute("SELECT points, count, current_level FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()
            
            old_points = 0
            old_level = LEVELS[0]["name"]
            
            if row:
                old_points = row[0]
                old_level = row[2] if row[2] else LEVELS[0]["name"]
                cur.execute("UPDATE users SET points=points+?, count=count+1 WHERE id=?", (pts, user_id))
            else:
                cur.execute("""
                    INSERT INTO users (id, username, points, count, current_level) 
                    VALUES (?, ?, ?, 1, ?)
                """, (user_id, username, pts, LEVELS[0]["name"]))
            
            # Verificar level up
            new_points = old_points + pts
            old_level_data = get_user_level(old_points)
            new_level_data = get_user_level(new_points)
            
            level_up_msg = None
            if old_level_data["name"] != new_level_data["name"]:
                # ¡LEVEL UP!
                cur.execute("UPDATE users SET current_level=? WHERE id=?", 
                          (new_level_data["name"], user_id))
                
                level_up_msg = (f"🎉 **¡LEVEL UP!** 🎉\n"
                              f"{new_level_data['emoji']} {username} ha alcanzado:\n"
                              f"**{new_level_data['name']}**\n\n"
                              f"¡Tu pasión cinéfila no tiene límites! 🚀")
                
                # Registrar level up en stats
                cur.execute("""
                    INSERT OR REPLACE INTO user_stats 
                    (user_id, level_up_notifications) 
                    VALUES (?, COALESCE((SELECT level_up_notifications FROM user_stats WHERE user_id = ?), 0) + 1)
                """, (user_id, user_id))
            
            # Actualizar estadísticas
            update_user_activity(user_id)
            conn.commit()
            
            return level_up_msg
            
        except Exception as e:
            print(f"[ERROR] agregando puntos: {e}")
            return None

def get_user_stats(user_id):
    """Obtener estadísticas de un usuario con nivel"""
    with db_lock:
        try:
            cur.execute("""
                SELECT username, points, count, current_level 
                FROM users WHERE id=?
            """, (user_id,))
            row = cur.fetchone()
            if row:
                points = row[1]
                current_level = get_user_level(points)
                next_level, points_needed = get_next_level(points)
                
                return {
                    "username": row[0], 
                    "points": points, 
                    "count": row[2],
                    "current_level": current_level,
                    "next_level": next_level,
                    "points_to_next": points_needed
                }
            return None
        except Exception as e:
            print(f"[ERROR] obteniendo stats: {e}")
            return None

def get_top10():
    """Obtener top 10 usuarios por puntos con niveles"""
    with db_lock:
        try:
            cur.execute("""
                SELECT username, points, current_level 
                FROM users 
                ORDER BY points DESC 
                LIMIT 10
            """)
            results = []
            for row in cur.fetchall():
                level_data = get_user_level(row[1])
                results.append({
                    "username": row[0],
                    "points": row[1], 
                    "level": level_data
                })
            return results
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
                INSERT INTO challenges (week_start, title, description, hashtag, 
                                      bonus_points, validation_type, validation_params)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                week_start,
                challenge_data['title'],
                challenge_data['description'], 
                challenge_data['hashtag'],
                challenge_data['bonus_points'],
                challenge_data.get('validation_type', 'always_true'),
                json.dumps(challenge_data.get('validation_params', {}))
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
                SELECT title, description, hashtag, bonus_points, validation_type, validation_params
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
                    'validation_type': row[4] if row[4] else 'always_true',
                    'validation_params': json.loads(row[5]) if row[5] else {}
                }
            return None
            
        except Exception as e:
            print(f"[ERROR] obteniendo reto actual: {e}")
            return None

def mark_challenge_completed(user_id, challenge_title):
    """Marcar que un usuario completó un reto"""
    with db_lock:
        try:
            week_start = datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday())
            
            # Verificar si ya completó este reto esta semana
            cur.execute("""
                SELECT id FROM challenge_completions 
                WHERE user_id = ? AND challenge_title = ? AND week_start = ?
            """, (user_id, challenge_title, week_start))
            
            if cur.fetchone():
                return False  # Ya completado
            
            # Marcar como completado
            cur.execute("""
                INSERT INTO challenge_completions (user_id, challenge_title, week_start)
                VALUES (?, ?, ?)
            """, (user_id, challenge_title, week_start))
            
            # Actualizar stats del usuario
            cur.execute("""
                INSERT OR REPLACE INTO user_stats 
                (user_id, challenges_completed)
                VALUES (?, COALESCE((SELECT challenges_completed FROM user_stats WHERE user_id = ?), 0) + 1)
            """, (user_id, user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"[ERROR] marcando reto completado: {e}")
            return False

def get_bot_config(key):
    """Obtener configuración del bot"""
    with db_lock:
        try:
            cur.execute("SELECT value FROM bot_config WHERE key=?", (key,))
            row = cur.fetchone()
            return row[0] if row else None
        except Exception as e:
            print(f"[ERROR] obteniendo config: {e}")
            return None

def set_bot_config(key, value):
    """Establecer configuración del bot"""
    with db_lock:
        try:
            cur.execute("""
                INSERT OR REPLACE INTO bot_config (key, value, updated_at)
                VALUES (?, ?, ?)
            """, (key, value, datetime.datetime.now()))
            conn.commit()
            return True
        except Exception as e:
            print(f"[ERROR] guardando config: {e}")
            return False

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
                SELECT u.username, u.points, u.count, u.current_level,
                       COALESCE(s.total_reviews, 0) as reviews,
                       COALESCE(s.total_recommendations, 0) as recommendations,
                       COALESCE(s.total_critiques, 0) as critiques,
                       COALESCE(s.challenges_completed, 0) as challenges,
                       COALESCE(s.reactions_received, 0) as reactions,
                       COALESCE(s.streak_days, 0) as streak,
                       COALESCE(s.level_up_notifications, 0) as level_ups
                FROM users u
                LEFT JOIN user_stats s ON u.id = s.user_id
                WHERE u.id = ?
            """, (user_id,))
            
            row = cur.fetchone()
            if row:
                points = row[1]
                current_level = get_user_level(points)
                next_level, points_needed = get_next_level(points)
                
                return {
                    'username': row[0],
                    'points': points, 
                    'total_messages': row[2],
                    'current_level': current_level,
                    'next_level': next_level,
                    'points_to_next': points_needed,
                    'reviews': row[4],
                    'recommendations': row[5],
                    'critiques': row[6],
                    'challenges_completed': row[7],
                    'reactions_received': row[8],
                    'streak_days': row[9],
                    'level_ups': row[10]
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
