# PepperAI Docker Setup

This document provides comprehensive instructions for running PepperAI in a fully dockerized environment.

## 🐳 Docker Architecture

The PepperAI system is containerized with the following services:

- **pepperai**: Main Flask application
- **nginx**: Reverse proxy and static file server
- **redis**: Caching and session storage
- **backup**: Automated database backup service

## 🚀 Quick Start

### Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v3.8+
- At least 4GB RAM available for Docker
- At least 2GB free disk space

### Windows Users

1. **Start PepperAI**:
   ```cmd
   docker-start.bat
   ```

2. **Stop PepperAI**:
   ```cmd
   docker-stop.bat
   ```

3. **View Logs**:
   ```cmd
   docker-logs.bat
   ```

4. **Reset Everything**:
   ```cmd
   docker-reset.bat
   ```

### Linux/macOS Users

1. **Start PepperAI**:
   ```bash
   ./docker-start.sh
   ```

2. **Stop PepperAI**:
   ```bash
   docker-compose down
   ```

3. **View Logs**:
   ```bash
   docker-compose logs -f
   ```

## 🔧 Manual Docker Commands

### Build and Start

```bash
# Build and start all services
docker-compose up --build -d

# Start in foreground (for debugging)
docker-compose up --build

# Start specific service
docker-compose up pepperai
```

### Stop and Cleanup

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove unused images
docker image prune -f
```

### Monitoring

```bash
# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f pepperai

# Check service status
docker-compose ps

# View resource usage
docker stats
```

## 🌐 Access Points

- **Web Interface**: http://localhost
- **Health Check**: http://localhost/health
- **Direct App**: http://localhost:5000 (bypasses nginx)

## 📁 Data Persistence

The following data is persisted using Docker volumes:

- `pepperai_uploads`: User uploaded images
- `pepperai_results`: Analysis results and generated images
- `pepperai_instance`: SQLite database
- `pepperai_redis`: Redis cache data

### Backup and Restore

```bash
# Manual backup
docker-compose exec pepperai cp /app/instance/pepperai.db /app/backups/manual_backup.db

# Restore from backup
docker-compose exec pepperai cp /app/backups/manual_backup.db /app/instance/pepperai.db
```

## ⚙️ Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

Key variables to configure:

- `SECRET_KEY`: Flask secret key (change in production)
- `DATABASE_URL`: Database connection string
- `REDIS_URL`: Redis connection string
- `MAX_CONTENT_LENGTH`: Maximum file upload size

### Nginx Configuration

Nginx configuration files are in the `nginx/` directory:

- `nginx/nginx.conf`: Main nginx configuration
- `nginx/conf.d/pepperai.conf`: PepperAI-specific configuration

## 🔍 Troubleshooting

### Common Issues

1. **Port 80 already in use**:
   ```bash
   # Check what's using port 80
   netstat -tulpn | grep :80
   
   # Stop the conflicting service or change nginx port in docker-compose.yml
   ```

2. **Out of memory**:
   ```bash
   # Increase Docker memory limit in Docker Desktop settings
   # Or reduce worker processes in nginx.conf
   ```

3. **Database connection issues**:
   ```bash
   # Check if database volume is mounted correctly
   docker-compose exec pepperai ls -la /app/instance/
   ```

4. **Model loading failures**:
   ```bash
   # Check if model files exist
   docker-compose exec pepperai ls -la /app/models/
   ```

### Debug Mode

Run in debug mode to see detailed logs:

```bash
# Set debug mode in .env
echo "DEBUG=True" >> .env

# Restart services
docker-compose restart pepperai
```

### Health Checks

Check service health:

```bash
# Overall health
curl http://localhost/health

# Individual service health
docker-compose exec pepperai curl http://localhost:5000/health
docker-compose exec redis redis-cli ping
```

## 🚀 Production Deployment

### Security Considerations

1. **Change default secret key**:
   ```bash
   # Generate a secure secret key
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

2. **Enable HTTPS**:
   - Add SSL certificates to nginx configuration
   - Update docker-compose.yml to mount certificate files

3. **Firewall configuration**:
   - Only expose port 80/443
   - Block direct access to port 5000

### Performance Optimization

1. **Resource limits**:
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

2. **Nginx optimization**:
   - Adjust worker processes in nginx.conf
   - Enable gzip compression
   - Configure caching headers

### Monitoring

1. **Log aggregation**:
   ```bash
   # Send logs to external system
   docker-compose logs | tee pepperai.log
   ```

2. **Health monitoring**:
   - Set up external health checks
   - Monitor Docker container status
   - Track resource usage

## 📊 Service Architecture

```
Internet → Nginx (Port 80/443) → PepperAI App (Port 5000)
                                    ↓
                               Redis (Port 6379)
                                    ↓
                               SQLite Database
```

## 🔄 Updates and Maintenance

### Updating PepperAI

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose up --build -d

# Verify health
curl http://localhost/health
```

### Database Maintenance

```bash
# Backup before updates
docker-compose exec pepperai cp /app/instance/pepperai.db /app/backups/pre_update.db

# Run database migrations (if any)
docker-compose exec pepperai python -c "from app import db; db.create_all()"
```

## 📝 Logs and Debugging

### Log Locations

- **Application logs**: `docker-compose logs pepperai`
- **Nginx logs**: `docker-compose logs nginx`
- **Redis logs**: `docker-compose logs redis`

### Debug Commands

```bash
# Access container shell
docker-compose exec pepperai bash

# Check file permissions
docker-compose exec pepperai ls -la /app/

# Monitor resource usage
docker stats pepperai-app

# Check network connectivity
docker-compose exec pepperai ping redis
```

## 🆘 Support

If you encounter issues:

1. Check the logs: `docker-compose logs -f`
2. Verify health status: `curl http://localhost/health`
3. Check Docker resources: `docker system df`
4. Restart services: `docker-compose restart`

For additional help, check the main README.md or create an issue in the repository.
