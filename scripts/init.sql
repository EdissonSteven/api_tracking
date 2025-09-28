-- Inicialización de base de datos PostgreSQL para Tracking API
-- Script corregido: primero crear tablas, luego índices

-- Crear extensión para funciones criptográficas y UUID
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Tabla de usuarios (sin credenciales hardcoded)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    is_superuser BOOLEAN DEFAULT FALSE,
    roles JSONB DEFAULT '["user"]'::jsonb,
    extra_data JSONB DEFAULT '["read"]'::jsonb,
    permissions JSONB DEFAULT '["read"]'::jsonb,
    last_login TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);


-- Crear tabla checkpoints
CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_id VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    location TEXT,
    description TEXT,
    operator VARCHAR(100),
    coordinates JSONB,
    meta_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear tabla units
CREATE TABLE IF NOT EXISTS units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tracking_id VARCHAR(50) UNIQUE NOT NULL,
    origin VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    status VARCHAR(20) DEFAULT 'created',
    weight_kg DECIMAL(10,2),
    dimensions JSONB,
    customer_info JSONB,
    extra_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices después de crear las tablas
CREATE INDEX IF NOT EXISTS idx_checkpoints_tracking_id ON checkpoints (tracking_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_status ON checkpoints (status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_timestamp ON checkpoints (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_checkpoints_tracking_status_time ON checkpoints (tracking_id, status, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_units_tracking_id ON units (tracking_id);
CREATE INDEX IF NOT EXISTS idx_units_status ON units (status);
CREATE INDEX IF NOT EXISTS idx_units_created_at ON units (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at DESC);

-- Insertar datos de prueba
INSERT INTO units (tracking_id, origin, destination, status, weight_kg, customer_info) 
VALUES 
    ('TRK001', 'Bogotá', 'Medellín', 'in_transit', 2.5, '{"name": "Juan Pérez", "phone": "+57300123456"}'),
    ('TRK002', 'Cali', 'Cartagena', 'created', 1.2, '{"name": "María García", "phone": "+57301987654"}')
ON CONFLICT (tracking_id) DO NOTHING;

INSERT INTO checkpoints (tracking_id, status, location, description) 
VALUES 
    ('TRK001', 'picked_up', 'Centro de Distribución Bogotá', 'Paquete recogido y procesado'),
    ('TRK001', 'in_transit', 'Terminal de Transporte', 'En ruta hacia Medellín'),
    ('TRK002', 'created', 'Centro de Distribución Cali', 'Paquete registrado en el sistema')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (username, email, hashed_password, full_name, is_active, is_superuser, roles, permissions) 
VALUES 
    (
        'admin',
        'admin@empresa.com',
        '$2y$10$RfisUnEmyvdeY34PPFBnPuKoanNOPujbO3.FoNfToZ6M99mEdWUIm',  -- admin123
        'Administrador del Sistema',
        TRUE,
        TRUE,
        '["admin", "superuser"]'::jsonb,
        '["read", "write", "delete", "admin","checkpoint:create"]'::jsonb
    ),
    (
        'operator',
        'operator@empresa.com',
        '$2y$10$Dvv.7Ba9oT3PD8Qr6a5SR.uL948ds33jPiDdvhrpgQGbZI5N4Q6Y.',  -- operator123
        'Operador de Tracking',
        TRUE,
        FALSE,
        '["operator"]'::jsonb,
        '["read", "write","checkpoint:create"]'::jsonb
    ),
    (
        'viewer',
        'viewer@empresa.com',
        '$2y$10$134AaukkEXe7fy3Z00NuCedH.cVzs771zxM5sVy9zl3YtZNZ/DuHK',  -- viewer123
        'Usuario Visualizador',
        TRUE,
        FALSE,
        '["viewer"]'::jsonb,
        '["read"]'::jsonb
    );