CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hash VARCHAR(255) NOT NULL,
);

CREATE TABLE projects (
    id SERIAL PRIMARY KEY, 
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    purpose VARCHAR(255) NOT NULL,
    description VARCHAR(255) NOT NULL,
    languages VARCHAR(255) NOT NULL,
    time VARCHAR(255) NOT NULL,
    note VARCHAR(255) NOT NULL,
    status VARCHAR(255) DEFAULT 'Pending',
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE proFunctions (
    function_id SERIAL PRIMARY_KEY, 
    project_id INT, 
    name VARCHAR(255) NOT NULL,
    status VARCHAR(255) DEFAULT 'Pending',
    FOREIGN KEY (project_id) REFERENCES projects(id) 
);

CREATE TABLE functions (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(255) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);