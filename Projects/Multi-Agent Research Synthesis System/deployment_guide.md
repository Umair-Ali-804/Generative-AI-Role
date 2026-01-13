# Deployment Guide

## Local Development Setup

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.template .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Required environment variables:
```bash
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 3. Test Installation

```bash
# Run tests
python test_system.py

# Quick smoke test
python main.py -q "Test query about AI" -n 1
```

## Production Deployment

### Option 1: Docker Deployment (Recommended)

```bash
# Build Docker image
docker build -t research-synthesis:latest .

# Run container
docker run -it \
  --env-file .env \
  -v $(pwd)/output:/app/output \
  research-synthesis:latest \
  python main.py -i
```

### Option 2: Docker Compose

```bash
# Start service
docker-compose up -d

# View logs
docker-compose logs -f

# Stop service
docker-compose down
```

### Option 3: AWS EC2 Deployment

#### Step 1: Launch EC2 Instance

```bash
# Recommended: t3.xlarge or larger
# AMI: Ubuntu 22.04 LTS
# Storage: 30GB+ EBS
```

#### Step 2: Install Dependencies

```bash
# SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo apt install docker-compose -y

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

#### Step 3: Deploy Application

```bash
# Clone repository
git clone https://github.com/yourusername/research-synthesis-system.git
cd research-synthesis-system

# Set up environment
nano .env  # Add your API keys

# Build and run
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

#### Step 4: Set Up Nginx (Optional)

If deploying as web service:

```bash
# Install Nginx
sudo apt install nginx -y

# Configure reverse proxy
sudo nano /etc/nginx/sites-available/research-synthesis

# Add configuration:
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/research-synthesis /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 4: AWS Lambda Deployment

For serverless deployment:

#### Step 1: Create Lambda Function

```bash
# Install AWS SAM CLI
pip install aws-sam-cli

# Create SAM template (template.yaml)
```

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31

Resources:
  ResearchSynthesisFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: research-synthesis
      Runtime: python3.11
      Handler: lambda_handler.handler
      CodeUri: .
      Timeout: 900
      MemorySize: 3008
      Environment:
        Variables:
          OPENAI_API_KEY: !Ref OpenAIKey
          ANTHROPIC_API_KEY: !Ref AnthropicKey
```

#### Step 2: Create Lambda Handler

Create `lambda_handler.py`:

```python
import json
from research_synthesis_system import ResearchSynthesisWorkflow

def handler(event, context):
    """AWS Lambda handler"""
    
    query = event.get('query', '')
    max_iterations = event.get('max_iterations', 2)
    
    workflow = ResearchSynthesisWorkflow()
    result = workflow.run(query, max_iterations)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'synthesis': result['final_output'],
            'quality_score': result['quality_score'],
            'papers_count': len(result['papers'])
        })
    }
```

#### Step 3: Deploy

```bash
# Build and deploy
sam build
sam deploy --guided
```

### Option 5: Kubernetes Deployment

#### Step 1: Create Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: research-synthesis
spec:
  replicas: 2
  selector:
    matchLabels:
      app: research-synthesis
  template:
    metadata:
      labels:
        app: research-synthesis
    spec:
      containers:
      - name: research-synthesis
        image: research-synthesis:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: anthropic
        resources:
          requests:
            memory: "4Gi"
            cpu: "2"
          limits:
            memory: "8Gi"
            cpu: "4"
```

Create `k8s/secret.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: api-keys
type: Opaque
stringData:
  openai: your-openai-key
  anthropic: your-anthropic-key
```

#### Step 2: Deploy to Kubernetes

```bash
# Apply secrets
kubectl apply -f k8s/secret.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml

# Check status
kubectl get pods
kubectl logs -f <pod-name>
```

## Monitoring & Observability

### LangSmith Integration

```bash
# Enable in .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=research-synthesis-prod
```

### Logging

Add to your deployment:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_synthesis.log'),
        logging.StreamHandler()
    ]
)
```

### Prometheus Metrics (Optional)

```python
from prometheus_client import Counter, Histogram

queries_processed = Counter('queries_processed_total', 'Total queries processed')
query_duration = Histogram('query_duration_seconds', 'Query processing duration')
quality_score = Histogram('quality_score', 'Synthesis quality score')
```

## Performance Optimization

### 1. Caching

Implement Redis caching for papers:

```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def get_cached_papers(query):
    cached = redis_client.get(f"papers:{query}")
    if cached:
        return json.loads(cached)
    return None

def cache_papers(query, papers):
    redis_client.setex(
        f"papers:{query}",
        3600,  # 1 hour TTL
        json.dumps(papers)
    )
```

### 2. Batch Processing

For high volume:

```python
from concurrent.futures import ThreadPoolExecutor

def process_batch(queries, max_workers=4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(workflow.run, queries))
    return results
```

### 3. GPU Acceleration

For FAISS with GPU:

```bash
# Install GPU version
pip install faiss-gpu

# Use in code
import faiss
index = faiss.IndexFlatL2(dimension)
gpu_index = faiss.index_cpu_to_gpu(faiss.StandardGpuResources(), 0, index)
```

## Scaling Considerations

### Horizontal Scaling

- Deploy multiple instances behind load balancer
- Use message queue (RabbitMQ, SQS) for job distribution
- Implement worker pool pattern

### Vertical Scaling

- Minimum: 4GB RAM, 2 CPU cores
- Recommended: 8GB RAM, 4 CPU cores
- High volume: 16GB+ RAM, 8+ CPU cores

### Database for Results

Use PostgreSQL for storing results:

```sql
CREATE TABLE research_results (
    id SERIAL PRIMARY KEY,
    query TEXT NOT NULL,
    synthesis TEXT,
    quality_score FLOAT,
    papers_analyzed INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

CREATE INDEX idx_quality ON research_results(quality_score);
CREATE INDEX idx_created ON research_results(created_at);
```

## Security Best Practices

1. **Never commit API keys** to version control
2. Use **environment variables** or secret management (AWS Secrets Manager, HashiCorp Vault)
3. Implement **rate limiting** to prevent abuse
4. Use **HTTPS** for all API communications
5. Implement **authentication** for production deployments
6. Regular **security updates** of dependencies

```bash
# Check for vulnerabilities
pip install safety
safety check
```

## Backup & Recovery

```bash
# Backup results
tar -czf backup_$(date +%Y%m%d).tar.gz output/

# Automated backups
0 0 * * * /path/to/backup_script.sh
```

## Troubleshooting

### High Memory Usage

```bash
# Monitor memory
docker stats

# Solution: Reduce batch size or MAX_PAPERS
```

### API Rate Limits

```python
# Implement exponential backoff
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_api():
    # API call here
    pass
```

### Slow Performance

1. Enable caching
2. Reduce paper count
3. Use GPU for FAISS
4. Implement parallel processing

## Cost Optimization

### API Usage

- Cache results to reduce API calls
- Use cheaper models for non-critical tasks
- Implement request batching

### Compute

- Use spot instances on AWS (60-90% savings)
- Auto-scaling based on load
- Schedule off-peak processing

## Monitoring Checklist

- [ ] API response times
- [ ] Quality scores over time
- [ ] Error rates
- [ ] API costs
- [ ] System resource usage
- [ ] Hallucination rates

## Support

For deployment issues:
- Check logs: `docker-compose logs -f`
- Run diagnostics: `python test_system.py`
- Enable verbose logging: `--log-level DEBUG`

---

Last Updated: 2024-01-15