# RAISE Ethics Toolkit

A prototype tool to help faculty navigate AI ethics in research and teaching.

## What this is

I built this after reading about the RAISE project at USF. The problem stuck with me — faculty are using AI tools like ChatGPT in their work, but most don't have clear guidance on when it's okay, when they need IRB amendments, or how to stay FERPA compliant.

The stats are kind of wild:
- 61% of faculty use AI in teaching (EDUCAUSE 2024)
- 68% have no formal AI ethics training
- 61% of institutions don't have AI policies yet

So instead of another PDF guide that nobody reads, I wanted to build something interactive that actually tells you what to do based on your specific situation.

## What it does

**Role-Based Access**
When you start, you pick your role (student, faculty, administrator). The interface adapts based on what's relevant to you.

**Project Dashboard**
Track your AI-related projects and their compliance status. See at a glance which ones need attention.

**Document Generator**
Generates actual templates you can use — IRB amendments, FERPA checklists, disclosure statements. Fill in your details and download.

**Knowledge Assessment**
Quick quiz to check your understanding of AI ethics. Scenario-based questions, not just self-report stuff.

## Tech stack

- Backend: Django + Django REST Framework
- Frontend: React + Vite
- Database: SQLite

## Running locally

Backend:
```bash
cd backend_django
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8000
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173

## Notes

This is a prototype — built to explore what a practical ethics toolkit could look like. The decision tree logic and templates are based on HIPAA Safe Harbor, FERPA requirements, and COPE guidelines.

The stats shown are from published research (EDUCAUSE, Digital Education Council).

## License

All rights reserved. See the LICENSE file. This code is published for
demonstration only and is not licensed for reuse.

