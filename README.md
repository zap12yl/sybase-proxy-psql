# Sybase to PostgreSQL Proxy Modified Version
Enterprise-grade migration solution with web interface and authentication.
Credit to [fadjar340](https://github.com/fadjar340)

## Project Structure
```markdown
sybase-postgres-proxy/
├── .env.example
├── docker-compose.yml
├── README.md
├── proxy/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── query_handler.py
│   │   ├── connection_manager.py
│   │   └── protocol_handler.py
│   ├── Dockerfile
│   └── requirements.txt
├── migration/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── migrator.py
│   │   ├── schema_translator.py
│   │   ├── data_mover.py
│   │   └── sp_converter.py
│   ├── Dockerfile
│   └── requirements.txt
├── webapp/
│   ├── backend/
│   │   ├── src/
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   │   ├── migration.py
│   │   │   │   └── auth.py
│   │   │   └── models.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── frontend/
│       ├── src/
│       │   ├── components/
│       │   │   ├── MigrationWizard.jsx
│       │   │   └── StatusMonitor.jsx
│       │   ├── App.js
│       │   └── index.js
│       ├── public/
│       │   └── index.html
│       ├── Dockerfile
│       ├── package.json
│       └── nginx.conf
└── scripts/
    ├── entrypoint.sh
    └── init_db.py
```

### **Key Features**

1. **Authentication Methods**
   - Environment variable credentials
   - JWT token validation

2. **Migration Tools**
   - Schema conversion
   - Data type mapping
   - Stored procedure translation
   - Batch data migration

3. **Web Interface**
   - Real-time progress monitoring
   - Migration configuration
   - Connection statistics
   - Log viewer

4. **Security**
   - SSL/TLS encryption (optional)
   - Password hashing (bcrypt)
   - Role-based access control
   - Token revocation


## Installation

[See detailed setup instructions](docs/SETUP.md)


## Usage

```bash
# Connect via Sybase client
tsql -S localhost -U admin -P password -D database

# Access web interface
http://localhost:3000
