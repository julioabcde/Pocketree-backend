# Pocketree API

Backend API untuk aplikasi Pocketree - Aplikasi manajemen keuangan pribadi yang modern dan powerful.

## Deskripsi

Pocketree API adalah backend service yang dibangun dengan FastAPI untuk mengelola transaksi keuangan, autentikasi pengguna, dan berbagai fitur manajemen keuangan pribadi lainnya. API ini menggunakan PostgreSQL sebagai database dan SQLAlchemy untuk ORM dengan dukungan async/await untuk performa optimal.

## Tech Stack

- **Framework**: FastAPI 0.135.1
- **Python**: 3.14+
- **Database**: PostgreSQL (dengan dukungan async via asyncpg)
- **ORM**: SQLAlchemy 2.0.48 (Async)
- **Migration**: Alembic 1.18.4
- **Authentication**: JWT (python-jose)
- **Password Hashing**: Passlib dengan Bcrypt
- **Validation**: Pydantic 2.12.5
- **Logging**: Loguru
- **Server**: Uvicorn dengan dukungan standard

## Fitur

- **Autentikasi & Autorisasi**
  - JWT-based authentication
  - Password hashing dengan bcrypt
  - Secure token management

- **Manajemen User**
  - User registration & management
  - User profiles dengan timestamps

- **Manajemen Transaksi**
  - CRUD operations untuk transaksi keuangan
  - Tracking income & expenses

- **Security**
  - Environment-based configuration
  - Secure password handling
  - Protected routes

## Prerequisites

Pastikan sistem Anda sudah terinstall:

- Python 3.14+ ([Download](https://www.python.org/downloads/))
- PostgreSQL 12+ ([Download](https://www.postgresql.org/download/))
- pip (Python package manager)
- pip-tools (untuk dependency management) - `pip install pip-tools`
- Git

## Installation & Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd pocketree-api
```

### 2. Setup Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install pip-tools untuk dependency management
pip install pip-tools

# Install semua dependencies
pip install -r requirements.txt
```

> **Note**: pip-tools digunakan untuk mengelola dependencies dan menghindari dependency hell. Lihat section [Dependency Management](#dependency-management---menghindari-dependency-hell) untuk detail lengkap.

### 4. Setup Environment Variables

Buat file `.env` di root directory:

```env
# Database Configuration
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/pocketree

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

**PENTING:**

- Ganti `username` dan `password` dengan kredensial PostgreSQL Anda
- Generate SECRET_KEY yang strong untuk production:
  ```python
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```
- File `.env` sudah di-ignore di Git untuk keamanan

### 5. Setup Database

#### Buat Database PostgreSQL

```sql
CREATE DATABASE pocketree;
```

#### Atau via psql command line:

```bash
psql -U postgres
CREATE DATABASE pocketree;
\q
```

### 6. Run Database Migrations

```bash
# Generate migration (jika ada perubahan model)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head
```

## Running the Application

### Development Mode

```bash
uvicorn app.main:app --reload
```

Server akan berjalan di: `http://localhost:8000`

### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Setelah aplikasi berjalan, akses dokumentasi interaktif di:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Project Structure

```
pocketree-api/
│
├── alembic/                    # Database migrations
│   ├── versions/              # Migration scripts
│   │   ├── 032ff9754aef_add_timestamps_to_users.py
│   │   └── df64d5a1d867_create_users_table.py
│   ├── env.py                 # Alembic environment config
│   └── script.py.mako         # Migration template
│
├── app/                        # Main application
│   ├── core/                   # Core functionality
│   │   ├── config.py          # Settings & configuration
│   │   ├── security.py        # Security utilities
│   │   └── logger.py          # Logging configuration
│   │
│   ├── db/                     # Database layer
│   │   ├── base.py            # Base model
│   │   ├── session.py         # Database session
│   │   └── mixins.py          # Database mixins
│   │
│   ├── modules/               # Feature modules
│   │   ├── auth/              # Authentication
│   │   │   ├── model.py
│   │   │   ├── schema.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   ├── users/             # User management
│   │   │   ├── model.py
│   │   │   ├── schema.py
│   │   │   ├── service.py
│   │   │   └── router.py
│   │   │
│   │   └── transactions/      # Transaction management
│   │       ├── model.py
│   │       ├── schema.py
│   │       ├── service.py
│   │       └── router.py
│   │
│   └── main.py                # Application entry point
│
├── .env                        # Environment variables (not in git)
├── .gitignore                 # Git ignore rules
├── alembic.ini                # Alembic configuration
├── pyproject.toml             # Project metadata & tools
├── requirements.in            # Direct dependencies
└── requirements.txt           # Pinned dependencies
```

## Development

### Code Formatting

Project ini menggunakan Ruff untuk linting dan formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .
```

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "your migration message"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history
```

### Dependency Management - Menghindari Dependency Hell

Project ini menggunakan **pip-tools** untuk mengelola dependencies dengan clean dan reproducible, menghindari "dependency hell".

#### Konsep: requirements.in vs requirements.txt

**requirements.in** - Top-level dependencies yang ditulis manual:

```
fastapi
sqlalchemy
asyncpg
```

**requirements.txt** - Fully resolved dependency tree (auto-generated):

```
fastapi==0.135.1
starlette==0.52.1  # transitive dependency
anyio==4.12.1       # transitive dependency
...
```

#### Setup pip-tools (One-time)

```bash
pip install pip-tools
```

#### Menambah Dependency Baru

```bash
# 1. Tambahkan ke requirements.in
echo "new-package" >> requirements.in

# 2. Compile untuk resolve all dependencies
pip-compile requirements.in

# 3. Install
pip install -r requirements.txt
```

#### Update Dependencies

```bash
# Update semua ke versi terbaru (hati-hati!)
pip-compile --upgrade requirements.in

# Update package tertentu saja
pip-compile --upgrade-package fastapi requirements.in
```

#### Benefits

- **Clean & Readable** - `requirements.in` hanya berisi dependencies yang benar-benar dibutuhkan
- **Reproducible** - `requirements.txt` lock exact versions untuk semua developer
- **Safe Updates** - `pip-compile` ensures compatible dependency tree
- **No Conflicts** - Menghindari version conflicts antar dependencies

#### Important Notes

- **Edit**: `requirements.in` (manually)
- **Jangan edit**: `requirements.txt` (auto-generated)
- **Commit both files** ke Git
- Run `pip-compile` setiap kali ubah `requirements.in`

## Security Best Practices

1. **Never commit `.env` file** - File ini sudah di-ignore di Git
2. **Never commit credentials** - Gunakan environment variables
3. **Use strong SECRET_KEY** - Generate dengan `secrets.token_urlsafe(32)`
4. **Keep dependencies updated** - Regular security updates
5. **Use HTTPS in production** - Always use SSL/TLS
6. **Validate input data** - Pydantic schemas untuk validation
7. **Rate limiting** - Implement rate limiting untuk API endpoints (upcoming)

## Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# Run with coverage
pytest --cov=app tests/
```

## Environment Variables Reference

| Variable                      | Description                       | Example                                                   |
| ----------------------------- | --------------------------------- | --------------------------------------------------------- |
| `DATABASE_URL`                | PostgreSQL connection URL (async) | `postgresql+asyncpg://user:pass@localhost:5432/pocketree` |
| `SECRET_KEY`                  | JWT secret key for token signing  | `your-super-secret-key-change-in-production`              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time         | `60`                                                      |

## Troubleshooting

### Database Connection Error

```
Solution: Pastikan PostgreSQL running dan credentials di .env benar
Check: pg_isready -h localhost -p 5432
```

### Import Error

```
Solution: Pastikan virtual environment aktif dan dependencies terinstall
Check: pip list | grep fastapi
```

### Migration Error

```
Solution: Check database connection dan pastikan database exists
Check: alembic current
```

## License

This project is proprietary and confidential.
Unauthorized copying or distribution is strictly prohibited.

## Contributors

- Julio
- Charles Cahyadi


## Links

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

