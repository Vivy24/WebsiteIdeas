CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    hash TEXT NOT NULL,
    email TEXT NOT NULL
)

CREATE TABLE projects (
    id INTEGER PRIMARY KEY, 
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    purpose TEXT NOT NULL,
    description TEXT NOT NULL,
    languages TEXT NOT NULL,
    time TEXT NOT NULL,
    note TEXT NOT NULL,
    status TEXT DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
)

CREATE TABLE proFunctions (
    id INTEGER PRIMARY KEY, 
    project_id INT, 
    name TEXT NOT NULL,
    status TEXT DEFAULT "Pending",
    FOREIGN KEY (project_id) REFERENCES projects(id) 
)

CREATE TABLE functions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
)