CREATE DATABASE sdnG03_db;
USE sdnG03_db;

-- Tabla de roles
CREATE TABLE role (
    idrole INT PRIMARY KEY AUTO_INCREMENT,
    rolname VARCHAR(50) NOT NULL
);

-- Tabla de usuarios
CREATE TABLE user (
    username VARCHAR(50) PRIMARY KEY,
    password VARCHAR(255) NOT NULL,
    names VARCHAR(100) NOT NULL,
    lastnames VARCHAR(100) NOT NULL,
    code VARCHAR(20),
    rol INT,
    session VARCHAR(10),
    time_stamp DATETIME,  -- cambiado de VARCHAR(50) a DATETIME
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

-- Insertar roles
INSERT INTO role (rolname) VALUES 
('admin'),
('user'),
('invitado');

-- Insertar usuarios con roles correspondientes (sin cambiar datos originales)
INSERT INTO user (username, password, names, lastnames, code, rol, session, time_stamp, ip, sw_id, sw_port, mac, numrules) VALUES
('admin1', 'admin123', 'Admin', 'User', 'ADMIN001', 1, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0),
('user1', 'password1', 'Nombre1', 'Apellido1', 'C001', 2, 'active', NOW(), '10.0.0.1', '00:00:f2:20:f9:45:4c:4e', 3, 'fa:16:3e:0a:37:49', 0),
('user2', 'password2', 'Nombre2', 'Apellido2', 'C002', 2, 'active', NOW(), '10.0.0.2', '00:00:aa:51:aa:ba:72:41', 5, 'fa:16:3e:69:ff:aa', 0),
('user3', 'password3', 'Nombre3', 'Apellido3', 'C003', 2, 'active', NOW(), '10.0.0.3', '00:00:1a:74:72:3f:ef:44', 3, 'fa:16:3e:a7:e1:fb', 0),
('guest1', 'guestpass', 'Invitado', 'Ejemplo', 'G001', 3, 'active', NOW(), '10.0.0.4', '00:00:11:22:33:44:55:66', 2, 'de:ad:be:ef:00:01', 0);

-- Insertar reglas
INSERT INTO rule (name, description, svr_ip, svr_port, svr_mac, action) VALUES
('Regla Admin', 'Acceso completo para admin', '192.168.201.200', 8080, 'aa:bb:cc:dd:ee:ff', 'allow'),
('Regla User', 'Acceso limitado para usuario', '192.168.201.201', 8081, 'fa:16:3e:0a:37:49', 'allow'),
('Regla Invitado', 'Acceso restringido para invitado', '192.168.201.202', 8082, 'de:ad:be:ef:00:01', 'deny');

-- Asociar reglas con roles
INSERT INTO role_has_rule (role_idrole, rule_idrule) VALUES
(1, 1), -- admin tiene la Regla Admin
(2, 2), -- user tiene la Regla User
(3, 3); -- invitado tiene la Regla Invitado
