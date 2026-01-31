# E-Commerce Backend API

A full-featured E-Commerce backend built using FastAPI and PostgreSQL.  
It supports authentication, product management, cart, orders, inventory handling, admin workflows.


## Features

- JWT-based authentication
- Role-based access (customer, admin)
- Product and category management
- Inventory tracking
- Cart functionality
- Order placement and cancellation
- Admin order management


## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication


## How to Run Locally

```bash
git clone https://github.com/roshanmishra17/E-commerce-Backend.git
cd E-commerce-Backend

python -m venv venv
.\venv\Scripts\activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

## Environment Variables

Create a `.env` file in the project root with the following values:

```env
DATABASE_URL=postgresql://user:password@host:port/db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_TIME=60
```

## API Documentation

Swagger UI is available at:

http://localhost:8000/docs

## Roles
- Customer: browse products, manage cart, place orders
- Admin: manage products, categories, and orders

## Author
Roshan Mishra  
BSc Computer Science Student  
Frontend & Backend Developer
GitHub: https://github.com/roshanmishra17
