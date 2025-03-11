# Setup Instructions
    Clone Repository
```
git clone https://github.com/fadjar340/sybase-postgres-proxy
cd sybase-postgres-proxy
```
# Initialize Environment

```
cp .env.example .env
mkdir -p config/ssl
```

# Build & Start

```
docker compose up proxy migration web-frontend web-backend
```
