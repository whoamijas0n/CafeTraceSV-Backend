# CaféTrace SV  documentation
## Summary

- [Introduction](#introduction)
- [Database Type](#database-type)
- [Table Structure](#table-structure)
	- [organizaciones](#organizaciones)
	- [usuarios](#usuarios)
	- [productores](#productores)
	- [fincas](#fincas)
	- [parcelas](#parcelas)
	- [cosechas](#cosechas)
	- [lotes_cafe](#lotes_cafe)
- [Relationships](#relationships)
- [Database Diagram](#database-diagram)

## Introduction

## Database type

- **Database system:** PostgreSQL
## Table structure

### organizaciones

| Name                | Type         | Settings                                     | References | Note |
| ------------------- | ------------ | -------------------------------------------- | ---------- | ---- |
| **id_organizacion** | UUID         | 🔑 PK, not null, default: uuid_generate_v4() |            |      |
| **nombre**          | VARCHAR(150) | not null                                     |            |      |
| **activa**          | BOOLEAN      | not null, default: true                      |            |      |
| **creado_en**       | TIMESTAMP    | not null, default: NOW()                     |            |      | 


### usuarios

| Name                | Type        | Settings                                     | References                                 | Note |
| ------------------- | ----------- | -------------------------------------------- | ------------------------------------------ | ---- |
| **id_usuario**      | UUID        | 🔑 PK, not null, default: uuid_generate_v4() |                                            |      |
| **id_organizacion** | UUID        | not null                                     | fk_usuarios_id_organizacion_organizaciones |      |
| **correo**          | VARCHAR(50) | not null, unique                             |                                            |      |
| **password_hash**   | VARCHAR(80) | not null                                     |                                            |      |
| **nombres**         | VARCHAR(50) | not null                                     |                                            |      |
| **apellidos**       | VARCHAR(50) | not null                                     |                                            |      |
| **rol**             | VARCHAR(30) | not null, default: admin, productor, tecnico |                                            |      |
| **activo**          | BOOLEAN     | not null, default: true                      |                                            |      |
| **creado_en**       | TIMESTAMP   | not null, default: NOW()                     |                                            |      | 


#### Indexes
| Name                      | Unique | Fields          |
| ------------------------- | ------ | --------------- |
| idx_usuarios_organizacion |        | id_organizacion |
### productores

| Name                    | Type        | Settings                                     | References                         | Note |
| ----------------------- | ----------- | -------------------------------------------- | ---------------------------------- | ---- |
| **id_productor**        | UUID        | 🔑 PK, not null, default: uuid_generate_v4() |                                    |      |
| **id_usuario**          | UUID        | not null, unique                             | fk_productores_id_usuario_usuarios |      |
| **documento_identidad** | VARCHAR(50) | not null                                     |                                    |      |
| **telefono**            | VARCHAR(30) | not null                                     |                                    |      |
| **departamento**        | VARCHAR(50) | not null                                     |                                    |      |
| **municipio**           | VARCHAR(80) | not null                                     |                                    |      |
| **creado_en**           | TIMESTAMP   | not null, default: NOW()                     |                                    |      | 


### fincas

| Name               | Type         | Settings                                 | References                         | Note |
| ------------------ | ------------ | ---------------------------------------- | ---------------------------------- | ---- |
| **id_finca**       | UUID         | 🔑 PK, null, default: uuid_generate_v4() |                                    |      |
| **id_productor**   | UUID         | not null                                 | fk_fincas_id_productor_productores |      |
| **nombre**         | VARCHAR(120) | not null                                 |                                    |      |
| **departamento**   | VARCHAR(50)  | not null                                 |                                    |      |
| **municipio**      | VARCHAR(80)  | not null                                 |                                    |      |
| **canton_caserio** | VARCHAR(120) | null                                     |                                    |      |
| **altitud_msnm**   | INTEGER      | null                                     |                                    |      |
| **creado_en**      | TIMESTAMP    | not null, default: NOW()                 |                                    |      | 


### parcelas

| Name               | Type          | Settings                                     | References                  | Note |
| ------------------ | ------------- | -------------------------------------------- | --------------------------- | ---- |
| **id_parcela**     | UUID          | 🔑 PK, not null, default: uuid_generate_v4() |                             |      |
| **id_finca**       | UUID          | not null                                     | fk_parcelas_id_finca_fincas |      |
| **nombre**         | VARCHAR(100)  | not null                                     |                             |      |
| **variedad_cafe**  | VARCHAR(60)   | not null                                     |                             |      |
| **area_hectareas** | NUMERIC(10,4) | not null                                     |                             |      |
| **geometria**      | BLOB          | not null                                     |                             |      |
| **creado_en**      | TIMESTAMP     | not null, default: NOW()                     |                             |      | 


#### Indexes
| Name                   | Unique | Fields    |
| ---------------------- | ------ | --------- |
| idx_parcelas_geometria |        | geometria |
### cosechas

| Name                   | Type          | Settings                                     | References                      | Note |
| ---------------------- | ------------- | -------------------------------------------- | ------------------------------- | ---- |
| **id_cosecha**         | UUID          | 🔑 PK, not null, default: uuid_generate_v4() |                                 |      |
| **id_parcela**         | UUID          | not null                                     | fk_cosechas_id_parcela_parcelas |      |
| **fecha_cosecha**      | DATE          | not null                                     |                                 |      |
| **peso_kg**            | NUMERIC(10,2) | not null                                     |                                 |      |
| **porcentaje_humedad** | NUMERIC(5,2)  | null                                         |                                 |      |
| **notas**              | TEXT          | null                                         |                                 |      |
| **creado_en**          | TIMESTAMP     | not null, default: NOW()                     |                                 |      | 


### lotes_cafe

| Name                     | Type         | Settings                                      | References                        | Note |
| ------------------------ | ------------ | --------------------------------------------- | --------------------------------- | ---- |
| **id_lote**              | UUID         | 🔑 PK, not null, default: uuid_generate_v4()  |                                   |      |
| **id_cosecha**           | UUID         | not null                                      | fk_lotes_cafe_id_cosecha_cosechas |      |
| **codigo_lote**          | VARCHAR(60)  | not null, unique                              |                                   |      |
| **qr_uuid**              | UUID         | not null, unique, default: uuid_generate_v4() |                                   |      |
| **metodo_procesamiento** | VARCHAR(50)  | not null                                      |                                   |      |
| **puntaje_catacion**     | NUMERIC(5,2) | not null                                      |                                   |      |
| **listo_exportacion**    | BOOLEAN      | not null, default: false                      |                                   |      |
| **creado_en**            | TIMESTAMP    | not null, default: NOW()                      |                                   |      | 


## Relationships

- **usuarios to organizaciones**: many_to_one
- **productores to usuarios**: one_to_one
- **fincas to productores**: many_to_one
- **parcelas to fincas**: many_to_one
- **cosechas to parcelas**: many_to_one
- **lotes_cafe to cosechas**: many_to_one

## Database Diagram

```mermaid
erDiagram
	usuarios }o--|| organizaciones : references
	productores ||--|| usuarios : references
	fincas }o--|| productores : references
	parcelas }o--|| fincas : references
	cosechas }o--|| parcelas : references
	lotes_cafe }o--|| cosechas : references

	organizaciones {
		UUID id_organizacion
		VARCHAR(150) nombre
		BOOLEAN activa
		TIMESTAMP creado_en
	}

	usuarios {
		UUID id_usuario
		UUID id_organizacion
		VARCHAR(50) correo
		VARCHAR(80) password_hash
		VARCHAR(50) nombres
		VARCHAR(50) apellidos
		VARCHAR(30) rol
		BOOLEAN activo
		TIMESTAMP creado_en
	}

	productores {
		UUID id_productor
		UUID id_usuario
		VARCHAR(50) documento_identidad
		VARCHAR(30) telefono
		VARCHAR(50) departamento
		VARCHAR(80) municipio
		TIMESTAMP creado_en
	}

	fincas {
		UUID id_finca
		UUID id_productor
		VARCHAR(120) nombre
		VARCHAR(50) departamento
		VARCHAR(80) municipio
		VARCHAR(120) canton_caserio
		INTEGER altitud_msnm
		TIMESTAMP creado_en
	}

	parcelas {
		UUID id_parcela
		UUID id_finca
		VARCHAR(100) nombre
		VARCHAR(60) variedad_cafe
		NUMERIC(10,4) area_hectareas
		BLOB geometria
		TIMESTAMP creado_en
	}

	cosechas {
		UUID id_cosecha
		UUID id_parcela
		DATE fecha_cosecha
		NUMERIC(10,2) peso_kg
		NUMERIC(5,2) porcentaje_humedad
		TEXT notas
		TIMESTAMP creado_en
	}

	lotes_cafe {
		UUID id_lote
		UUID id_cosecha
		VARCHAR(60) codigo_lote
		UUID qr_uuid
		VARCHAR(50) metodo_procesamiento
		NUMERIC(5,2) puntaje_catacion
		BOOLEAN listo_exportacion
		TIMESTAMP creado_en
	}
```