"""Schema families: DDL, seeded row generators, question templates with gold SQL.

A database instance is (family, data seed). Variants (permute=True) keep the schema and
the pools of entity names and category values, resample all row data, and permute which
id and which attributes belong to which name. So a query that hardcodes an id or a
looked-up value is right on the visible database and wrong on variants.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

Rows = dict[str, list[tuple]]

_FIRST = ["Ada", "Ben", "Cara", "Dev", "Elif", "Finn", "Gita", "Hugo", "Ines", "Jon", "Kira", "Leo", "Mina", "Noor", "Omar", "Pia", "Quin", "Rosa", "Sam", "Tara"]
_LAST = ["Abbott", "Banerjee", "Castro", "Dubois", "Eriksen", "Farouk", "Garcia", "Haas", "Ito", "Jensen", "Kowalski", "Lopez", "Mehta", "Novak", "Okafor", "Petrov", "Quigley", "Rossi", "Sato", "Tanaka"]
PEOPLE = [f"{f} {l}" for f in _FIRST for l in _LAST]  # 400 unique names
CITIES = ["Lisbon", "Pune", "Austin", "Osaka", "Leeds"]


@dataclass(frozen=True)
class Template:
    id: str
    tier: str  # easy | medium | hard
    question: str
    sql: str
    params: dict[str, tuple[str, str]] = field(default_factory=dict)  # name -> (table, column) in the visible db
    ordered: bool = False


@dataclass(frozen=True)
class Family:
    name: str
    ddl: tuple[str, ...]
    gen: Callable[[random.Random, bool], Rows]
    templates: tuple[Template, ...]


def _ids(rng: random.Random, n: int, permute: bool) -> list[int]:
    return rng.sample(range(1, 20 * n), n) if permute else list(range(1, n + 1))


def _names(rng: random.Random, pool: list[str], permute: bool) -> list[str]:
    out = list(pool)
    if permute:
        rng.shuffle(out)
    return out


# ---------------------------------------------------------------- retail
_PRODUCTS = [f"{a} {n}" for a in ["Basic", "Deluxe", "Compact", "Pro"] for n in ["Lamp", "Chair", "Desk", "Kettle", "Backpack"]]
_CATEGORIES = ["home", "office", "outdoor", "kitchen"]
_SEGMENTS = ["consumer", "business", "education"]
_STATUSES = ["pending", "shipped", "delivered", "cancelled"]


def _retail(rng: random.Random, permute: bool) -> Rows:
    cid = _ids(rng, 30, permute)
    pid = _ids(rng, 20, permute)
    oid = _ids(rng, 120, permute)
    return {
        "customers": [(i, n, rng.choice(CITIES), rng.choice(_SEGMENTS)) for i, n in zip(cid, _names(rng, PEOPLE[:30], permute))],
        "products": [(i, n, rng.choice(_CATEGORIES), rng.randrange(5, 200)) for i, n in zip(pid, _names(rng, _PRODUCTS, permute))],
        "orders": [(i, rng.choice(cid), f"2025-{rng.randrange(1, 13):02d}-{rng.randrange(1, 29):02d}", rng.choice(_STATUSES)) for i in oid],
        "order_items": [(i, rng.choice(oid), rng.choice(pid), rng.randrange(1, 6)) for i in _ids(rng, 300, permute)],
    }


RETAIL = Family(
    "retail",
    (
        "CREATE TABLE customers (customer_id INTEGER PRIMARY KEY, name TEXT, city TEXT, segment TEXT)",
        "CREATE TABLE products (product_id INTEGER PRIMARY KEY, name TEXT, category TEXT, price INTEGER)",
        "CREATE TABLE orders (order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(customer_id), order_date TEXT, status TEXT)",
        "CREATE TABLE order_items (item_id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(order_id), product_id INTEGER REFERENCES products(product_id), quantity INTEGER)",
    ),
    _retail,
    (
        Template("retail_e1", "easy", "How many orders have the status '{status}'?", "SELECT COUNT(*) FROM orders WHERE status = '{status}'", {"status": ("orders", "status")}),
        Template("retail_e2", "easy", "List the names of products in the '{category}' category that cost more than {price}.", "SELECT name FROM products WHERE category = '{category}' AND price > {price}", {"category": ("products", "category"), "price": ("products", "price")}),
        Template("retail_e3", "easy", "How many customers live in {city}?", "SELECT COUNT(*) FROM customers WHERE city = '{city}'", {"city": ("customers", "city")}),
        Template("retail_m1", "medium", "How many orders has the customer named '{customer}' placed?", "SELECT COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.name = '{customer}'", {"customer": ("customers", "name")}),
        Template("retail_m2", "medium", "What is the total quantity ordered of the product named '{product}'?", "SELECT COALESCE(SUM(oi.quantity), 0) FROM order_items oi JOIN products p ON oi.product_id = p.product_id WHERE p.name = '{product}'", {"product": ("products", "name")}),
        Template("retail_m3", "medium", "For each order status, how many orders were placed by customers in the '{segment}' segment? Return status and count.", "SELECT o.status, COUNT(*) FROM orders o JOIN customers c ON o.customer_id = c.customer_id WHERE c.segment = '{segment}' GROUP BY o.status", {"segment": ("customers", "segment")}),
        Template("retail_h1", "hard", "Which 3 customers spent the most (quantity times price) on orders with status '{status}'? Return customer name and total spent, highest first, ties broken by name.", "SELECT c.name, SUM(oi.quantity * p.price) AS total FROM customers c JOIN orders o ON o.customer_id = c.customer_id JOIN order_items oi ON oi.order_id = o.order_id JOIN products p ON p.product_id = oi.product_id WHERE o.status = '{status}' GROUP BY c.customer_id, c.name ORDER BY total DESC, c.name ASC LIMIT 3", {"status": ("orders", "status")}, ordered=True),
        Template("retail_h2", "hard", "For each product category, what is the total revenue (quantity times price) from customers who live in {city}? Return category and revenue.", "SELECT p.category, SUM(oi.quantity * p.price) FROM order_items oi JOIN products p ON p.product_id = oi.product_id JOIN orders o ON o.order_id = oi.order_id JOIN customers c ON c.customer_id = o.customer_id WHERE c.city = '{city}' GROUP BY p.category", {"city": ("customers", "city")}),
        Template("retail_h3", "hard", "List the names of customers in the '{segment}' segment who have no order with status '{status}'.", "SELECT c.name FROM customers c WHERE c.segment = '{segment}' AND NOT EXISTS (SELECT 1 FROM orders o WHERE o.customer_id = c.customer_id AND o.status = '{status}')", {"segment": ("customers", "segment"), "status": ("orders", "status")}),
    ),
)

# ---------------------------------------------------------------- hr
_DEPTS = ["Engineering", "Sales", "Finance", "Marketing", "Operations", "Legal"]
_LOCATIONS = ["Berlin", "Nairobi", "Toronto", "Hanoi"]
_TITLES = ["analyst", "engineer", "manager", "designer", "coordinator"]
_PROJECTS = [f"Project {x}" for x in ["Atlas", "Borealis", "Cobalt", "Delta", "Ember", "Fjord", "Garnet", "Harbor", "Iris", "Juniper", "Kestrel", "Lumen"]]


def _hr(rng: random.Random, permute: bool) -> Rows:
    did = _ids(rng, 6, permute)
    eid = _ids(rng, 40, permute)
    pid = _ids(rng, 12, permute)
    return {
        "departments": [(i, n, rng.choice(_LOCATIONS)) for i, n in zip(did, _names(rng, _DEPTS, permute))],
        "employees": [(i, n, rng.choice(did), rng.choice(_TITLES), rng.randrange(40, 160) * 1000, rng.randrange(2010, 2025)) for i, n in zip(eid, _names(rng, PEOPLE[40:80], permute))],
        "projects": [(i, n, rng.choice(did), rng.randrange(10, 100) * 1000) for i, n in zip(pid, _names(rng, _PROJECTS, permute))],
        "assignments": [(i, rng.choice(eid), rng.choice(pid), rng.randrange(5, 80)) for i in _ids(rng, 60, permute)],
    }


HR = Family(
    "hr",
    (
        "CREATE TABLE departments (dept_id INTEGER PRIMARY KEY, name TEXT, location TEXT)",
        "CREATE TABLE employees (emp_id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER REFERENCES departments(dept_id), title TEXT, salary INTEGER, hire_year INTEGER)",
        "CREATE TABLE projects (project_id INTEGER PRIMARY KEY, name TEXT, dept_id INTEGER REFERENCES departments(dept_id), budget INTEGER)",
        "CREATE TABLE assignments (assign_id INTEGER PRIMARY KEY, emp_id INTEGER REFERENCES employees(emp_id), project_id INTEGER REFERENCES projects(project_id), hours INTEGER)",
    ),
    _hr,
    (
        Template("hr_e1", "easy", "How many employees have the title '{title}'?", "SELECT COUNT(*) FROM employees WHERE title = '{title}'", {"title": ("employees", "title")}),
        Template("hr_e2", "easy", "List the names of employees hired after {hire_year} who earn more than {salary}.", "SELECT name FROM employees WHERE hire_year > {hire_year} AND salary > {salary}", {"hire_year": ("employees", "hire_year"), "salary": ("employees", "salary")}),
        Template("hr_e3", "easy", "What is the highest salary among employees with the title '{title}'?", "SELECT MAX(salary) FROM employees WHERE title = '{title}'", {"title": ("employees", "title")}),
        Template("hr_m1", "medium", "How many employees work in the department named '{dept}'?", "SELECT COUNT(*) FROM employees e JOIN departments d ON e.dept_id = d.dept_id WHERE d.name = '{dept}'", {"dept": ("departments", "name")}),
        Template("hr_m2", "medium", "What is the total number of hours assigned to the project named '{project}'?", "SELECT COALESCE(SUM(a.hours), 0) FROM assignments a JOIN projects p ON a.project_id = p.project_id WHERE p.name = '{project}'", {"project": ("projects", "name")}),
        Template("hr_m3", "medium", "For each department, how many employees were hired in or after {hire_year}? Return department name and count.", "SELECT d.name, COUNT(*) FROM employees e JOIN departments d ON e.dept_id = d.dept_id WHERE e.hire_year >= {hire_year} GROUP BY d.dept_id, d.name", {"hire_year": ("employees", "hire_year")}),
        Template("hr_h1", "hard", "Which 3 employees have the most hours assigned on projects owned by the department named '{dept}'? Return employee name and total hours, highest first, ties broken by name.", "SELECT e.name, SUM(a.hours) AS total FROM employees e JOIN assignments a ON a.emp_id = e.emp_id JOIN projects p ON p.project_id = a.project_id JOIN departments d ON d.dept_id = p.dept_id WHERE d.name = '{dept}' GROUP BY e.emp_id, e.name ORDER BY total DESC, e.name ASC LIMIT 3", {"dept": ("departments", "name")}, ordered=True),
        Template("hr_h2", "hard", "For each department, what is the total salary of employees who are assigned to at least one project with a budget above {budget}? Return department name and total salary.", "SELECT d.name, SUM(e.salary) FROM employees e JOIN departments d ON d.dept_id = e.dept_id WHERE EXISTS (SELECT 1 FROM assignments a JOIN projects p ON p.project_id = a.project_id WHERE a.emp_id = e.emp_id AND p.budget > {budget}) GROUP BY d.dept_id, d.name", {"budget": ("projects", "budget")}),
        Template("hr_h3", "hard", "List the names of employees in departments located in {location} who have no project assignments.", "SELECT e.name FROM employees e JOIN departments d ON d.dept_id = e.dept_id WHERE d.location = '{location}' AND NOT EXISTS (SELECT 1 FROM assignments a WHERE a.emp_id = e.emp_id)", {"location": ("departments", "location")}),
    ),
)

# ---------------------------------------------------------------- library
_TITLES_BOOK = [f"The {a} {n}" for a in ["Silent", "Quiet", "Last", "Crimson", "Winter", "Broken", "Golden", "Distant"] for n in ["River", "Garden", "Signal", "Orchard", "Harbor"]]
_GENRES = ["mystery", "science", "history", "fantasy", "poetry"]
_COUNTRIES = ["Chile", "Kenya", "Norway", "Japan", "Canada"]


def _library(rng: random.Random, permute: bool) -> Rows:
    aid = _ids(rng, 15, permute)
    mid = _ids(rng, 30, permute)
    bid = _ids(rng, 40, permute)
    return {
        "authors": [(i, n, rng.choice(_COUNTRIES)) for i, n in zip(aid, _names(rng, PEOPLE[100:115], permute))],
        "members": [(i, n, rng.choice(CITIES), rng.randrange(2015, 2025)) for i, n in zip(mid, _names(rng, PEOPLE[120:150], permute))],
        "books": [(i, n, rng.choice(aid), rng.choice(_GENRES), rng.randrange(1950, 2024)) for i, n in zip(bid, _names(rng, _TITLES_BOOK, permute))],
        "loans": [(i, rng.choice(bid), rng.choice(mid), rng.randrange(2021, 2026), rng.randrange(0, 2)) for i in _ids(rng, 70, permute)],
    }


LIBRARY = Family(
    "library",
    (
        "CREATE TABLE authors (author_id INTEGER PRIMARY KEY, name TEXT, country TEXT)",
        "CREATE TABLE members (member_id INTEGER PRIMARY KEY, name TEXT, city TEXT, join_year INTEGER)",
        "CREATE TABLE books (book_id INTEGER PRIMARY KEY, title TEXT, author_id INTEGER REFERENCES authors(author_id), genre TEXT, pub_year INTEGER)",
        "CREATE TABLE loans (loan_id INTEGER PRIMARY KEY, book_id INTEGER REFERENCES books(book_id), member_id INTEGER REFERENCES members(member_id), loan_year INTEGER, returned INTEGER)",
    ),
    _library,
    (
        Template("library_e1", "easy", "How many books are in the '{genre}' genre?", "SELECT COUNT(*) FROM books WHERE genre = '{genre}'", {"genre": ("books", "genre")}),
        Template("library_e2", "easy", "List the titles of '{genre}' books published before {pub_year}.", "SELECT title FROM books WHERE genre = '{genre}' AND pub_year < {pub_year}", {"genre": ("books", "genre"), "pub_year": ("books", "pub_year")}),
        Template("library_e3", "easy", "How many loans made in {loan_year} have not been returned (returned = 0)?", "SELECT COUNT(*) FROM loans WHERE loan_year = {loan_year} AND returned = 0", {"loan_year": ("loans", "loan_year")}),
        Template("library_m1", "medium", "How many books were written by the author named '{author}'?", "SELECT COUNT(*) FROM books b JOIN authors a ON b.author_id = a.author_id WHERE a.name = '{author}'", {"author": ("authors", "name")}),
        Template("library_m2", "medium", "How many loans has the member named '{member}' made?", "SELECT COUNT(*) FROM loans l JOIN members m ON l.member_id = m.member_id WHERE m.name = '{member}'", {"member": ("members", "name")}),
        Template("library_m3", "medium", "For each book genre, how many loans were made in {loan_year}? Return genre and count.", "SELECT b.genre, COUNT(*) FROM loans l JOIN books b ON l.book_id = b.book_id WHERE l.loan_year = {loan_year} GROUP BY b.genre", {"loan_year": ("loans", "loan_year")}),
        Template("library_h1", "hard", "Which 3 authors have the most loans of their books by members who live in {city}? Return author name and loan count, highest first, ties broken by name.", "SELECT a.name, COUNT(*) AS n FROM authors a JOIN books b ON b.author_id = a.author_id JOIN loans l ON l.book_id = b.book_id JOIN members m ON m.member_id = l.member_id WHERE m.city = '{city}' GROUP BY a.author_id, a.name ORDER BY n DESC, a.name ASC LIMIT 3", {"city": ("members", "city")}, ordered=True),
        Template("library_h2", "hard", "For each author country, how many distinct members have borrowed a '{genre}' book by an author from that country? Return country and member count.", "SELECT a.country, COUNT(DISTINCT l.member_id) FROM authors a JOIN books b ON b.author_id = a.author_id JOIN loans l ON l.book_id = b.book_id WHERE b.genre = '{genre}' GROUP BY a.country", {"genre": ("books", "genre")}),
        Template("library_h3", "hard", "List the titles of '{genre}' books that have never been loaned.", "SELECT b.title FROM books b WHERE b.genre = '{genre}' AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.book_id = b.book_id)", {"genre": ("books", "genre")}),
    ),
)

# ---------------------------------------------------------------- support
_TEAMS = ["billing", "technical", "onboarding"]
_PLANS = ["free", "team", "enterprise"]
_REGIONS = ["north", "south", "east", "west"]
_PRIORITIES = ["low", "medium", "high"]
_TSTATUS = ["open", "waiting", "closed"]


def _support(rng: random.Random, permute: bool) -> Rows:
    aid = _ids(rng, 12, permute)
    cid = _ids(rng, 30, permute)
    tid = _ids(rng, 120, permute)
    return {
        "agents": [(i, n, rng.choice(_TEAMS)) for i, n in zip(aid, _names(rng, PEOPLE[200:212], permute))],
        "clients": [(i, n, rng.choice(_PLANS), rng.choice(_REGIONS)) for i, n in zip(cid, _names(rng, PEOPLE[220:250], permute))],
        "tickets": [(i, rng.choice(cid), rng.choice(aid), rng.choice(_PRIORITIES), rng.choice(_TSTATUS), rng.randrange(1, 13)) for i in tid],
        "messages": [(i, rng.choice(tid), rng.choice(["client", "agent"]), rng.randrange(20, 500)) for i in _ids(rng, 300, permute)],
    }


SUPPORT = Family(
    "support",
    (
        "CREATE TABLE agents (agent_id INTEGER PRIMARY KEY, name TEXT, team TEXT)",
        "CREATE TABLE clients (client_id INTEGER PRIMARY KEY, name TEXT, plan TEXT, region TEXT)",
        "CREATE TABLE tickets (ticket_id INTEGER PRIMARY KEY, client_id INTEGER REFERENCES clients(client_id), agent_id INTEGER REFERENCES agents(agent_id), priority TEXT, status TEXT, opened_month INTEGER)",
        "CREATE TABLE messages (message_id INTEGER PRIMARY KEY, ticket_id INTEGER REFERENCES tickets(ticket_id), sender TEXT, length INTEGER)",
    ),
    _support,
    (
        Template("support_e1", "easy", "How many tickets have priority '{priority}' and status '{status}'?", "SELECT COUNT(*) FROM tickets WHERE priority = '{priority}' AND status = '{status}'", {"priority": ("tickets", "priority"), "status": ("tickets", "status")}),
        Template("support_e2", "easy", "List the names of clients on the '{plan}' plan in the {region} region.", "SELECT name FROM clients WHERE plan = '{plan}' AND region = '{region}'", {"plan": ("clients", "plan"), "region": ("clients", "region")}),
        Template("support_e3", "easy", "How many tickets were opened in month {opened_month}?", "SELECT COUNT(*) FROM tickets WHERE opened_month = {opened_month}", {"opened_month": ("tickets", "opened_month")}),
        Template("support_m1", "medium", "How many tickets are assigned to the agent named '{agent}'?", "SELECT COUNT(*) FROM tickets t JOIN agents a ON t.agent_id = a.agent_id WHERE a.name = '{agent}'", {"agent": ("agents", "name")}),
        Template("support_m2", "medium", "How many tickets has the client named '{client}' opened?", "SELECT COUNT(*) FROM tickets t JOIN clients c ON t.client_id = c.client_id WHERE c.name = '{client}'", {"client": ("clients", "name")}),
        Template("support_m3", "medium", "For each ticket priority, how many tickets come from clients on the '{plan}' plan? Return priority and count.", "SELECT t.priority, COUNT(*) FROM tickets t JOIN clients c ON t.client_id = c.client_id WHERE c.plan = '{plan}' GROUP BY t.priority", {"plan": ("clients", "plan")}),
        Template("support_h1", "hard", "Which 3 agents have the most messages on their tickets with status '{status}'? Return agent name and message count, highest first, ties broken by name.", "SELECT a.name, COUNT(*) AS n FROM agents a JOIN tickets t ON t.agent_id = a.agent_id JOIN messages m ON m.ticket_id = t.ticket_id WHERE t.status = '{status}' GROUP BY a.agent_id, a.name ORDER BY n DESC, a.name ASC LIMIT 3", {"status": ("tickets", "status")}, ordered=True),
        Template("support_h2", "hard", "For each agent team, what is the total message length on tickets from clients in the {region} region? Return team and total length.", "SELECT a.team, SUM(m.length) FROM messages m JOIN tickets t ON t.ticket_id = m.ticket_id JOIN agents a ON a.agent_id = t.agent_id JOIN clients c ON c.client_id = t.client_id WHERE c.region = '{region}' GROUP BY a.team", {"region": ("clients", "region")}),
        Template("support_h3", "hard", "List the names of clients on the '{plan}' plan who have no ticket with priority '{priority}'.", "SELECT c.name FROM clients c WHERE c.plan = '{plan}' AND NOT EXISTS (SELECT 1 FROM tickets t WHERE t.client_id = c.client_id AND t.priority = '{priority}')", {"plan": ("clients", "plan"), "priority": ("tickets", "priority")}),
    ),
)

FAMILIES: dict[str, Family] = {f.name: f for f in (RETAIL, HR, LIBRARY, SUPPORT)}
