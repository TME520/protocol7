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

### Current

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

### Updated

| Field | Type | Defined / Computed | Example |
| ----- | ---- | ------------------ | ------- |
| appname | String | D | Google |
| customer | String | D | Google search |
| url | String | D | https://www.google.com |
| credentials | KVP | D | { 'foo' : 'bar' } |
| payload | String | C | HTTP 200 OK |
| failure_history | Array | C | [0,0,0,0,0,0] |
| rt_history | Array | C | [0,0,0,0,0,0] |
| orange_since | String | C | Sunday 25 October @ 16:50 |
| red_since | String | C | Sunday 25 October @ 16:50 |
| orange_sent | Integer | C | 0 |
| red_sent | Integer | C | 1 |
| release_def_ids | Array | D | [0] |
| latest_deployment | String | C | None |
| protocol | String | D | HTTP |
| retries | Integer | D | 3 |
| timeout | Integer | D | 10 |
| http_success | Array | D | [200,301] |
| http_failure | Array | D | [401,404,500] |
| http_maintenance | Array | D | [307,503] |
| payload_success | String | D | "Welcome" |
| payload_failure | String | D | "Runtime error" |
| payload_maintenance | String | D | "currently under maintenance" |
| flappingCntr | Integer | C | 4 |
| flappingStatus | Integer | C | 2 |
| previousStatus | String | C | U |
| currentStatus | String | C | D |
| ack | String | D | 20201015 |
| runbook | String | D | http://runbooks.com |
