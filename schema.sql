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

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  first_name varchar(25) NOT NULL,
  last_name varchar(25) NOT NULL,
  email varchar(75) NOT NULL UNIQUE,
  password varchar(30) NOT NULL,
  auth boolean DEFAULT false,
  department_id integer REFERENCES departments
);

CREATE TABLE IF NOT EXISTS rocs (
  id SERIAL PRIMARY KEY,
  amount_in_cents integer NOT NULL,
  roc MEDIUMBLOB NOT NULL,
  claimed_date DATE NOT NULL,
  user_id integer REFERENCES users
);

CREATE TABLE IF NOT EXISTS ach_credits (
  id SERIAL PRIMARY KEY,
  amount_in_cents integer,
  fund text,
  description text,
  received date,
  roc_id integer REFERENCES rocs,
  department_id integer REFERENCES departments
);

CREATE TABLE IF NOT EXISTS supporting_docs (
  id SERIAL PRIMARY KEY,
  filename text NOT NULL,
  doc MEDIUMBLOB NOT NULL,
  roc_id integer REFERENCES rocs
);
