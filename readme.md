# Kubernetes Webhook

Welcome! This repository contains everything you need to set up a mutating webhook that injects environment variables into pod deployments. The project is structured into three main directories:

- `main`: Contains the Python code and Dockerfile.
- `webhook`: Contains the mutating webhook configuration.
- `sample`: Contains a test deployment and service file for testing the mutating webhook configuration.

## Project Structure

```plaintext
.
├── main
│   ├── Dockerfile
│   ├── app.py
│   └── ...
├── webhook
│   ├── mutating-webhook-configuration.yaml
│   └── ...
├── sample
│   ├── deployment.yaml
│   └── service.yaml
└── README.md
└── deployments.yaml
└── service.yaml
└── secret.yaml
```
# Getting Started

## Prerequisites

- Docker installed
- Kubernetes cluster set up
- `kubectl` configured to interact with your cluster
- OpenSSL (for generating SSL certificates)
- Access to a Docker registry (e.g., Docker Hub)

## Steps to Set Up the Project

### Build the Docker Image

Navigate to the main directory and build the Docker image:

```sh
cd main
docker build -t <your-docker-registry-username>/mutating-webhook:latest .
```

### Push the Docker Image

Push the built Docker image to your Docker registry:

```sh
docker push <your-docker-registry-username>/mutating-webhook:latest
```
### Generate SSL Certificates

Generate SSL certificates for the webhook. These will be used to create a Kubernetes secret.

```sh
openssl req -newkey rsa:2048 -nodes -keyout webhook.key -x509 -days 365 -out webhook.crt
```

### Encode the certificates in Base64:

```sh
base64 webhook.crt > webhook.crt.base64
base64 webhook.key > webhook.key.base64
```

### Update the secret.yaml file with the encoded certificate and key:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: webhook-secret
  namespace: default
type: Opaque
data:
  webhook.crt: <Base64_encoded_cert>
  webhook.key: <Base64_encoded_key>
```

### Deploy the Webhook

Update the deployments.yaml file in the repository with your Docker image details:

```yaml
spec:
  containers:
  - name: mutating-webhook
    image: <your-docker-registry-username>/mutating-webhook:latest
```

### Apply the deployment, service, and secret configurations: 

```sh
kubectl apply -f secret.yaml
kubectl apply -f deployments.yaml
kubectl apply -f service.yaml
```

### Create the Mutating Webhook Configuration

Finally, apply the mutating webhook configuration from the webhook directory:

```sh
kubectl apply -f webhook/mutating-webhook-configuration.yaml
```

### Testing the Mutating Webhook

To test if the mutating webhook is working correctly, you can use the sample deployment and service files provided in the sample directory:

```sh
kubectl apply -f sample/deployment.yaml
kubectl apply -f sample/service.yaml
```

These files will create a sample deployment and service which should have the environment variables injected by the mutating webhook.

### Conclusion

You are now ready to use the Kubernetes Mutating Webhook to inject environment variables into your pod deployments. Make sure to follow the sequence of Kubernetes object creation: first the secret, then the deployment and service, and finally the mutating webhook configuration.

If you have any questions or run into issues, please feel free to open an issue in this repository. Happy coding!
















