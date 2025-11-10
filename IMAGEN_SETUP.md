# Using Google Imagen 3 with Creative Automation Pipeline

This guide explains how to use Google's Imagen 3 instead of OpenAI DALL-E 3 for image generation.

## Why Use Imagen 3?

- **Cost-effective**: Generally lower cost per image than DALL-E 3
- **High quality**: Photorealistic image generation
- **Fast generation**: Quick turnaround times
- **Multiple aspect ratios**: Native support for 1:1, 9:16, 16:9, 4:3, 3:4
- **Google Cloud integration**: Works seamlessly with GCP infrastructure

## Prerequisites

1. **Google Cloud Account**: You need an active Google Cloud account
2. **Google Cloud Project**: Create a project in Google Cloud Console
3. **Vertex AI API**: Enable the Vertex AI API in your project
4. **Authentication**: Set up authentication (API key or Application Default Credentials)

## Setup Instructions

### Step 1: Install Google Cloud Dependencies

```bash
pip install google-cloud-aiplatform vertexai
```

Or uncomment the lines in `requirements.txt`:
```bash
# Uncomment these lines in requirements.txt
google-cloud-aiplatform>=1.38.0
vertexai>=1.38.0

# Then install
pip install -r requirements.txt
```

### Step 2: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your **Project ID** (you'll need this)
4. Enable the **Vertex AI API**:
   - Go to APIs & Services > Library
   - Search for "Vertex AI API"
   - Click "Enable"

### Step 3: Set Up Authentication

**Option A: Using Application Default Credentials (Recommended)**

```bash
# Install gcloud CLI if you haven't already
# https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

**Option B: Using API Key**

1. Go to APIs & Services > Credentials
2. Create credentials > API key
3. Copy the API key

### Step 4: Configure the Pipeline

**Option A: Use the Imagen config file**

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GOOGLE_API_KEY=your-api-key  # Only if using API key auth

# Run with Imagen config
python pipeline.py --brief examples/example_brief.yaml --config config_imagen.yaml
```

**Option B: Modify config.yaml**

Edit `config.yaml`:

```yaml
genai:
  provider: "imagen"  # Change from "openai" to "imagen"
  api_key: "${GOOGLE_API_KEY}"  # Or leave empty for ADC
  model: "imagen-3.0-generate-001"
  project_id: "your-project-id"  # Your GCP project ID
  location: "us-central1"  # Or your preferred region
```

Then run normally:
```bash
python pipeline.py --brief examples/example_brief.yaml
```

## Usage Examples

### Basic Usage with Imagen

```bash
# Using Application Default Credentials
export GCP_PROJECT_ID=my-project-123
python pipeline.py --brief examples/example_brief.yaml --config config_imagen.yaml

# Using API Key
export GCP_PROJECT_ID=my-project-123
export GOOGLE_API_KEY=your-api-key-here
python pipeline.py --brief examples/example_brief.yaml --config config_imagen.yaml
```

### Generate Superman in Japan Campaign

```bash
# Make sure no input assets exist (to trigger generation)
rm -f input_assets/superman_*.png

# Run with Imagen
export GCP_PROJECT_ID=your-project-id
python pipeline.py --brief examples/example_brief.yaml --config config_imagen.yaml --verbose
```

## Supported Regions

Imagen 3 is available in these regions:
- `us-central1` (Iowa, USA) - Recommended
- `europe-west4` (Netherlands)
- `asia-southeast1` (Singapore)

Choose the region closest to your users for best performance.

## Cost Comparison

**Imagen 3 Pricing** (as of 2024):
- Standard quality: ~$0.020 per image
- High quality: ~$0.040 per image

**DALL-E 3 Pricing**:
- Standard quality (1024×1024): $0.040 per image
- HD quality (1024×1024): $0.080 per image

**For the Superman in Japan campaign (2 products):**
- Imagen 3: ~$0.04 - $0.08
- DALL-E 3: ~$0.08 - $0.16

💡 **Imagen 3 is approximately 50% cheaper than DALL-E 3!**

## Features Comparison

| Feature | Imagen 3 | DALL-E 3 |
|---------|----------|----------|
| Max Resolution | 1024×1024 | 1024×1024 |
| Aspect Ratios | 1:1, 9:16, 16:9, 4:3, 3:4 | 1024×1024, 1024×1792, 1792×1024 |
| Generation Speed | Fast (~5-10s) | Medium (~10-20s) |
| Cost per Image | $0.020 - $0.040 | $0.040 - $0.080 |
| Quality | Photorealistic | Artistic/Photorealistic |
| Safety Filters | Yes | Yes |
| API Retries | Yes (3 attempts) | Yes (3 attempts) |

## Troubleshooting

### Error: "Vertex AI API not enabled"

```bash
# Enable the API
gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
```

### Error: "Permission denied"

Make sure your account has the necessary permissions:
- Vertex AI User
- Service Account Token Creator (if using service accounts)

```bash
# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
    --member="user:your-email@example.com" \
    --role="roles/aiplatform.user"
```

### Error: "Module 'google.cloud.aiplatform' not found"

```bash
# Install the required packages
pip install google-cloud-aiplatform vertexai
```

### Error: "Quota exceeded"

Imagen 3 has rate limits. If you hit them:
1. Wait a few minutes and retry
2. Request a quota increase in Google Cloud Console
3. Use exponential backoff (already implemented in the pipeline)

## Switching Between Providers

You can easily switch between OpenAI and Imagen:

**Use OpenAI:**
```bash
python pipeline.py --brief examples/example_brief.yaml --config config.yaml
```

**Use Imagen:**
```bash
python pipeline.py --brief examples/example_brief.yaml --config config_imagen.yaml
```

Or set the provider in your config file and use the default config.

## Best Practices

1. **Use Application Default Credentials** for better security (no API keys in files)
2. **Choose the right region** for your use case (latency vs. cost)
3. **Monitor costs** in Google Cloud Console
4. **Set up billing alerts** to avoid unexpected charges
5. **Use asset reuse** to minimize generation costs
6. **Test with small campaigns** before scaling up

## Additional Resources

- [Vertex AI Imagen Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Imagen 3 Model Card](https://cloud.google.com/vertex-ai/docs/generative-ai/model-reference/imagen)
- [Google Cloud Pricing Calculator](https://cloud.google.com/products/calculator)
- [Vertex AI Quotas and Limits](https://cloud.google.com/vertex-ai/docs/quotas)

## Support

If you encounter issues:
1. Check the [troubleshooting section](#troubleshooting) above
2. Review Google Cloud logs in Cloud Console
3. Check the pipeline logs in `pipeline.log`
4. Ensure your Google Cloud project has billing enabled
