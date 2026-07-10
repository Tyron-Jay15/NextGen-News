# PythonAnywhere deployment

This project includes a dedicated settings module for PythonAnywhere
(`DJANGO_ENV=pythonanywhere`). It uses SQLite (or optional MySQL), in-memory
cache, DB sessions, and no Redis/Celery workers.

## 1. Upload the project

In a Bash console on PythonAnywhere:

```bash
cd ~
git clone <your-repo-url> News
# or upload a zip and unzip it
cd News
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Use the Python version available on your account (3.10–3.12 are typical).

## 2. Create `.env`

```bash
cp .env.example .env
nano .env
```

Set at least:

```env
DJANGO_ENV=pythonanywhere
DEBUG=False
SECRET_KEY=<long-random-string>
ALLOWED_HOSTS=yourusername.pythonanywhere.com
CSRF_TRUSTED_ORIGINS=https://yourusername.pythonanywhere.com
SITE_URL=https://yourusername.pythonanywhere.com
SECURE_SSL_REDIRECT=True
SERVE_MEDIA=True
DB_ENGINE=sqlite
```

Replace `yourusername` with your PythonAnywhere username.

### Optional: MySQL

1. Create a database in the PythonAnywhere Databases tab.
2. `pip install mysqlclient`
3. In `.env`:

```env
DB_ENGINE=mysql
DB_NAME=yourusername$nextgen_news
DB_USER=yourusername
DB_PASSWORD=...
DB_HOST=yourusername.mysql.pythonanywhere-services.com
```

## 3. Initialize the app

```bash
cd ~/News
source venv/bin/activate
mkdir -p logs media staticfiles
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py seed_public_articles
```

`seed_public_articles` loads published sample stories with sharp hero images.
Use this on **free accounts** where BBC/Panay scraping is blocked.

If your plan allows outbound HTTP, you can also try live scraping:

```bash
python manage.py setup_scraper_sources
python manage.py scrape_news
```

## 4. Web app configuration

**Web** tab → **Add a new web app** → Manual configuration → your Python version.

| Setting | Value |
|---------|--------|
| Source code | `/home/yourusername/News` |
| Working directory | `/home/yourusername/News` |
| Virtualenv | `/home/yourusername/News/venv` |
| WSGI file | edit to load `config.wsgi` (see below) |

### WSGI file

Replace the contents of the WSGI file with:

```python
import os
import sys

project_home = '/home/yourusername/News'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Ensure the project `.env` is in `project_home` so `python-decouple` can read it.

### Static / media mappings

| URL | Directory |
|-----|-----------|
| `/static/` | `/home/yourusername/News/staticfiles` |
| `/media/` | `/home/yourusername/News/media` |

Then click **Reload**.

## 5. Scheduled news scrape

Celery Beat is disabled on PythonAnywhere. Use **Tasks** → **Scheduled tasks**:

```bash
cd ~/News && source venv/bin/activate && python manage.py scrape_news
```

Suggested schedule: every hour (or every 15 minutes on a paid plan).

Optional image refresh:

```bash
cd ~/News && source venv/bin/activate && python manage.py refresh_article_images --scraped-only
```

## 6. Staff login

- Public site: `https://yourusername.pythonanywhere.com/`
- Staff portal (not linked on the public site): `/accounts/admin/login/`
- Django admin: `/admin/`

## Notes

- Live WebSocket notifications are not supported on standard PA web apps.
- Outbound scraping (BBC, Panay News) works on paid plans; free accounts have limited external network access to allowlisted sites.
- Keep `DEBUG=False` in production.
