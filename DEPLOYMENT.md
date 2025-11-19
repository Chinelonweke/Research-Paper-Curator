# Research Paper Curator - Deployment Guide

## Current Status
✅ Phase 1-5 Complete
- Core system working
- Authentication added
- Airflow automation running
- Redis caching active
- Ready for production!

## Quick Deploy to DigitalOcean

### 1. Create Droplet
- Go to digitalocean.com
- Create Droplet: Ubuntu 22.04, $12/month
- Note your IP address

### 2. Deploy
```powershell
# From your PC
.\deploy.ps1 -ServerIP "YOUR_IP"
```

### 3. Access
- UI: http://YOUR_IP:7860
- API: http://YOUR_IP:8000
- Airflow: http://YOUR_IP:8080 (admin/admin)

## What's Working
- ✅ Search papers
- ✅ Browse papers
- ✅ User authentication
- ✅ Daily automation (2 AM)
- ✅ Redis caching
- ✅ NeonDB storage

## Costs
- DigitalOcean: $12/month
- NeonDB: $0 (free tier)
- Domain (optional): $10/year
- **Total: ~$13/month**

## Next Steps After Deployment
1. Get domain name
2. Add NGINX reverse proxy
3. Install SSL certificate
4. Set up monitoring
5. Add CDN (optional)

## Support
- API Docs: http://localhost:8000/docs
- Airflow: http://localhost:8080
