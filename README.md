# AUSSIZ-ISMS
AUSSIZ Internal Student Management System

A comprehensive internal management system for AUSSIZ Education and Training to digitize student management operations.

## Overview
This system is designed specifically for AUSSIZ's operational workflow to replace paper records, Excel sheets, and manual processes with a centralized digital solution.

## Technology Stack

### Frontend
- Next.js 13+ with App Router
- React 18
- TypeScript
- Tailwind CSS
- shadcn/ui
- React Hook Form + Zod
- TanStack Query
- Recharts

### Backend
- Python 3.9+
- Django 4.2+
- Django REST Framework
- PostgreSQL
- SimpleJWT
- Celery + Redis

### Infrastructure
- Docker & Docker Compose
- GitHub

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Node.js 18+
- Python 3.9+

### Installation
1. Clone the repository
2. Copy `.env.example` to `.env` and configure environment variables
3. Run `docker-compose up --build`
4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/v1/
   - Admin Interface: http://localhost:8000/admin/

## Development Progress

### Phase 0: Foundation ✓ COMPLETED
- Repository structure initialized
- Backend Django project configured
- Frontend Next.js project configured
- Docker containers for development
- Environment configuration
- Core apps created:
  - accounts (authentication, roles, users)
  - students (student management, next of kin, documents)
  - courses (course categories, courses, classes)
  - attendance (sessions, statuses, records)
- Initial database migrations created
- Basic API endpoints for authentication

### Phase 1: Authentication & Staff
- Login/logout functionality
- JWT/session architecture
- Staff users management
- Roles and permissions
- Protected routes
- Backend authorization

### Phase 2: Student Management
- Student registration
- Student ID generation
- Student profile
- Next of kin
- Documents
- Student status
- Search
- Filters
- Student detail page

### Phase 3: Courses & Classes
- IELTS course
- Computer Packages
- Course configuration
- Classes
- Schedules
- Tutor assignment
- Student enrollment

### Phase 4: Attendance
- Attendance sessions
- Attendance recording
- Present/Absent/etc.
- Attendance history
- Attendance reports

### Phase 5: IELTS Academic Management
- Practice tests
- Mock tests
- Component scores
- Overall scores
- Target band
- Tutor feedback
- Student progress

### Phase 6: IELTS Exam Booking
- Booking request
- Required candidate information
- Staff review
- Booking status
- Booking/reference details
- Test date
- Test centre
- Booking history

### Phase 7: Official Results
- Official IELTS results
- Result document
- Result history
- Permissions
- Audit trail

### Phase 8: Finance
- Fees
- Charges
- Installments
- Payments
- Payment references
- Balances
- Payment history

### Phase 9: Receipts
- Receipt generation
- PDF
- Receipt numbering
- Receipt history
- Financial audit trail

### Phase 10: Reports
- Management
- Academic
- Attendance
- Finance
- IELTS performance
- Exports

### Phase 11: Notifications
- In-system notifications
- Email architecture
- Event-driven notification system

### Phase 12: Audit & Production Hardening
- Audit logs
- Security review
- Permission review
- Data validation
- Backup strategy
- Error monitoring
- Performance
- Deployment
- Production testing

### Phase 13: Website Integration
- Secure APIs for public website (post-MVP)

### Phase 14: Student Portal
- Future student-facing interface (post-MVP)

## Project Structure
```
aussiz-isms/
├── backend/                  # Django backend
│   ├── config/               # Django settings and WSGI/ASGI
│   ├── apps/                 # Domain-specific Django apps
│   │   ├── accounts/
│   │   ├── students/
│   │   ├── courses/
│   │   ├── classes/
│   │   ├── attendance/
│   │   └── ... (more apps to be implemented)
│   ├── requirements/         # Python requirements files
│   ├── migrations/           # Database migrations
│   ├── fixtures/             # Initial data fixtures
│   ├── scripts/              # Utility scripts
│   ├── tests/                # Backend tests
│   ├── Dockerfile            # Backend container
│   ├── manage.py             # Django management
│   └── README.md
├── frontend/                 # Next.js frontend
│   ├── app/                  # App router pages
│   ├── components/           # Reusable components
│   │   ├── ui/               # shadcn/ui components
│   │   ├── layout/           # Layout components
│   │   └── shared/           # Shared components
│   ├── features/             # Feature-specific code
│   │   ├── auth/
│   │   ├── dashboard/
│   │   ├── students/
│   │   ├── courses/
│   │   ├── classes/
│   │   ├── attendance/
│   │   └── ... (more features to be implemented)
│   ├── lib/                  # Utility functions
│   ├── hooks/                # Custom React hooks
│   ├── types/                # TypeScript types
│   ├── public/               # Static assets
│   ├── styles/               # Global styles
│   ├── scripts/              # Frontend scripts
│   ├── tests/                # Frontend tests
│   ├── next.config.js        # Next.js config
│   ├── tailwind.config.js    # Tailwind config
│   ├── postcss.config.js     # PostCSS config
│   ├── tsconfig.json         # TypeScript config
│   ├── Dockerfile            # Frontend container
│   └── README.md
├── docs/                     # Documentation
├── .github/                  # GitHub workflows
├── .dockerignore             # Docker ignore file
├── .gitignore                # Git ignore file
├── docker-compose.yml        # Multi-container setup
├── README.md                 # Project overview
├── .env.example              # Environment variables template
└── LICENSE                   # License file
```

## License
[To be determined]

## Contact
AUSSIZ Education and Training