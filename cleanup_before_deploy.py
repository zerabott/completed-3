#!/usr/bin/env python3
"""
Clean up unnecessary files before deploying to Render/GitHub
"""
import os
import shutil

# Files to remove
FILES_TO_REMOVE = [
    # Test scripts
    "test_bot_connection.py",
    "test_comment_ranks.py",
    "test_database.py",
    "test_postgres.py",
    "test_postgresql_connection.py",
    "test_profile_contacts.py",
    "check_comments.py",
    "check_db_schema.py",
    "check_posts_schema.py",
    "check_schema.py",
    "check_tables.py",
    
    # Migration/fix scripts (already applied)
    "add_accepting_contacts_field.py",
    "add_extended_profile_fields.py",
    "apply_pg_migration.py",
    "auto_migrate_notifications.py",
    "cleanup_for_deploy.py",
    "fix_emoji_encoding.py",
    "fix_local_db.py",
    "fix_migration.py",
    "fix_notification_schema.py",
    "fix_postgres_connection.py",
    "migrate_profile_fields.py",
    "quick_add_accepting_contacts.py",
    
    # Broken/backup files
    "utils_broken.py",
    "comments_backup.py",
    
    # Other platform configs
    "replit.nix",
    "railway.json",
]

def cleanup():
    """Remove unnecessary files"""
    print("🧹 Cleaning up files before deployment...\n")
    
    removed = 0
    for filename in FILES_TO_REMOVE:
        try:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"✅ Removed: {filename}")
                removed += 1
        except Exception as e:
            print(f"❌ Error removing {filename}: {e}")
    
    print(f"\n✨ Removed {removed} files successfully!")
    print("\n📋 Next steps:")
    print("1. Review the .gitignore file")
    print("2. Initialize git: git init")
    print("3. Add files: git add .")
    print("4. Commit: git commit -m 'Initial commit - optimized bot'")
    print("5. Push to GitHub")
    print("6. Deploy to Render")

if __name__ == "__main__":
    cleanup()
