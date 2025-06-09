CREATE TABLE coches (
    id INT AUTO_INCREMENT PRIMARY KEY,
    marca VARCHAR(50),
    modelo VARCHAR(50),
    anio INT,
    precio_financiado DECIMAL(10,2),
    estado VARCHAR(50),
    descripcion TEXT,
    fecha_agregado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    admin_id INT,
    motor INT,
    precio_contado DECIMAL(10,2),
    consumo DECIMAL(5,2),
    cambio VARCHAR(50),
    combustible VARCHAR(50),
    kilometros INT,
    puertas INT,
    plazas INT,
    tipo VARCHAR(15),
    FOREIGN KEY (admin_id) REFERENCES admin(id)
);

CREATE TABLE fotos(
    id INT AUTO_INCREMENT PRIMARY KEY,
    coche_id INT NOT NULL,
    ruta VARCHAR(255) NOT NULL,
    FOREIGN KEY (coche_id) REFERENCES coches(id) ON DELETE CASCADE
);

CREATE TABLE admin (  
    id INT AUTO_INCREMENT PRIMARY KEY,  
    nombre VARCHAR(100) NOT NULL,  
    email VARCHAR(100) NOT NULL UNIQUE,  
    contraseña VARCHAR(255) NOT NULL,  
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  
    es_super_admin BOOLEAN DEFAULT FALSE  
);  

CREATE TABLE mensajes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    motivo VARCHAR(100) NOT NULL,
    descripcion TEXT NOT NULL,
    fecha_envio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);