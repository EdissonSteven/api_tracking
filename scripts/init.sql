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
    guide_id UUID DEFAULT uuid_generate_v4(),
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
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checkpoints_tracking_status ON checkpoints(tracking_id, status);

CREATE INDEX IF NOT EXISTS idx_units_tracking_id ON units (tracking_id);
CREATE INDEX IF NOT EXISTS idx_units_status ON units (status);
CREATE INDEX IF NOT EXISTS idx_units_created_at ON units (created_at DESC);
CREATE INDEX IF NOT EXISTS idx_units_origin_destination ON units(origin, destination);

CREATE INDEX IF NOT EXISTS idx_users_username ON users (username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users (is_active);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON users (created_at DESC);

CREATE INDEX IF NOT EXISTS idx_checkpoints_active 
ON checkpoints(tracking_id, timestamp DESC)
WHERE status NOT IN ('delivered', 'cancelled');

-- Insertar datos de prueba
INSERT INTO units (tracking_id, origin, destination, status, weight_kg, customer_info) 
VALUES 
    ('TRK001', 'Bogotá', 'Medellín', 'in_transit', 2.5, '{"name": "Juan Pérez", "phone": "+57300123456"}'),
    ('TRK002', 'Cali', 'Cartagena', 'created', 1.2, '{"name": "María García", "phone": "+57301987654"}'),
    ('TRK003', 'Medellín', 'Barranquilla', 'delivered', 3.8, '{"name": "Carlos Rodríguez", "phone": "+57302456789"}'),
    ('TRK004', 'Bogotá', 'Cali', 'out_for_delivery', 5.2, '{"name": "Ana López", "phone": "+57303567890"}'),
    ('TRK005', 'Cartagena', 'Bogotá', 'at_facility', 1.5, '{"name": "Luis Martínez", "phone": "+57304678901"}'),
    ('TRK006', 'Barranquilla', 'Medellín', 'in_transit', 4.1, '{"name": "Diana Sánchez", "phone": "+57305789012"}'),
    ('TRK007', 'Cali', 'Pereira', 'picked_up', 2.3, '{"name": "Roberto Gómez", "phone": "+57306890123"}'),
    ('TRK008', 'Bogotá', 'Bucaramanga', 'exception', 6.7, '{"name": "Patricia Hernández", "phone": "+57307901234"}'),
    ('TRK009', 'Medellín', 'Cali', 'created', 0.8, '{"name": "Jorge Ramírez", "phone": "+57308012345"}'),
    ('TRK010', 'Pereira', 'Bogotá', 'in_transit', 3.5, '{"name": "Sandra Castro", "phone": "+57309123456"}'),
    ('TRK011', 'Bucaramanga', 'Cartagena', 'at_facility', 2.9, '{"name": "Miguel Vargas", "phone": "+57310234567"}'),
    ('TRK012', 'Cali', 'Bogotá', 'out_for_delivery', 4.6, '{"name": "Laura Morales", "phone": "+57311345678"}')
ON CONFLICT (tracking_id) DO NOTHING;

-- TRK001: En tránsito (2 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK001', 'picked_up', 'Centro de Distribución Bogotá', 'Paquete recogido y procesado', NOW() - INTERVAL '2 hours'),
    ('TRK001', 'in_transit', 'Terminal de Transporte Bogotá', 'En ruta hacia Medellín', NOW() - INTERVAL '1 hour')
ON CONFLICT (id) DO NOTHING;

-- TRK002: Recién creado (1 checkpoint)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK002', 'created', 'Centro de Distribución Cali', 'Paquete registrado en el sistema', NOW() - INTERVAL '30 minutes')
ON CONFLICT (id) DO NOTHING;

-- TRK003: Entregado (3 checkpoints - ciclo completo)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK003', 'picked_up', 'Centro de Distribución Medellín', 'Recolección exitosa', NOW() - INTERVAL '8 hours'),
    ('TRK003', 'in_transit', 'Punto Intermedio Caucasia', 'En ruta hacia destino', NOW() - INTERVAL '5 hours'),
    ('TRK003', 'delivered', 'Barranquilla - Dirección del cliente', 'Entregado y firmado por el cliente', NOW() - INTERVAL '1 hour')
ON CONFLICT (id) DO NOTHING;

-- TRK004: Listo para entrega (3 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK004', 'picked_up', 'Bodega Principal Bogotá', 'Paquete ingresado al sistema', NOW() - INTERVAL '6 hours'),
    ('TRK004', 'at_facility', 'Centro de Distribución Cali', 'Llegó a ciudad destino', NOW() - INTERVAL '3 hours'),
    ('TRK004', 'out_for_delivery', 'Vehículo de Reparto Zona Sur', 'En ruta de entrega final', NOW() - INTERVAL '45 minutes')
ON CONFLICT (id) DO NOTHING;

-- TRK005: En bodega (2 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK005', 'picked_up', 'Punto de Recolección Cartagena', 'Recogido de remitente', NOW() - INTERVAL '12 hours'),
    ('TRK005', 'at_facility', 'Hub Central Bogotá', 'En proceso de clasificación', NOW() - INTERVAL '4 hours')
ON CONFLICT (id) DO NOTHING;

-- TRK006: En tránsito (2 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK006', 'picked_up', 'Terminal Barranquilla', 'Iniciando transporte', NOW() - INTERVAL '7 hours'),
    ('TRK006', 'in_transit', 'Peaje Planeta Rica', 'Avance en ruta', NOW() - INTERVAL '3 hours 30 minutes')
ON CONFLICT (id) DO NOTHING;

-- TRK007: Recién recogido (1 checkpoint)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK007', 'picked_up', 'Oficina Principal Cali', 'Paquete recogido del remitente', NOW() - INTERVAL '2 hours')
ON CONFLICT (id) DO NOTHING;

-- TRK008: Excepción/Problema (3 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK008', 'picked_up', 'Centro de Acopio Bogotá Norte', 'Recolectado correctamente', NOW() - INTERVAL '10 hours'),
    ('TRK008', 'in_transit', 'Ruta Nacional Tunja', 'En camino a Bucaramanga', NOW() - INTERVAL '6 hours'),
    ('TRK008', 'exception', 'Centro de Distribución Bucaramanga', 'Dirección incorrecta - requiere validación', NOW() - INTERVAL '2 hours')
ON CONFLICT (id) DO NOTHING;

-- TRK009: Solo creado (1 checkpoint)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK009', 'created', 'Sistema Central Medellín', 'Guía generada - esperando recolección', NOW() - INTERVAL '15 minutes')
ON CONFLICT (id) DO NOTHING;

-- TRK010: En tránsito (2 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK010', 'picked_up', 'Sucursal Pereira Centro', 'Paquete ingresado', NOW() - INTERVAL '5 hours'),
    ('TRK010', 'in_transit', 'Terminal La Pola', 'Dirección a Bogotá', NOW() - INTERVAL '2 hours 15 minutes')
ON CONFLICT (id) DO NOTHING;

-- TRK011: En bodega de destino (3 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK011', 'picked_up', 'Punto de Origen Bucaramanga', 'Recolección completada', NOW() - INTERVAL '20 hours'),
    ('TRK011', 'in_transit', 'Corredor Vial Santa Marta', 'Tránsito hacia costa', NOW() - INTERVAL '14 hours'),
    ('TRK011', 'at_facility', 'Bodega Central Cartagena', 'Disponible para despacho', NOW() - INTERVAL '3 hours')
ON CONFLICT (id) DO NOTHING;

-- TRK012: Listo para entrega (3 checkpoints)
INSERT INTO checkpoints (tracking_id, status, location, description, timestamp) 
VALUES 
    ('TRK012', 'picked_up', 'Hub Cali Sur', 'Ingreso al sistema logístico', NOW() - INTERVAL '9 hours'),
    ('TRK012', 'at_facility', 'Centro de Distribución Bogotá', 'Arribó a ciudad destino', NOW() - INTERVAL '4 hours 30 minutes'),
    ('TRK012', 'out_for_delivery', 'Ruta de Entrega Norte', 'En vehículo hacia dirección final', NOW() - INTERVAL '1 hour 15 minutes')
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