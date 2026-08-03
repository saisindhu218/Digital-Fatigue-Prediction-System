# AI-Based Digital Fatigue & Productivity Risk Prediction System



An AI-powered full-stack application that monitors digital behavior, predicts fatigue and productivity risks, and provides personalized recommendations through real-time analytics. The system combines web and mobile platforms with Machine Learning to help users improve focus, productivity, and digital well-being.



## Project Overview

The rapid increase in digital device usage has resulted in issues such as digital fatigue, reduced productivity, and unhealthy screen-time habits. Existing applications primarily focus on tracking screen time and lack intelligent prediction, behavioral analysis, and cross-device integration.

The **AI-Based Digital Fatigue & Productivity Risk Prediction System** addresses these challenges by collecting behavioral data from both desktop and mobile devices, analyzing user activity using Machine Learning algorithms, and generating fatigue predictions, productivity insights, and personalized recommendations.

The system integrates a modern web dashboard, Flutter mobile application, FastAPI backend, and MongoDB database to provide an intelligent, scalable, and user-centric productivity monitoring platform.



## Key Features

* Secure User Authentication using JWT
* QR-Based Device Pairing for Cross-Device Synchronization
* Real-Time Activity Monitoring
* Screen Time & Application Usage Tracking
* Keyboard, Mouse, Idle Time & Session Analysis
* AI-Based Fatigue Prediction
* Productivity Risk Assessment
* Interactive Dashboard & Analytics
* Personalized Recommendations & Alerts
* Responsive Web & Mobile Applications



## Technology Stack

### Frontend

* React.js
* Flutter
* HTML5
* CSS3
* JavaScript

### Backend

* Python
* FastAPI
* REST APIs

### Database

* MongoDB Atlas

### Machine Learning

* Random Forest
* XGBoost
* Scikit-learn
* Pandas
* NumPy

### Authentication

* JSON Web Token (JWT)
* bcrypt

### Development Tools

* Visual Studio Code
* Android Studio
* Git & GitHub
* Postman



## System Architecture

The application follows a modular three-tier architecture consisting of:

* **Presentation Layer** – React Web Dashboard & Flutter Mobile Application
* **Application Layer** – FastAPI Backend, Authentication, Business Logic & Machine Learning Services
* **Data Layer** – MongoDB Atlas for secure storage of user information, activity logs, predictions, and recommendations

The system communicates through REST APIs, enabling secure and efficient data exchange between all components.



## Machine Learning Workflow

1. Collect user activity data from laptop and mobile devices.
2. Perform data preprocessing and feature extraction.
3. Train and evaluate Random Forest and XGBoost models.
4. Predict fatigue levels, productivity scores, and risk categories.
5. Display AI-generated insights through dashboards and analytics.
6. Generate personalized recommendations and real-time alerts.



## Project Structure

```
AI-Based-Digital-Fatigue-Productivity-Risk-Prediction-System/
│
├── frontend/                 # React Web Dashboard
│   ├── src/
│   ├── components/
│   ├── pages/
│   └── services/
│
├── mobile/                   # Flutter Mobile Application
│   ├── lib/
│   ├── screens/
│   ├── widgets/
│   └── services/
│
├── backend/                  # FastAPI Backend
│   ├── routes/
│   ├── models/
│   ├── services/
│   ├── ml_models/
│   └── main.py
│
├── database/
│
└── README.md
```



## Installation

### Prerequisites

* Python 3.10+
* Node.js (v16 or above)
* Flutter SDK
* MongoDB Atlas
* Android Studio / VS Code



### Clone Repository

```bash
git clone https://github.com/your-username/AI-Based-Digital-Fatigue-Productivity-Risk-Prediction-System.git

cd AI-Based-Digital-Fatigue-Productivity-Risk-Prediction-System
```



### 1 Run Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn main:app --reload
```



### 2 Run Frontend

```bash
cd frontend

npm install

npm start
```



### 3 Run Mobile Application

```bash
cd mobile

flutter pub get

flutter run
```



## Project Outcomes

## Output

| Login  |  Registration |
|----------------------|-----------|
| <img src="https://github.com/user-attachments/assets/85aa96b3-6633-4a01-b148-69087666cc4d" width="100%"> | <img src="https://github.com/user-attachments/assets/6aabf57c-9cc9-4757-8116-b6319a349451" width="100%"> |

<br>

| Dashboard  | Dashboard Insights |
|--------------------|--------------------|
| <img src="https://github.com/user-attachments/assets/fee7bae3-fc2c-4f0f-97a7-4b9209ec8b0f" width="100%">| <img src="https://github.com/user-attachments/assets/231b5500-30a0-4971-8931-2393bc747911" width="100%"> |

<br>

| Light Themed | AI Analytics Details |
|-------------------|---------------|
| <img src="https://github.com/user-attachments/assets/b44ce18b-9092-4a02-8ea5-87e3acd87076" width="100%"> | <img src="https://github.com/user-attachments/assets/b839edc1-d077-409b-a8b8-a91f1f3da624" width="100%"> |

<br>

| AI Analytics Overview | AI Prediction |
|-----------------|----------------|
| <img src="https://github.com/user-attachments/assets/e36ef405-8536-453d-b9e4-82843f9d6e92" width="100%"> | <img src="https://github.com/user-attachments/assets/93977463-0297-4ee3-b190-ce7d987c3b33" width="100%"> |

<br>

| Recommendations |  Device Pairing |
|--------------|--------------|
| <img src="https://github.com/user-attachments/assets/f53f2eae-d61c-4ed8-a282-e80c441fd1f1" width="100%"> | <img src="https://github.com/user-attachments/assets/088de252-3127-458f-a2e6-54045c560062" width="100%"> |

<br>

| User Profile |  Mobile Login |
|------------------|-------------------|
| <img src="https://github.com/user-attachments/assets/f8a3bafd-9731-42ec-8ed9-296c6efda9c7" width="100%"> | <img width="356" height="639" alt="Image" src="https://github.com/user-attachments/assets/e029d0d1-b325-4a1f-8526-cfbb2265a6c6" width="100%" /> |

<br>

|  Mobile Dashboard & Statistics  | Mobile Alerts & Settings |
|---------------|-----------------|
| <img src="https://github.com/user-attachments/assets/7159b608-0b61-4afa-9f8c-fb40cd3820f7" width="100%"> | <img src="https://github.com/user-attachments/assets/158f9d27-00e5-4aa3-bdd4-3e590ea9c932" width="100%"> |



## Future Enhancements

* Wearable device integration
* Deep Learning-based prediction models
* Advanced behavioral analytics
* Enhanced recommendation engine



## Team Members

* **Rachabattuni Sai Sindhu**
* **Reddy Akkamma Chandana**
* **Ragendu V. S**



## Academic Information
* **Project Title:** AI-Based Digital Fatigue & Productivity Risk Prediction System
* **Course:** Master of Computer Applications (MCA), Jain (Deemed-to-be)University, Jayanagar, Banglore
* **Semester:** IV Semester Major Project



