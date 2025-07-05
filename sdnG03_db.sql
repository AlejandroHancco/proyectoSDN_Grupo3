DROP DATABASE IF EXISTS sdnG03_db;
CREATE DATABASE IF NOT EXISTS sdnG03_db;
USE sdnG03_db;

-- Tabla de roles
CREATE TABLE role (
    idrole INT PRIMARY KEY AUTO_INCREMENT,
    rolname VARCHAR(50) NOT NULL
);

-- Tabla de usuarios
CREATE TABLE user (
    iduser INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    names VARCHAR(100) NOT NULL,
    lastnames VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    rol INT,
    session VARCHAR(10),
    time_stamp DATETIME,
    ip VARCHAR(15),
    sw_id VARCHAR(50),
    sw_port INT,
    mac VARCHAR(17),
    numrules INT,
    FOREIGN KEY (rol) REFERENCES role(idrole)
);

-- Tabla de reglas
CREATE TABLE rule (
    idrule INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    svr_ip VARCHAR(15),
    svr_port INT,
    svr_mac VARCHAR(17),
    action VARCHAR(20)
);

-- Tabla de relación rol-regla
CREATE TABLE role_has_rule (
    role_idrole INT,
    rule_idrule INT,
    PRIMARY KEY (role_idrole, rule_idrule),
    FOREIGN KEY (role_idrole) REFERENCES role(idrole),
    FOREIGN KEY (rule_idrule) REFERENCES rule(idrule)
);

-- Tabla cursos con estado y código, y nuevo campo 'puerto'
CREATE TABLE curso (
    idcurso INT PRIMARY KEY AUTO_INCREMENT,
    codigo VARCHAR(20) UNIQUE NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    estado ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo',
    puerto INT NOT NULL
);

-- Tabla inscripcion (dejamos sin datos insertados)
CREATE TABLE inscripcion (
    user_iduser INT,
    curso_idcurso INT,
    rol_id INT,
    fecha_inscripcion DATETIME DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_iduser, curso_idcurso, rol_id),
    FOREIGN KEY (user_iduser) REFERENCES user(iduser),
    FOREIGN KEY (curso_idcurso) REFERENCES curso(idcurso),
    FOREIGN KEY (rol_id) REFERENCES role(idrole)
);

-- Insertar roles
INSERT INTO role (rolname) VALUES 
('Administrador'),
('Alumno'),
('Profesor'),
('Invitado');

-- Insertar usuarios con roles
INSERT INTO user (username, password, names, lastnames, code, rol, session, time_stamp, ip, sw_id, sw_port, mac, numrules) VALUES
('admin1', 'admin123', 'Admin', 'User', 'ADMIN001', 1, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0),
('profesor1', 'profesor1', 'Profesor', 'Apellido1', 'P001', 3, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0),
('invitado1', 'invitado1', 'Profesor', 'Apellido1', 'P001', 4, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0),
('alumno1', 'passalumno', 'Alumno', 'Ejemplo', 'A001', 2, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0);

-- Insertar reglas
INSERT INTO rule (name, description, svr_ip, svr_port, svr_mac, action) VALUES
('Regla Admin', 'Acceso completo para admin', '10.0.0.3', 9000, 'fa:16:3e:a7:e1:fb', 'allow'),
('Regla Admin', 'Acceso completo para admin', '10.0.0.3', 9001, 'fa:16:3e:a7:e1:fb', 'allow'),
('Regla Admin', 'Acceso completo para admin', '10.0.0.3', 9002, 'fa:16:3e:a7:e1:fb', 'allow'),
('Regla Admin', 'Acceso completo para admin', '10.0.0.3', 9003, 'fa:16:3e:a7:e1:fb', 'allow'),
('Regla Admin', 'Acceso completo para admin', '10.0.0.3', 9004, 'fa:16:3e:a7:e1:fb', 'allow');

-- Asociar reglas con roles
INSERT INTO role_has_rule (role_idrole, rule_idrule) VALUES
(1, 1),
(2, 2),
(3, 3),
(4, 4);

-- Insertar cursos con PUERTO y sin inscripciones
INSERT INTO curso (codigo, nombre, estado, puerto) VALUES
('TEL120', 'Curso Python Básico', 'activo', 9000),
('TEL121', 'Curso Redes', 'activo', 9001),
('TEL122', 'Curso Seguridad', 'inactivo', 9002),
('TEL123', 'Curso SDN', 'activo', 9003),
('TEL124', 'Curso Cisco', 'activo', 9004);
