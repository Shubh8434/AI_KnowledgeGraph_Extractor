#!/usr/bin/env python3
"""
Database migration management script for AI-Powered Knowledge Graph Builder
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    """Main migration management function"""
    
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <command>")
        print("\nAvailable commands:")
        print("  init        - Initialize database with migrations")
        print("  upgrade     - Apply all pending migrations")
        print("  downgrade   - Rollback last migration")
        print("  revision    - Create a new migration")
        print("  history     - Show migration history")
        print("  current     - Show current migration")
        print("  seed        - Run seed script to populate sample data")
        print("  reset       - Reset database and run all migrations + seed")
        return
    
    command = sys.argv[1].lower()
    
    if command == "init":
        print("🚀 Initializing database...")
        # Run initial migration
        if run_command("alembic upgrade head", "Applying initial migration"):
            print("✅ Database initialized successfully!")
        else:
            print("❌ Database initialization failed!")
            sys.exit(1)
    
    elif command == "upgrade":
        run_command("alembic upgrade head", "Applying pending migrations")
    
    elif command == "downgrade":
        run_command("alembic downgrade -1", "Rolling back last migration")
    
    elif command == "revision":
        if len(sys.argv) < 3:
            print("Usage: python migrate.py revision <message>")
            return
        message = " ".join(sys.argv[2:])
        run_command(f'alembic revision --autogenerate -m "{message}"', f"Creating migration: {message}")
    
    elif command == "history":
        run_command("alembic history", "Showing migration history")
    
    elif command == "current":
        run_command("alembic current", "Showing current migration")
    
    elif command == "seed":
        print("🌱 Running seed script...")
        try:
            import seed_data
            seed_data.create_sample_documents()
            print("✅ Seed data created successfully!")
        except Exception as e:
            print(f"❌ Seed script failed: {e}")
            sys.exit(1)
    
    elif command == "reset":
        print("🔄 Resetting database...")
        
        # Remove existing database
        db_files = ["knowledge_graph.db", "knowledge_graph.db-journal"]
        for db_file in db_files:
            if os.path.exists(db_file):
                os.remove(db_file)
                print(f"🗑️  Removed {db_file}")
        
        # Run migrations
        if run_command("alembic upgrade head", "Applying migrations"):
            # Run seed
            print("🌱 Running seed script...")
            try:
                import seed_data
                seed_data.create_sample_documents()
                print("✅ Database reset and seeded successfully!")
            except Exception as e:
                print(f"❌ Seed script failed: {e}")
                sys.exit(1)
        else:
            print("❌ Database reset failed!")
            sys.exit(1)
    
    else:
        print(f"❌ Unknown command: {command}")
        print("Run 'python migrate.py' to see available commands")
        sys.exit(1)

if __name__ == "__main__":
    main()