import sqlite3
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

# Configuración de la base de datos
DB_PATH = "cinebot.db"
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
cur = conn.cursor()

def init_database():
    """Inicializa todas las tablas necesarias"""
    
    # Tabla de usuarios
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY, 
            username TEXT, 
            points INTEGER DEFAULT 0, 
            count INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de contribuciones para historial detallado
    cur.execute("""
        CREATE TABLE IF NOT EXISTS contributions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            hashtag TEXT,
            points INTEGER,
            message_text TEXT,
            chat_id INTEGER,
            message_id INTEGER,
            is_challenge_bonus BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
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
    
    # Tabla de configuración por chat
    cur.execute("""
        CREATE TABLE IF NOT EXISTS chat_config (
            chat_id INTEGER PRIMARY KEY,
            chat_title TEXT,
            auto_ranking BOOLEAN DEFAULT 1,
            auto_challenges BOOLEAN DEFAULT 1,
            admin_notifications BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Tabla de logros/achievements
    cur.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            achievement_id TEXT,
            achievement_name TEXT,
            earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    
    conn.commit()
    print("[INFO] Base de datos inicializada correctamente")

# Inicializar al importar
init_database()

# ===== FUNCIONES PARA USUARIOS =====

def add_points(user_id: int, username: str, pts: int, hashtag: str = "", message_text: str = "", chat_id: int = 0, message_id: int = 0, is_challenge_bonus: bool = False):
    """Agrega puntos a un usuario y registra la contribución"""
    try:
        # Verificar si el usuario existe
        cur.execute("SELECT points, count FROM users WHERE id=?", (user_id,))
        row = cur.fetchone()
        
        if row:
            # Usuario existe - actualizar
            cur.execute("""
                UPDATE users 
                SET points=points+?, count=count+1, last_activity=CURRENT_TIMESTAMP 
                WHERE id=?
            """, (pts, user_id))
        else:
            # Usuario nuevo - insertar
            cur.execute("""
                INSERT INTO users (id, username, points, count) 
                VALUES (?, ?, ?, 1)
            """, (user_id, username, pts))
        
        # Registrar la contribución
        cur.execute("""
            INSERT INTO contributions 
            (user_id, username, hashtag, points, message_text, chat_id, message_id, is_challenge_bonus)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, username, hashtag, pts, message_text[:500], chat_id, message_id, is_challenge_bonus))
        
        conn.commit()
        
        # Verificar si subió de nivel
        new_total_points = (row[0] + pts) if row else pts
        level_change = check_level_up(user_id, new_total_points)
        
        print(f"[INFO] +{pts} puntos para {username} (total: {new_total_points})")
        
        return {"success": True, "total_points": new_total_points, "level_change": level_change}
        
    except Exception as e:
        print(f"[ERROR] Error agregando puntos: {e}")
        conn.rollback()
        return {"success": False, "error": str(e)}

def get_user_stats(user_id: int) -> Optional[Dict]:
    """Obtiene estadísticas detalladas de un usuario"""
    try:
        cur.execute("""
            SELECT username, points, count, level, last_activity, created_at 
            FROM users WHERE id=?
        """, (user_id,))
        row = cur.fetchone()
        
        if not row:
            return None
        
        # Obtener contribuciones recientes
        cur.execute("""
            SELECT hashtag, points, created_at 
            FROM contributions 
            WHERE user_id=? 
            ORDER BY created_at DESC LIMIT 5
        """, (user_id,))
        recent_contributions = cur.fetchall()
        
        # Calcular nivel y progreso
        level_info = get_level_info(row[1])  # row[1] = points
        
        return {
            "username": row[0],
            "points": row[1],
            "count": row[2],
            "level": level_info["level"],
            "level_name": level_info["name"],
            "points_to_next": level_info["points_to_next"],
            "last_activity": row[4],
            "member_since": row[5],
            "recent_contributions": recent_contributions
        }
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo stats de usuario: {e}")
        return None

def get_top10() -> List[Tuple]:
    """Obtiene el top 10 de usuarios por puntos"""
    try:
        cur.execute("""
            SELECT username, points, level 
            FROM users 
            ORDER BY points DESC 
            LIMIT 10
        """)
        return cur.fetchall()
    except Exception as e:
        print(f"[ERROR] Error obteniendo top 10: {e}")
        return []

def get_weekly_stats() -> Dict:
    """Obtiene estadísticas de la semana actual"""
    try:
        week_ago = datetime.now() - timedelta(days=7)
        
        # Usuarios más activos de la semana
        cur.execute("""
            SELECT username, COUNT(*) as contributions, SUM(points) as weekly_points
            FROM contributions 
            WHERE created_at > ?
            GROUP BY user_id, username
            ORDER BY weekly_points DESC
            LIMIT 5
        """, (week_ago,))
        top_weekly = cur.fetchall()
        
        # Estadísticas por hashtag
        cur.execute("""
            SELECT hashtag, COUNT(*) as count, SUM(points) as total_points
            FROM contributions 
            WHERE created_at > ?
            GROUP BY hashtag
            ORDER BY count DESC
        """, (week_ago,))
        hashtag_stats = cur.fetchall()
        
        # Stats generales
        cur.execute("""
            SELECT 
                COUNT(*) as total_contributions,
                COUNT(DISTINCT user_id) as active_users,
                SUM(points) as total_points
            FROM contributions 
            WHERE created_at > ?
        """, (week_ago,))
        general_stats = cur.fetchone()
        
        return {
            "top_weekly": top_weekly,
            "hashtag_stats": hashtag_stats,
            "general": {
                "total_contributions": general_stats[0],
                "active_users": general_stats[1],
                "total_points": general_stats[2]
            }
        }
    except Exception as e:
        print(f"[ERROR] Error obteniendo stats semanales: {e}")
        return {}

# ===== SISTEMA DE NIVELES =====

LEVEL_THRESHOLDS = {
    1: {"name": "🎞️ Proyector de Barrio", "points": 0},
    2: {"name": "📽️ Crítico Emergente", "points": 100},
    3: {"name": "🎬 Director Honorario", "points": 250},
    4: {"name": "🏆 Cinéfilo de Oro", "points": 500},
    5: {"name": "👑 Maestro del Séptimo Arte", "points": 1000}
}

def get_level_info(points: int) -> Dict:
    """Calcula el nivel actual y puntos para el siguiente"""
    current_level = 1
    for level, data in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
        if points >= data["points"]:
            current_level = level
            break
    
    next_level_points = None
    points_to_next = 0
    
    if current_level < max(LEVEL_THRESHOLDS.keys()):
        next_level_points = LEVEL_THRESHOLDS[current_level + 1]["points"]
        points_to_next = next_level_points - points
    
    return {
        "level": current_level,
        "name": LEVEL_THRESHOLDS[current_level]["name"],
        "current_points": points,
        "points_to_next": points_to_next
    }

def check_level_up(user_id: int, new_points: int) -> Optional[Dict]:
    """Verifica si el usuario subió de nivel - CORREGIDO"""
    try:
        # Obtener nivel anterior
        cur.execute("SELECT level FROM users WHERE id=?", (user_id,))
        result = cur.fetchone()
        old_level = result[0] if result else 1
        
        # Calcular nuevo nivel
        new_level_info = get_level_info(new_points)
        new_level = new_level_info["level"]
        
        if new_level > old_level:
            # Actualizar nivel en la base de datos
            cur.execute("UPDATE users SET level=? WHERE id=?", (new_level, user_id))
            conn.commit()
            
            return {
                "leveled_up": True,
                "old_level": old_level,
                "new_level": new_level,
                "level_name": new_level_info["name"]
            }
        
        return {"leveled_up": False}
        
    except Exception as e:
        print(f"[ERROR] Error verificando level up: {e}")
        return None

# ===== FUNCIONES PARA RETOS =====

def get_current_challenge() -> Optional[str]:
    """Obtiene el reto personalizado actual"""
    try:
        cur.execute("SELECT value FROM bot_config WHERE key='current_challenge'")
        row = cur.fetchone()
        return row[0] if row else None
    except Exception as e:
        print(f"[ERROR] Error obteniendo reto actual: {e}")
        return None

def set_challenge(text: str):
    """Establece un reto personalizado"""
    try:
        cur.execute("""
            INSERT OR REPLACE INTO bot_config (key, value, updated_at) 
            VALUES ('current_challenge', ?, CURRENT_TIMESTAMP)
        """, (text,))
        conn.commit()
        print(f"[INFO] Reto establecido: {text[:50]}...")
    except Exception as e:
        print(f"[ERROR] Error estableciendo reto: {e}")

def clear_challenge():
    """Limpia el reto personalizado actual"""
    try:
        cur.execute("DELETE FROM bot_config WHERE key='current_challenge'")
        conn.commit()
        print("[INFO] Reto personalizado limpiado")
    except Exception as e:
        print(f"[ERROR] Error limpiando reto: {e}")

# ===== CONFIGURACIÓN DE CHATS =====

def get_chat_config() -> List[int]:
    """Obtiene lista de chat_ids configurados para notificaciones automáticas"""
    try:
        cur.execute("SELECT chat_id FROM chat_config WHERE auto_ranking=1 OR auto_challenges=1")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        print(f"[ERROR] Error obteniendo configuración de chats: {e}")
        return []

def set_chat_config(chat_id: int, chat_title: str = "", auto_ranking: bool = True, auto_challenges: bool = True):
    """Configura un chat para recibir notificaciones automáticas"""
    try:
        cur.execute("""
            INSERT OR REPLACE INTO chat_config 
            (chat_id, chat_title, auto_ranking, auto_challenges) 
            VALUES (?, ?, ?, ?)
        """, (chat_id, chat_title, auto_ranking, auto_challenges))
        conn.commit()
        print(f"[INFO] Chat {chat_id} configurado correctamente")
    except Exception as e:
        print(f"[ERROR] Error configurando chat: {e}")

# ===== FUNCIONES DE CONFIGURACIÓN GENERAL =====

def get_config(key: str, default_value: str = "") -> str:
    """Obtiene un valor de configuración"""
    try:
        cur.execute("SELECT value FROM bot_config WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else default_value
    except Exception as e:
        print(f"[ERROR] Error obteniendo config {key}: {e}")
        return default_value

def set_config(key: str, value: str):
    """Establece un valor de configuración"""
    try:
        cur.execute("""
            INSERT OR REPLACE INTO bot_config (key, value, updated_at) 
            VALUES (?, ?, CURRENT_TIMESTAMP)
        """, (key, value))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Error estableciendo config {key}: {e}")

# ===== FUNCIONES DE LIMPIEZA Y MANTENIMIENTO =====

def cleanup_old_contributions(days: int = 90):
    """Limpia contribuciones más antiguas que X días"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        cur.execute("DELETE FROM contributions WHERE created_at < ?", (cutoff_date,))
        deleted_count = cur.rowcount
        conn.commit()
        print(f"[INFO] {deleted_count} contribuciones antiguas limpiadas")
    except Exception as e:
        print(f"[ERROR] Error en limpieza: {e}")

def get_database_stats():
    """Obtiene estadísticas generales de la base de datos"""
    try:
        stats = {}
        
        # Contar usuarios
        cur.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = cur.fetchone()[0]
        
        # Contar contribuciones
        cur.execute("SELECT COUNT(*) FROM contributions")
        stats['total_contributions'] = cur.fetchone()[0]
        
        # Puntos totales otorgados
        cur.execute("SELECT SUM(points) FROM users")
        stats['total_points'] = cur.fetchone()[0] or 0
        
        # Usuario más activo
        cur.execute("""
            SELECT username, points, count 
            FROM users 
            ORDER BY points DESC 
            LIMIT 1
        """)
        top_user = cur.fetchone()
        stats['top_user'] = {"username": top_user[0], "points": top_user[1], "contributions": top_user[2]} if top_user else None
        
        return stats
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo stats de DB: {e}")
        return {}
