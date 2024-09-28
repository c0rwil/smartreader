from smartreader.database import engine, Base

# Drop all tables
Base.metadata.drop_all(bind=engine)

# Create all tables
Base.metadata.create_all(bind=engine)

print("Database has been reset.")
