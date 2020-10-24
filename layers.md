# Layers

## Types

### Hardware

- Physical server
- Virtual Machine
- AWS EC2 instance
- Azure Virtual Machine

### OS

- GNU/Linux
- MS Windows Server

### Virtualization

- VMWare
- Docker

### Managed Service

- AWS RDS
- AWS S3
- Azure SQL Server
- Azure Storage Account

### Service

- GNU/Linux daemon
- Windows service

### Microservice

- Microservice

### Application

- Backend
- Frontend


## Layer data format (JSON structure)

```
'GOOGLE':{
    'appname':'Google',
    'customer':'Google search',
    'url':'https://www.google.com',
    'credentials':emptyCreds,
    'payload':'EMPTY',
    'failure_history':[0,0,0,0,0,0],
    'rt_history':[0,0,0,0,0,0],
    'orange_since':'-',
    'red_since':'-',
    'orange_sent':0,
    'red_sent':0,
    'release_def_ids':[0],
    'latest_deployment':'None'
    }
```