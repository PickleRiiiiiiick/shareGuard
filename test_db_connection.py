from sqlalchemy import create_engine, text

# Use the same connection string as your application
conn_str = "mssql+pyodbc://shareguard_user:YourStrongPassword123!@localhost/ShareGuard?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(conn_str)

with engine.connect() as connection:
    # Test basic connection
    result = connection.execute(text("SELECT CURRENT_USER;"))
    print("Current user:", result.scalar())
    
    # Test alembic_version table access
    try:
        result = connection.execute(text("SELECT * FROM alembic_version;"))
        print("Successfully queried alembic_version table")
    except Exception as e:
        print("Error querying alembic_version:", str(e))