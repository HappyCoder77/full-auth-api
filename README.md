# Full-Auth API & Digital Sticker Management System
![Django](https://img.shields.io/badge/Django-092E20?style=for-the-badge&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-ff1709?style=for-the-badge&logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=json-web-tokens)
![Tests](https://img.shields.io/badge/Tests-500+-success?style=for-the-badge&logo=python)

## 🚀 Overview
A high-performance, production-ready RESTful API designed to manage digital sticker collections. This system solves the complexity of multi-role user management and real-time digital asset allocation for collectors, retailers, and sponsors.



## 🛠️ Tech Stack & Architecture
* **Backend:** Python 3.x / Django 4.x
* **API Framework:** Django REST Framework (DRF)
* **Database:** PostgreSQL (Optimized with indexing for fast asset retrieval)
* **Authentication:** Stateless JWT (via `djangorestframework-simplejwt`)
* **Architecture:** Modular Monolith (Separated by apps: `authentication`, `albums`, `commerce`, `promotions`)

## 🔑 Key Features
* **Advanced Authentication:** Custom user model using Email as the primary identifier. No-username logic implemented by overriding `BaseUserManager` to handle `REQUIRED_FIELDS` efficiently.
* **Scalable Multi-Role System:** Granular permission control for three distinct user types (Collector, Retailer, Sponsor).
* **The `/albums` Core:** A sophisticated engine that manages digital album creation, sticker slot allocation, and progress tracking per user.
* **Secure Transactions:** Integer-based logic for commerce and promotions to ensure data integrity during sticker exchanges.

## 🛡️ Quality Assurance
This project is built with a **security-first and stability-first mindset**. I maintained a rigorous testing workflow to ensure the system is bulletproof.

* **Unit Tests:** Over 500 tests covering models, serializers, and custom permissions.
* **Integration Tests:** End-to-end validation of the JWT login flow and sticker acquisition.
* **Edge Case Handling:** Specific tests for data isolation (ensuring Users can't access unauthorized albums) and token expiration.
* **Development Workflow:** Strictly followed a **Working Branch** strategy to maintain a clean and deployable `main` branch at all times.

## ⚙️ Installation & Setup
1. **Clone the repo:**
   ```bash
   git clone [https://github.com/HappyCoder77/full-auth-api.git](https://github.com/HappyCoder77/full-auth-api.git)
   ```
2. Environment Variables: Create a .env file and add your SECRET_KEY and PostgreSQL credentials.
3. Install Dependencies:
4. ```bash
   pip install -r requirements.txt
   ```
5. Run the Test Suite:
6. ```bash
   python manage.py test
   ```
Developed by Saul - Software Engineer focused on robust Backend Architectures.









