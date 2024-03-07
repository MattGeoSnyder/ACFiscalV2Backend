DROP TABLE IF EXISTS departments;

CREATE TABLE departments(
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL
);

INSERT INTO departments 
  (name)
VALUES
  ('Fiscal'),
  ('Cage'),
  ('Budget and Finance'),
  ('Real Estate'),
  ('Police'),
  ('DHS'),
  ('Human Resources'),
  ('Health'),
  ('Economic Development'),
  ('Courts'),
  ('Parks'),
  ('Emergency Services'),
  ('Medical Examiner''s'),
  ('Jail'),
  ('Tax'),
  ('Kane'),
  ('Special Tax'),
  ('District Attorney''s Office' ), 
  ('Sheriff''s');

DROP TABLE IF EXISTS users;

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  first_name varchar(25) NOT NULL,
  last_name varchar(25) NOT NULL,
  email varchar(75) NOT NULL UNIQUE,
  password text NOT NULL,
  department_id integer REFERENCES departments,
  permitted boolean DEFAULT false,
  role varchar(25) DEFAULT 'user'
);

DROP TABLE IF EXISTS rocs;

CREATE TABLE IF NOT EXISTS rocs (
  id SERIAL PRIMARY KEY,
  filename text, 
  roc MEDIUMBLOB NOT NULL,
  amount_in_cents integer NOT NULL,
  user_id integer DEFAULT NULL REFERENCES users
);

DROP TABLE IF EXISTS ach_credits;

CREATE TABLE IF NOT EXISTS ach_credits (
  id SERIAL PRIMARY KEY,
  amount_in_cents integer,
  fund int,
  description text,
  received date,
  claimed date DEFAULT NULL,
  roc_id integer DEFAULT NULL REFERENCES rocs, 
  department_id integer DEFAULT NULL REFERENCES departments 
);

DROP TABLE IF EXISTS supporting_docs;

CREATE TABLE IF NOT EXISTS supporting_docs (
  id SERIAL PRIMARY KEY,
  filename text NOT NULL,
  doc MEDIUMBLOB NOT NULL,
  roc_id integer REFERENCES rocs
);

DROP TABLE IF EXISTS credit_descriptions;

CREATE TABLE IF NOT EXISTS credit_descriptions (
  id SERIAL PRIMARY KEY,
  keywords_array JSON NOT NULL, 
  fund int NOT NULL,
  department_id int REFERENCES departments
);

DROP TABLE IF EXISTS roc_descriptions;

CREATE TABLE IF NOT EXISTS roc_descriptions (
  id SERIAL PRIMARY KEY,
  roc_id REFERENCES rocs,
  mcu TEXT NOT NULL,
  cost_center TEXT NOT NULL,
  object_number TEXT NOT NULL,
  subsidiary TEXT,
  subledger TEXT,
  explanation TEXT NOT NULL
) 

