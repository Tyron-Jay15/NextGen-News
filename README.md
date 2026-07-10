# NextGen News Management System

A production-ready Django news portal with editorial workflow, CMS, analytics, REST API, and AI-ready architecture.

## Features

- **Public Website** — Homepage, categories, article pages, search, newsletter
- **Editorial Workflow** — Draft → Review → Fact Check → Approval → Publish
- **CMS Dashboard** — Article management, comment moderation, analytics charts
- **REST API** — JWT authentication, full CRUD for articles, categories, authors
- **Real-time** — WebSocket notifications via Django Channels
- **Background Tasks** — Celery for analytics aggregation and scheduled publishing
- **SEO** — Sitemaps, Open Graph, Twitter Cards, Schema.org NewsArticle
- **Security** — CSRF, XSS headers, rate limiting, audit logs, RBAC

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | Django 5.x / 6.x |
| Database | PostgreSQL (SQLite for dev) |
| Cache | Redis |
| Task Queue | Celery |
| WebSockets | Django Channels |
| API | Django REST Framework + JWT |
| Frontend | Bootstrap 5, Chart.js, CKEditor 5 |
| Deployment | Docker, Gunicorn, Nginx |

## Quick Start

### Local Development

```bash
# Clone and setup
cd News
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
copy .env.example .env

# Database
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

Visit http://localhost:8000

**Default credentials (after seed):**
- Admin: `admin@nextgennews.com` / `Admin@12345`
- Reporter: `reporter@nextgennews.com` / `Reporter@12345`
- Staff portal (not linked on the public site): `/accounts/admin/login/`

### Docker Production

```bash
cp .env.example .env
docker-compose up -d --build
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py seed_data
docker-compose exec web python manage.py createsuperuser
```

## Project Structure

```
News/
├── accounts/          # Authentication, roles, user profiles
├── news/              # Articles, bookmarks, newsletter
├── categories/        # Categories and tags
├── authors/           # Author profiles
├── media_library/     # Media management
├── comments/          # Comments and moderation
├── advertisements/    # Ad management
├── analytics/         # Visitor tracking and charts
├── notifications/     # Email, push, in-app notifications
├── dashboard/         # Admin dashboard, settings, audit logs
├── search/            # Instant search and autocomplete
├── api/               # REST API endpoints
├── config/            # Settings, middleware, Celery, ASGI
├── templates/         # HTML templates
├── static/            # CSS, JavaScript
├── media/             # Uploaded files
├── nginx/             # Nginx configuration
└── tests/             # Integration tests
```

## User Roles

| Role | Permissions |
|------|------------|
| Super Admin | Full system access |
| Admin | User management, settings, publish |
| Chief Editor | Approve and publish articles |
| Editor | Review and edit articles |
| Reporter | Create and submit articles |
| Photographer | Upload media |
| Contributor | Submit articles |
| Moderator | Comment moderation |
| Registered Reader | Comment, bookmark |
| Guest | Read public content |

## API Endpoints

| Endpoint | Description |
|----------|------------|
| `POST /api/auth/token/` | Obtain JWT token |
| `GET /api/articles/` | List articles |
| `GET /api/articles/{id}/` | Article detail |
| `GET /api/categories/` | List categories |
| `GET /api/authors/` | List authors |
| `GET /api/search/?q=` | Search articles |
| `GET /api/analytics/` | Analytics data (admin) |

## Database Schema (ER Diagram)

```mermaid
erDiagram
    User ||--o| UserProfile : has
    User }o--|| Role : belongs_to
    User ||--o| AuthorProfile : has
    User ||--o{ Bookmark : creates
    User ||--o{ ReadingHistory : has
    User ||--o{ Notification : receives
    User ||--o{ Comment : writes

    AuthorProfile ||--o{ Article : writes
    Category ||--o{ Article : contains
    Category ||--o{ Category : parent_of
    Tag }o--o{ Article : tagged

    Article ||--o{ ArticleRevision : has
    Article ||--o{ ArticleMedia : contains
    Article ||--o{ Comment : has
    Article ||--o{ ArticleView : tracked

    Comment ||--o{ Comment : replies
    Comment ||--o{ CommentVote : has
    Comment ||--o{ CommentReport : has

    Advertisement ||--o{ AdClick : tracks
    Advertisement ||--o{ AdImpression : tracks

    MediaFolder ||--o{ MediaFile : contains
    VisitorLog }o--|| DailyAnalytics : aggregates
```

## System Flow

```mermaid
flowchart TD
    A[Visitor] --> B[Homepage]
    B --> C[Browse Categories]
    B --> D[Search Articles]
    C --> E[Article Detail]
    D --> E
    E --> F[Read / Comment / Share / Bookmark]

    G[Reporter] --> H[Create Article]
    H --> I[Save Draft]
    I --> J[Submit for Review]
    J --> K[Editor Review]
    K --> L[Fact Check]
    L --> M[Chief Editor Approval]
    M --> N[Schedule / Publish]
    N --> B

    O[Authentication] --> P[Dashboard]
    P --> Q[CRUD Modules]
    Q --> R[(PostgreSQL)]
    R --> S[Analytics]
    S --> B
```

## Use Case Diagram

```mermaid
graph LR
    Guest((Guest)) --> UC1[Read Articles]
    Guest --> UC2[Search News]
    Guest --> UC3[Subscribe Newsletter]

    Reader((Registered Reader)) --> UC1
    Reader --> UC4[Comment]
    Reader --> UC5[Bookmark]

    Reporter((Reporter)) --> UC6[Create Article]
    Reporter --> UC7[Save Draft]

    Editor((Editor)) --> UC8[Review Article]
    Editor --> UC9[Moderate Comments]

    ChiefEditor((Chief Editor)) --> UC10[Approve Article]
    ChiefEditor --> UC11[Publish Article]

    Admin((Admin)) --> UC12[Manage Users]
    Admin --> UC13[View Analytics]
    Admin --> UC14[Manage Ads]
```

## Class Diagram

```mermaid
classDiagram
    class User {
        +email: str
        +role: Role
        +can_edit_articles()
        +can_publish_articles()
    }
    class Role {
        +name: str
        +permissions: JSON
    }
    class Article {
        +title: str
        +status: str
        +published_at: datetime
        +increment_views()
    }
    class ArticleService {
        +get_published()
        +transition_status()
        +prepare_article()
    }
    class Category {
        +name: str
        +slug: str
        +parent: Category
    }
    class AuthorProfile {
        +display_name: str
        +biography: str
    }
    class Comment {
        +body: str
        +status: str
    }
    User --> Role
    User --> AuthorProfile
    AuthorProfile --> Article
    Category --> Article
    Article --> Comment
    ArticleService ..> Article
```

## Sequence Diagram — Article Publish Flow

```mermaid
sequenceDiagram
    participant R as Reporter
    participant CMS as Dashboard
    participant S as ArticleService
    participant DB as Database
    participant C as Celery
    participant P as Public Site

    R->>CMS: Create Article
    CMS->>S: prepare_article()
    S->>DB: Save Draft
    R->>CMS: Submit for Review
    CMS->>S: transition_status(pending_review)
    S->>DB: Update Status
    Note over CMS: Editor & Chief Editor review
    CMS->>S: transition_status(published)
    S->>DB: Set published_at
    S->>C: send_breaking_news_alert (if breaking)
    C->>P: Update homepage cache
    P-->>R: Article live
```

## Deployment Guide

### PythonAnywhere (recommended for shared hosting)

See **[PYTHONANYWHERE.md](PYTHONANYWHERE.md)** for a full checklist.

Quick start: set `DJANGO_ENV=pythonanywhere` in `.env`, install requirements in a virtualenv,
run `migrate` + `collectstatic`, point the WSGI file at `config.wsgi`, and map `/static/`
and `/media/` in the Web tab. Schedule `python manage.py scrape_news` under Tasks.

### Prerequisites (VPS / Docker)
- Python 3.12+
- PostgreSQL 16+
- Redis 7+
- Nginx (production)

### Production Checklist (VPS)

1. Set `DJANGO_ENV=production` in `.env`
2. Generate a strong `SECRET_KEY`
3. Configure PostgreSQL credentials
4. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` to your domain
5. Enable `SECURE_SSL_REDIRECT=True`
6. Configure email SMTP settings
7. Run `python manage.py collectstatic`
8. Start Gunicorn + Nginx + Celery workers

### Gunicorn (manual)

```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### Celery

```bash
celery -A config worker -l info
celery -A config beat -l info
```

On PythonAnywhere, skip Celery and use Scheduled Tasks instead (see PYTHONANYWHERE.md).
## Running Tests

```bash
python manage.py test
pytest
```

## License

MIT License — NextGen News Management System
