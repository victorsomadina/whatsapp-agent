# NPF Pensions WhatsApp Agent

A containerized WhatsApp bot for NPF Pensions Ltd that provides information about pension services using AI-powered conversations with voice support.

## 📁 Project Structure

```
NPFPension/
├── whatsapp-agent/           # Main application directory
│   ├── app.py               # FastAPI application
│   ├── agent.py             # WhatsApp agent logic
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Docker container configuration
│   ├── docker-compose.yml  # Docker Compose orchestration
│   ├── .dockerignore       # Docker build context exclusions
│   ├── .env.example        # Environment variables template
│   └── ...                 # Other application files
└── README.md               # Project documentation
```

**Note**: All Docker commands should be run from within the `whatsapp-agent/` directory.

## 🚀 Features

- **Text and Voice Message Support**: Handles both text messages and voice messages
- **AI-Powered Responses**: Uses Groq's LLM for intelligent responses
- **Interactive UI**: Supports WhatsApp interactive buttons and lists for better UX
- **Speech-to-Text**: Converts voice messages to text using Groq's Whisper
- **Text-to-Speech**: Converts responses to audio using ElevenLabs
- **Memory Support**: Maintains conversation context using LangGraph
- **Session Management**: Automatic inactivity detection and session termination
- **Containerized**: Easy deployment with Docker and Docker Compose

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/) (v20.10 or higher)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0 or higher)
- WhatsApp Business API access
- API keys for Groq and ElevenLabs

## 🐳 Quick Start with Docker

### 1. Clone and Setup

```bash
git clone <your-repository-url>
cd NPFPension/whatsapp-agent
```

### 2. Configure Environment Variables

Create a `.env` file in the `whatsapp-agent` directory:

```bash
# WhatsApp API Configuration
# Get these from your Facebook Developer account and WhatsApp Business API setup
WHATSAPP_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token_here

# AI/LLM Configuration
# Get your API key from https://console.groq.com/
GROQ_API_KEY=your_groq_api_key_here

# Text-to-Speech Configuration (ElevenLabs)
# Get these from https://elevenlabs.io/
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_VOICE_ID=your_preferred_voice_id_here
TTS_MODEL_NAME=eleven_monolingual_v1

# Server Configuration
PORT=8080
```

### 3. Build and Run with Docker Compose

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode (background)
docker-compose up --build -d
```

### 4. Verify Deployment

The application will be available at:

- **Health Check**: http://localhost:8080/health
- **Root Endpoint**: http://localhost:8080/
- **WhatsApp Webhook**: http://localhost:8080/whatsapp

## 🛠️ Alternative Docker Commands

### Build Image Only

```bash
cd whatsapp-agent
docker build -t npf-whatsapp-agent .
```

### Run Container Manually

```bash
cd whatsapp-agent
docker run -d \
  --name npf-whatsapp-agent \
  -p 8080:8080 \
  --env-file .env \
  npf-whatsapp-agent
```

### View Logs

```bash
# Docker Compose
docker-compose logs -f

# Direct Docker
docker logs -f npf-whatsapp-agent
```

### Stop Services

```bash
# Docker Compose
docker-compose down

# Direct Docker
docker stop npf-whatsapp-agent
docker rm npf-whatsapp-agent
```

## 🔧 Development Setup

For local development without Docker:

### 1. Install Python Dependencies

```bash
cd whatsapp-agent
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Locally

```bash
python app.py
```

## 🌐 Production Deployment

### Using Docker Compose with Nginx (Recommended)

Uncomment the nginx service in `whatsapp-agent/docker-compose.yml` and create nginx configuration:

```bash
cd whatsapp-agent
mkdir nginx
# Add your nginx.conf and SSL certificates
docker-compose up -d
```

### Environment-Specific Configurations

For different environments, create separate compose files:

```bash
cd whatsapp-agent

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d
```

## 🔗 API Endpoints

| Endpoint    | Method   | Description                               |
| ----------- | -------- | ----------------------------------------- |
| `/`         | GET      | Root endpoint - service status            |
| `/health`   | GET      | Detailed health check with service status |
| `/whatsapp` | GET/POST | WhatsApp webhook for message handling     |

## 🏢 Services Offered

The WhatsApp agent provides information about:

1. **Audited Accounts**
2. **PenCom Compliance**
3. **Fund Management**
4. **Pension Calculator**
5. **Whistle Blowing**
6. **FAQ Support**
7. **Customer Login Assistance**

## 🏗️ Architecture

- **FastAPI**: High-performance web framework for handling HTTP requests
- **LangGraph**: Agent framework with memory support and conversation flow
- **Groq**: LLM provider for text generation and speech-to-text processing
- **ElevenLabs**: Professional text-to-speech conversion
- **WhatsApp Business API**: Message handling and rich media support
- **Docker**: Containerization for consistent deployments

## 📊 Monitoring and Health Checks

The application includes built-in health monitoring:

```bash
# Check application health
curl http://localhost:8080/health

# Docker health check
docker inspect --format='{{.State.Health.Status}}' npf-whatsapp-agent
```

## 🔐 Security Considerations

- Environment variables are used for sensitive configuration
- Non-root user in Docker container for security
- Input validation and error handling
- Session management with automatic cleanup
- HTTPS recommended for production deployments

## 🐛 Troubleshooting

### Common Issues:

1. **Container won't start**:

   ```bash
   cd whatsapp-agent

   # Check logs
   docker-compose logs whatsapp-agent

   # Verify environment variables
   docker-compose config
   ```

2. **API Keys not working**:

   - Verify all environment variables are set correctly
   - Check API key validity and permissions
   - Ensure WhatsApp webhook is properly configured

3. **Port conflicts**:

   ```bash
   cd whatsapp-agent

   # Use different port
   docker-compose down
   # Edit docker-compose.yml ports section
   docker-compose up -d
   ```

4. **Memory issues**:

   ```bash
   # Check container resources
   docker stats npf-whatsapp-agent

   # Increase Docker memory limits if needed
   ```

## 📝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📧 Support

For support and questions:

- Email: support@npfpensions.com
- GitHub Issues: [Create an issue](https://github.com/your-repo/issues)

---

**Made with ❤️ for NPF Pensions Ltd**
