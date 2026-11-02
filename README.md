<div align="center">

# 🏦 Enterprise Internet Banking System
### A Full-Stack, AI-Powered Digital Banking Platform with Fraud Detection & Automated KYC

[![React](https://img.shields.io/badge/React-18-blue?style=for-the-badge&logo=react)](https://reactjs.org/)
[![Django](https://img.shields.io/badge/Django-5.0-green?style=for-the-badge&logo=django)](https://www.djangoproject.com/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-teal?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue?style=for-the-badge&logo=postgresql)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue?style=for-the-badge&logo=docker)](https://www.docker.com/)
[![Celery](https://img.shields.io/badge/Celery-Async-green?style=for-the-badge&logo=celery)](https://docs.celeryq.dev/)

**Secure • Scalable • AI-Driven • Cloud-Ready**

</div>

---

## 📖 Overview
The **Internet Banking System** is a production-grade, microservices-based banking application designed to handle core banking operations securely. It features real-time AI-powered fraud detection, automated document extraction (NID OCR), multilingual customer support (Bangla/English), and robust role-based access control.

Built with a **Django REST API** at its core, an isolated **FastAPI AI Microservice**, a blazing-fast **React frontend**, and backed by **PostgreSQL** and **Redis**. The entire stack is orchestrated using **Docker Compose** for one-command deployment.

---

## ✨ Key Features

### 🔐 Authentication & Security
- **JWT-based Authentication** with refresh token rotation.
- **Role-Based Access Control (RBAC):** Customer, Employee, Admin, Auditor.
- **2FA / OTP:** Secure SMS and Email OTP for login and transactions.
- **Audit Logging:** Every sensitive action is tracked with IP and User-Agent.

### 💸 Core Banking
- **Fund Transfer:** Real-time transfer between accounts with atomic transactions (ACID).
- **Bill Payments & Mobile Recharge.**
- **Virtual Card Management:** Issue, block/unblock, and set daily limits.
- **Loan Management:** Apply, evaluate, and track loans with AI-based credit scoring.

### 🧠 Artificial Intelligence (AI Service)
- **Fraud Detection (XGBoost):** Real-time transaction scoring (AUPRC: 0.87). High-risk transactions are auto-held.
- **SHAP Explainability:** Transparent AI—see exactly *why* a transaction was flagged.
- **NID OCR (EasyOCR):** Automated KYC extraction from NID cards (Front/Back).
- **Face Matching (dlib):** Compares NID photo with live selfie for KYC verification.
- **AI Chatbot (RAG + OpenAI):** 24/7 support in **Bangla & English** using FAISS vector search.
- **Model Retraining Pipeline:** Automated weekly model retraining via Celery Beat.

### 👑 Admin Dashboard
- Real-time statistics & Chart.js analytics.
- KYC Approval queue with OCR data & Tamper detection scores.
- Fraud Alert monitoring with SHAP force-plots.
- User management (Block/Unblock, Role change).

---

## 🛠️ Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | React 18, Bootstrap 5, Chart.js, Axios, React Router |
| **Backend (Core)** | Python 3.12, Django 5.0, Django REST Framework |
| **AI Microservice** | FastAPI, Scikit-learn, XGBoost, EasyOCR, OpenAI, LangChain |
| **Database** | PostgreSQL 16 |
| **Message Broker / Cache** | Redis 7 |
| **Background Tasks** | Celery, Celery Beat |
| **DevOps** | Docker, Docker Compose, Nginx (Reverse Proxy) |

---

## 🚀 Quick Start (Docker Setup)

Deploy the entire architecture (7 services) with a single command using Docker.

### Prerequisites
- Docker Desktop installed (Min 8GB RAM allocated).
- Git installed.

### 1. Clone the Repository
bash
git clone https://github.com/your-username/internet-banking.git
cd internet-banking

2. Setup Environment Variables
Copy the .env.example file and fill in your credentials (OpenAI API Key, Email SMTP, etc.).

bash
cp .env.example .env
3. Build & Run
bash
# Build and start all services in detached mode
docker-compose up --build -d
4. Access the Application
Service	URL
Frontend (React)	http://localhost:3000
Backend API (Swagger)	http://localhost:8000/api/docs/
AI Service (FastAPI)	http://localhost:9000/docs
Django Admin Panel	http://localhost:8000/admin/
(Default Admin: admin@ibs.com / Admin@12345 - Change immediately in production)

📸 Screenshots
(Here you will add your screenshots)

![Dashboard](docs/screenshots/dashboard.png)

![Admin Panel](docs/screenshots/admin-panel.png)

![Chatbot](docs/screenshots/chatbot.png)

🏗️ Project Architecture
text
├── backend/                 # Django REST API & Celery Workers
├── ai-service/              # FastAPI AI Microservice (OCR, Fraud, Chatbot)
├── frontend/                # React.js Application
├── nginx/                   # Nginx Reverse Proxy Configuration
├── docker-compose.yml       # Multi-container orchestration
└── Makefile                 # Useful Docker commands
🧪 Testing the API
Use the interactive Swagger UI at http://localhost:8000/api/docs/ to test endpoints.

Register a user via /api/auth/register/.

Login via /api/auth/login/ to obtain a JWT.

Authorize the Swagger UI with the JWT token.

Test fund transfer, KYC upload, etc.

🛡️ License
This project is licensed under the MIT License - see the LICENSE file for details.

<div align="center"> <i>Built with ❤️ for secure, intelligent banking.</i> </div> ```
