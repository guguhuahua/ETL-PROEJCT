# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an ELT (Extract, Load, Transform) system with the following characteristics:
- **Frontend**: Vue.js + Element UI
- **Backend**: Flask + SQLite
- **Features**: User authentication, data source management (Hive, Kingbase8), ELT configuration with data migration and field type conversion, scheduling with dependencies and retries

## Project Structure

The project is organized as follows:
- `plan/` - Contains design documents and prototypes
  - `ELT系统设计说明书.md` - Complete system design documentation
  - `架构设计.md` - System architecture overview
  - `概要设计.md` - High-level functional design
  - `详细设计.md` - Detailed technical specifications
  - `前端原型.md` - HTML prototypes for UI components

## Key Components

### Backend (Flask)
- User authentication with JWT tokens
- Data source management supporting multiple database types
- ELT engine for data transformation
- Task scheduler with dependency management
- Database models for users, data sources, ELT tasks, schedules, and executions

### Frontend (Vue.js + Element UI)
- Authentication interface (login/register)
- Dashboard with statistics
- Data source management interface
- ELT task configuration wizard
- Scheduling configuration panel

## Development Guidelines

### Architecture
- Follow separation of concerns between frontend and backend
- Use RESTful API design principles
- Implement proper authentication and authorization
- Support pluggable database connectors

### Database Design
- Use SQLite for local storage in this implementation
- Store connection parameters securely
- Track task executions and status
- Maintain referential integrity between entities

### Security Considerations
- Encrypt sensitive connection parameters
- Validate and sanitize user inputs
- Implement proper session management
- Use parameterized queries to prevent SQL injection

## API Endpoints

### Authentication
- POST /api/auth/register: User registration
- POST /api/auth/login: User login
- POST /api/auth/logout: User logout
- GET /api/auth/profile: Get user information

### Data Sources
- GET /api/data-sources: Get all data sources
- POST /api/data-sources: Create new data source
- PUT /api/data-sources/{id}: Update data source
- DELETE /api/data-sources/{id}: Delete data source
- POST /api/data-sources/test-connection: Test connection

### ELT Tasks
- GET /api/elt-tasks: Get all ELT tasks
- POST /api/elt-tasks: Create new ELT task
- PUT /api/elt-tasks/{id}: Update ELT task
- DELETE /api/elt-tasks/{id}: Delete ELT task
- POST /api/elt-tasks/{id}/execute: Execute ELT task

### Schedules
- GET /api/schedules: Get all scheduled tasks
- POST /api/schedules: Create scheduled task
- PUT /api/schedules/{id}: Update scheduled task
- DELETE /api/schedules/{id}: Delete scheduled task

## Database Schema

### Core Tables
- users: Stores user accounts
- data_sources: Configured data sources with connection parameters
- elt_tasks: ELT task definitions
- schedules: Task scheduling configurations
- task_executions: Execution logs and status

## Common Development Tasks

### Setting up the Development Environment
1. Install Python dependencies for the backend
2. Set up Vue.js environment for the frontend
3. Initialize SQLite database
4. Configure application settings

### Adding New Database Connectors
1. Create a new connector class inheriting from the base connector
2. Implement connection and query methods
3. Add connector type to the data source configuration
4. Test connectivity and data transfer capabilities

### Extending ELT Capabilities
1. Add new transformation functions to the ELT engine
2. Update the frontend to expose new configuration options
3. Ensure proper validation and error handling
4. Update documentation accordingly