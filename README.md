
---

# 🏠 Rental Housing API (Django)

A full-featured backend API for a housing rental platform in Germany, built with Django and DRF.

---

## 📌 Project Goals

- Manage property listings (CRUD) with status control (`active`/`inactive`)  
- Advanced search & filtering by:  
  - Keywords (title/description)  
  - Price range  
  - City (in Germany)  
  - Number of rooms  
  - Housing type (apartment, house, studio, etc.)  
- Sorting by price or date  
- User roles: **Tenant** vs **Landlord**  
- Booking system with confirmation flow  
- Reviews & ratings **only after completed booking**  
- Search history & view history  
- Popular listings based on views  
- RESTful API with JWT authentication  
- OpenAPI (Swagger) documentation  
- MySQL as main database  
- Docker containerization  
- Deployment-ready for AWS EC2  
- Comprehensive unit and integration tests** (100% coverage for core logic)

---

## 🛠️ Technologies Used

- **Backend**: Python 3.12, Django 5.2, Django REST Framework  
- **Authentication**: JWT (`djangorestframework-simplejwt`)  
- **Database**: MySQL (production), SQLite (development)  
- **API Docs**: `drf-spectacular` (OpenAPI 3.0 + Swagger UI)  
- **Testing**: Built-in `unittest`, `Django TestCase`, `APITestCase`  
- **Deployment**: Docker, Docker Compose  
- **Cloud**: AWS EC2 + RDS (fully configured)  
- **Other**: `django-environ`, `Faker`, `gunicorn`, `mysqlclient`  

---

## 🧪 Testing

The project includes **extensive unit and integration tests** covering:

- User registration & authentication  
- Listing creation, filtering, and permissions  
- Booking logic (overlap prevention, role checks, cancellation rules)  
- Review validation (only after completed stay)  
- History tracking (searches, views)  
- Popular listings & search queries  

Run tests with:

```bash
python manage.py test
```

All core business rules are validated both at the **model** and **view** levels.

---

## 📂 Project Structure

```
ich_django_final_project/
├── apps/
│   ├── users/          # Custom User model, registration, groups
│   ├── listings/       # Property listings, search, filters, popular
│   ├── bookings/       # Booking logic, email notifications
│   ├── reviews/        # Reviews with validation
│   ├── history/        # Search & view history
│   └── common/         # Shared models (BaseModel), permissions, validators
├── utils/              # Helpers (if any)
├── manage.py
├── requirements.txt
├── .env.example
├── .env                # ← NOT in Git!
├── Dockerfile
├── docker-compose.yml
└── ...
```

---

## ⚙️ Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ich_django_final_project.git  
cd ich_django_final_project
```

### 2. Create virtual environment & install dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 3. Configure environment

Copy `.env.example` to `.env` and fill in your secrets:

```ini
# .env
DEBUG=True
SECRET_KEY=your-50+-char-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# MySQL (optional)
MYSQL=False
DB_NAME=ich_django_final_project
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

> 🔒 **Never commit `.env` to Git!**

### 4. Run migrations & start server

```bash
python manage.py migrate
python manage.py createsuperuser  # optional
python manage.py runserver
```

### 5. Explore the API

- **Swagger UI**: http://127.0.0.1:8000/api/docs/  
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

---

## 🔐 Authentication

- **Register**: `POST /api/v1/users/register/`  
- **Login**: `POST /api/v1/users/login/` → returns JWT tokens  
- **Protected endpoints**: require `Authorization: Bearer <access_token>`  
- **Roles**:  
  - `Landlords` — create/edit/delete own listings  
  - `Tenants` — browse, book, review  

---

## 📊 Key Business Logic

### ✅ Booking Rules
- Only tenants can create bookings  
- Landlords confirm/reject bookings  
- Tenants can cancel ≥7 days before start  

### ✅ Review Rules
A user can leave a review **only if**:
- They are authenticated  
- They have a **completed booking** for that listing  
- The booking’s `end_date` is in the past  

> Enforced in `ReviewSerializer.validate_booking()` and `validate_booking_for_review()`.

### ✅ Data Integrity
- Soft-delete via `BaseModel` (`is_deleted`)  
- Postal code validation for Germany (`\d{5}`)  
- No overlapping bookings (`validate_no_overlapping_booking`)  
- Prevent self-booking (`validate_not_own_listing`)  

---

## 🚀 Deployment (AWS EC2)

✅ **Fully implemented and tested**

### Steps:
1. Launch Ubuntu 22.04 EC2 instance  
2. Install Docker:  
   ```bash
   sudo apt update && sudo apt install -y docker.io
   sudo usermod -aG docker ubuntu
   ```
3. Upload project (via Git or `scp`)  
4. Create `.env` on server with production settings:  
   ```ini
   DEBUG=False
   ALLOWED_HOSTS=your-ec2-public-ip
   MYSQL=True
   DB_NAME=ich_django_final_project
   DB_USER=************
   DB_PASSWORD=***************
   DB_HOST=********************
   DB_PORT=3306
   ```
5. Build and run:  
   ```bash
   docker build -t rental-app .
   docker run -d -p 8000:8000 --name rental-app rental-app
   ```
6. Access API: `http://<EC2_PUBLIC_IP>:8000/api/docs/`

> 💡 **Note**: The app connects to the **external MySQL server** provided by ITCareerHub (`ich-edit.edu.itcareerhub.de`).

---

## 📜 License

This project is for educational purposes only.  
© 2025 Alexander Pankow — Final Project for **Python Advanced** at ITCareerHub.de.

---

<br><hr><br>

# 🏠 API для системы аренды жилья (Django)

Полнофункциональный бэкенд для платформы аренды жилья в Германии на Django и DRF.

---

## 📌 Цели проекта

- Управление объявлениями (CRUD) со статусом (`активно`/`неактивно`)  
- Расширенный поиск и фильтрация по:  
  - Ключевым словам (в заголовке/описании)  
  - Диапазону цены  
  - Городу (в Германии)  
  - Количеству комнат  
  - Типу жилья (квартира, дом, студия и т.д.)  
- Сортировка по цене или дате добавления  
- Разделение ролей: **Арендатор** и **Арендодатель**  
- Система бронирования с подтверждением  
- Отзывы и рейтинги **только после завершённого бронирования**  
- История поиска и просмотров  
- Популярные объявления по количеству просмотров  
- REST API с JWT-аутентификацией  
- Документация OpenAPI (Swagger)  
- MySQL как основная БД  
- Контейнеризация через Docker  
- Готовность к развёртыванию на AWS EC2  
- Полные unit- и интеграционные тесты** (100% покрытие ключевой логики)

---

## 🛠️ Используемые технологии

- **Бэкенд**: Python 3.12, Django 5.2, Django REST Framework  
- **Аутентификация**: JWT (`djangorestframework-simplejwt`)  
- **База данных**: MySQL (продакшен), SQLite (разработка)  
- **Документация**: `drf-spectacular` (OpenAPI 3.0 + Swagger UI)  
- **Тестирование**: встроенные `unittest`, `Django TestCase`, `APITestCase`  
- **Деплой**: Docker, Docker Compose  
- **Облако**: AWS EC2 + RDS (полностью настроено)  
- **Прочее**: `django-environ`, `Faker`, `gunicorn`, `mysqlclient`  

---

## 🧪 Тестирование

Проект включает **масштабные unit- и интеграционные тесты**, охватывающие:

- Регистрацию и аутентификацию пользователей  
- Создание, фильтрацию объявлений и проверку прав доступа  
- Логику бронирования (предотвращение пересечений, роли, отмена)  
- Валидацию отзывов (только после завершённого проживания)  
- Историю поиска и просмотров  
- Популярные объявления и запросы  

Запуск тестов:

```bash
python manage.py test
```

Все ключевые бизнес-правила протестированы как на уровне **моделей**, так и на уровне **API**.

---

## ⚙️ Установка и запуск

(Инструкции идентичны английской версии)

---

## 🚀 Деплой (AWS EC2)

✅ **Полностью реализовано и протестировано**

Приложение подключается к **внешнему MySQL-серверу** (`ich-edit.edu.itcareerhub.de`), предоставленному ITCareerHub.

---

## 🤝 Автор: Александр Панков

Проект выполнен как **финальная работа** по курсу **Python Advanced** в ITCareerHub.de.

---

<br><hr><br>

# 🏠 Rental Housing API (Django)

Ein vollständiges Backend-API für eine Wohnungsvermietungsplattform in Deutschland, entwickelt mit Django und DRF.

---

## 📌 Projektziele

- Verwaltung von Wohnungsanzeigen (CRUD) mit Status (`aktiv`/`inaktiv`)  
- Erweiterte Suche & Filterung nach:  
  - Stichworten (Titel/Beschreibung)  
  - Preisspanne  
  - Stadt (in Deutschland)  
  - Anzahl der Zimmer  
  - Wohnungsart (Wohnung, Haus, Studio usw.)  
- Sortierung nach Preis oder Datum  
- Benutzerrollen: **Mieter** vs **Vermieter**  
- Buchungssystem mit Bestätigungsprozess  
- Bewertungen & Sterne **nur nach abgeschlossener Buchung**  
- Suchverlauf & Ansichtsverlauf  
- Beliebte Wohnungen basierend auf Aufrufen  
- RESTful API mit JWT-Authentifizierung  
- OpenAPI-Dokumentation (Swagger)  
- MySQL als Hauptdatenbank  
- Containerisierung mit Docker  
- Bereit für Bereitstellung auf AWS EC2  
- Umfassende Unit- und Integrationstests** (100 % Abdeckung der Kernlogik)

---

## 🛠️ Verwendete Technologien

- **Backend**: Python 3.12, Django 5.2, Django REST Framework  
- **Authentifizierung**: JWT (`djangorestframework-simplejwt`)  
- **Datenbank**: MySQL (Produktion), SQLite (Entwicklung)  
- **API-Dokumentation**: `drf-spectacular` (OpenAPI 3.0 + Swagger UI)  
- **Tests**: `unittest`, `Django TestCase`, `APITestCase`  
- **Deployment**: Docker, Docker Compose  
- **Cloud**: AWS EC2 + RDS (vollständig konfiguriert)  
- **Sonstiges**: `django-environ`, `Faker`, `gunicorn`, `mysqlclient`  

---

## 🧪 Tests

Das Projekt enthält **umfangreiche Unit- und Integrationstests** für:

- Benutzerregistrierung & Authentifizierung  
- Erstellung, Filterung und Berechtigungen bei Wohnungsanzeigen  
- Buchungslogik (Überlappungsvermeidung, Rollen, Stornierungsregeln)  
- Bewertungsvalidierung (nur nach abgeschlossenem Aufenthalt)  
- Verlauf von Suchanfragen und Aufrufen  
- Beliebte Wohnungen und Suchbegriffe  

Tests ausführen mit:

```bash
python manage.py test
```

Alle Kernregeln sind sowohl auf **Model-** als auch auf **View-Ebene** getestet.

---

## ⚙️ Einrichtung und Ausführung

(Anleitungen identisch zur englischen Version)

---

## 🚀 Bereitstellung (AWS EC2)

✅ **Vollständig implementiert und getestet**

Die Anwendung verbindet sich mit dem **externen MySQL-Server** (`ich-edit.edu.itcareerhub.de`), bereitgestellt von ITCareerHub.

---

## 🤝 Autor: Alexander Pankow

Dieses Projekt wurde als **Abschlussarbeit** für den **Python Advanced**-Kurs bei ITCareerHub.de erstellt.

---