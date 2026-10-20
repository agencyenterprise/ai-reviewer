# Draft Detective - Kubernetes Deployment

Simple, plug-and-play Kubernetes deployment for Draft Detective.
**Optimized for OpenShift** with support for vanilla Kubernetes.

## Prerequisites

- Kubernetes cluster (1.24+) or OpenShift (4.10+)
- `kubectl` or `oc` CLI
- Container registry access (Quay.io, Docker Hub, GitHub Container Registry, etc.)
- Your API keys (OpenAI, Langfuse, etc.)

## Quick Start

### 1. Build and Push Container Images

From the project root directory:

```bash
# Set your container registry
export REGISTRY=quay.io/your-org  # or docker.io/your-username, ghcr.io/your-org

# Build images
docker build -t $REGISTRY/ai-reviewer-api:latest -f Dockerfile .
# The frontend calls the API at NEXT_PUBLIC_API_URL, from the browser and from its own
# server code. The value is fixed when the image is built (setting it in frontend-config
# has no effect). With http://localhost:8000 (also the default) and the port-forward
# quick start, only the browser reaches the API: file downloads, the admin pages and
# the About page call it from inside the pod and fail. Behind Routes or an Ingress,
# pass the API's public URL, which both sides can reach, and rebuild once you know it.
docker build -t $REGISTRY/ai-reviewer-frontend:latest -f frontend/Dockerfile frontend/ \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000

# Push to registry
docker push $REGISTRY/ai-reviewer-api:latest
docker push $REGISTRY/ai-reviewer-frontend:latest

# Update manifests to use your images
cd k8s
sed -i.bak "s|image: ai-reviewer-api:latest|image: $REGISTRY/ai-reviewer-api:latest|" api.yaml
sed -i.bak "s|image: ai-reviewer-frontend:latest|image: $REGISTRY/ai-reviewer-frontend:latest|" frontend.yaml
```

### 2. Configure Environment Variables

```bash
# Copy template and edit with your API keys
cp ../.env.template .env
# Edit .env with your OpenAI key, database password, etc.
```

The template's defaults are for local development. Before you create the secret, check these in `.env`:

- `DATABASE_URL`: use the `db` Service as the host, with the same user, password and database name as `POSTGRES_USER`, `POSTGRES_PASSWORD` and `POSTGRES_DB` (for example `postgresql://ai_reviewer_user:<password>@db:5432/ai_reviewer`).
- `FRONTEND_URL` and `MCP_BASE_URL`: the API builds share links and its OAuth base URL from them. With the port-forward quick start below, keep the `localhost` defaults (MCP clients also need `kubectl port-forward -n ai-reviewer svc/api 8000:8000`). When you expose the app through Routes or an Ingress, use their public URLs instead (`MCP_BASE_URL` keeps its `/mcp` path). On OpenShift the Routes get their hosts only when they are created, so set these two after deploying (see step 3).

### 3. Deploy to Cluster

**OpenShift:**

```bash
oc create namespace ai-reviewer
oc create secret generic app-secrets --from-env-file=.env -n ai-reviewer
oc apply -f . -n ai-reviewer

# Get the URL
oc get routes -n ai-reviewer

# Put the Route URLs in FRONTEND_URL and MCP_BASE_URL in .env, then update the secret and restart the API
oc create secret generic app-secrets --from-env-file=.env -n ai-reviewer --dry-run=client -o yaml | oc apply -f -
oc rollout restart deployment/api -n ai-reviewer
```

**Vanilla Kubernetes:**

```bash
kubectl create namespace ai-reviewer
kubectl create secret generic app-secrets --from-env-file=.env -n ai-reviewer

# Apply all manifests (OpenShift Routes will be ignored)
kubectl apply -f configmap.yaml -f database.yaml -f api.yaml -f frontend.yaml -n ai-reviewer

# Access via port-forward (the browser calls the API on localhost:8000)
kubectl port-forward -n ai-reviewer svc/frontend 3000:3000 &
kubectl port-forward -n ai-reviewer svc/api 8000:8000
# Visit http://localhost:3000
```

## Platform-Specific Notes

### OpenShift

- Routes are automatically created for external access
- Network policies work out of the box
- Default storage class is used automatically
- No additional configuration needed

### AWS EKS

```bash
# Optional: Use specific storage class
sed -i 's|# storageClassName: ""|storageClassName: "gp3"|' database.yaml api.yaml
```

### Google GKE

```bash
# Optional: Use specific storage class
sed -i 's|# storageClassName: ""|storageClassName: "standard"|' database.yaml api.yaml
```

### Vanilla Kubernetes with Ingress

Save this as `ingress.yaml` and apply separately:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ai-reviewer
spec:
  ingressClassName: nginx
  rules:
    - host: ai-reviewer.yourdomain.com
      http:
        paths:
          - path: /api
            pathType: Prefix
            backend:
              service: { name: api, port: { number: 8000 } }
          - path: /
            pathType: Prefix
            backend:
              service: { name: frontend, port: { number: 3000 } }
```

## Common Operations

**View logs:**

```bash
kubectl logs -f deployment/api -n ai-reviewer
kubectl logs -f deployment/frontend -n ai-reviewer
```

**Check status:**

```bash
kubectl get pods -n ai-reviewer
kubectl get all -n ai-reviewer
```

**Update environment variables:**

```bash
kubectl create secret generic app-secrets --from-env-file=.env \
  --dry-run=client -o yaml -n ai-reviewer | kubectl apply -f -
kubectl rollout restart deployment/api -n ai-reviewer
```

**Database backup:**

```bash
kubectl exec deployment/db -n ai-reviewer -- \
  pg_dump -U ai_reviewer_user ai_reviewer > backup-$(date +%Y%m%d).sql
```

## Optional: Network Security

For production, apply network policies to restrict pod-to-pod traffic:

```bash
kubectl apply -f network-policy.yaml -n ai-reviewer
```

**Note:** Requires a CNI plugin that supports NetworkPolicy (Calico, Cilium, Weave).
OpenShift has this by default.

## Troubleshooting

**Pods not starting:**

```bash
kubectl describe pod -l app=api -n ai-reviewer
kubectl logs -l app=api -n ai-reviewer
```

**Image pull errors:**

```bash
# Verify image names in manifests match your registry
grep "image:" api.yaml frontend.yaml

# For private registries, create image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=your-registry.io \
  --docker-username=your-username \
  --docker-password=your-password \
  -n ai-reviewer

# Add to deployments under spec.template.spec:
#   imagePullSecrets:
#   - name: regcred
```

**Database connection issues:**

```bash
kubectl logs deployment/api -n ai-reviewer | grep -i database
kubectl exec -it deployment/db -n ai-reviewer -- psql -U ai_reviewer_user -d ai_reviewer
```

## What's Deployed

| Component    | Description                          | Port |
| ------------ | ------------------------------------ | ---- |
| **frontend** | Next.js UI                           | 3000 |
| **api**      | FastAPI backend with auto-migrations | 8000 |
| **db**       | PostgreSQL 16 + pgvector             | 5432 |

**Persistent Storage:**

- Database data: 20Gi
- API uploads: 20Gi

## Clean Up

Remove everything:

```bash
kubectl delete namespace ai-reviewer
```
