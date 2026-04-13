#!/usr/bin/env python3
"""
Web Service Wrapper for Telegram Bot on Render
Runs bot.py in a background subprocess and exposes health check endpoints
"""

from flask import Flask, jsonify
import os
import sys
import logging
from datetime import datetime, timezone
import subprocess
import threading

# ------------------- Logging -------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# ------------------- Environment -------------------
required_vars = ["BOT_TOKEN", "CHANNEL_ID", "BOT_USERNAME", "ADMIN_ID_1"]
missing_vars = [var for var in required_vars if not os.getenv(var)]
if missing_vars:
    logger.error(f"❌ Missing environment variables: {missing_vars}")
    sys.exit(1)

# ------------------- Bot Status -------------------
bot_status = {"running": False, "start_time": None, "last_activity": None}

# ------------------- Flask App -------------------
app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    """Basic health check"""
    return jsonify({
        "status": "healthy",
        "service": "Telegram Confession Bot",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "bot_running": bot_status["running"],
        "uptime": (datetime.now(timezone.utc) - bot_status["start_time"]).total_seconds() if bot_status["start_time"] else 0
    })

@app.route("/health", methods=["GET"])
def health():
    """Detailed health check"""
    return jsonify({
        "status": "ok" if bot_status["running"] else "error",
        "bot_status": bot_status,
        "environment": {var: bool(os.getenv(var)) for var in required_vars}
    })

@app.route("/ping", methods=["GET"])
def ping():
    """Simple ping endpoint"""
    return "pong"

# ------------------- Database Setup -------------------
def setup_database():
    """Run database migrations and setup"""
    try:
        logger.info("🗄️ Setting up database...")
        
        # Import and run migrations
        from migration import run_database_migrations
        run_database_migrations()
        
        logger.info("✅ Database setup completed")
        
        # Run accepting_contacts migration
        logger.info("👤 Running profile migrations...")
        try:
            from db_connection import get_db_connection
            db_conn = get_db_connection()
            with db_conn.get_connection() as conn:
                cursor = conn.cursor()
                if db_conn.use_postgresql:
                    cursor.execute('ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS accepting_contacts BOOLEAN DEFAULT TRUE')
                    logger.info("✅ Added accepting_contacts column (PostgreSQL)")
                else:
                    try:
                        cursor.execute('ALTER TABLE user_profiles ADD COLUMN accepting_contacts INTEGER DEFAULT 1')
                        logger.info("✅ Added accepting_contacts column (SQLite)")
                    except:
                        logger.info("ℹ️ Column accepting_contacts already exists")
                conn.commit()
            logger.info("✅ Profile migrations completed!")
        except Exception as e:
            logger.warning(f"⚠️ Profile migration error (continuing anyway): {e}")
            
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        raise

# ------------------- Start Bot -------------------
def run_bot():
    """Start bot.py as a non-blocking subprocess"""
    try:
        logger.info("🚀 Starting Telegram bot subprocess...")
        bot_status["start_time"] = datetime.now(timezone.utc)
        bot_status["running"] = True

        # First, setup database
        setup_database()

        # Start bot.py with output redirected to stdout so we can see errors
        import subprocess
        bot_process = subprocess.Popen(
            [sys.executable, "bot.py"],
            stdout=sys.stdout,
            stderr=sys.stderr,
            universal_newlines=True,
            bufsize=1
        )
        
        logger.info(f"✅ Bot subprocess started with PID: {bot_process.pid}")
        
        # Monitor the bot process
        def monitor_bot():
            while True:
                poll_result = bot_process.poll()
                if poll_result is not None:
                    logger.error(f"❌ Bot subprocess exited with code: {poll_result}")
                    bot_status["running"] = False
                    break
                bot_status["last_activity"] = datetime.now(timezone.utc)
                import time
                time.sleep(5)
        
        monitor_thread = threading.Thread(target=monitor_bot, daemon=True)
        monitor_thread.start()

    except Exception as e:
        logger.error(f"❌ Bot subprocess error: {e}")
        bot_status["running"] = False
        raise

# ------------------- Main -------------------
if __name__ == "__main__":
    # Start bot in a background thread (NOT daemon - keep it alive)
    bot_thread = threading.Thread(target=run_bot, daemon=False)
    bot_thread.start()
    
    # Give bot time to start
    import time
    time.sleep(3)
    
    # Start Flask server immediately so Render detects the open port
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"🌐 Starting web server on 0.0.0.0:{port}")
    
    # Keep the main thread alive forever
    try:
        app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("👋 Shutting down...")
        sys.exit(0)


