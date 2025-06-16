# Sales/Inventory System with LangGraph

A modern Python-based sales and inventory management system powered by LangGraph workflows, Pydantic data validation, Google Gemini AI, and JWT authentication.

## Features

- **AI-Powered Workflows**: LangGraph-based agent workflows for intelligent inventory management
- **Modern Data Validation**: Pydantic v2+ models for robust data handling
- **AI Integration**: Google Gemini API for intelligent analysis and recommendations
- **Video Processing**: FFmpeg integration for product media processing
- **Secure Authentication**: JWT-based authentication system
- **RESTful API**: FastAPI-based REST API with automatic documentation
- **Database Integration**: SQLAlchemy ORM with migration support

## Project Structure

```
sales-inventory-system/
├── src/
│   ├── models/          # Pydantic data models
│   ├── agents/          # LangGraph agent implementations
│   ├── workflows/       # LangGraph workflow definitions
│   └── tools/           # External tool integrations (FFmpeg, Gemini)
├── examples/            # Sample data and usage examples
├── tests/              # Unit and integration tests
├── requirements.txt    # Python dependencies
├── .env.example       # Environment variables template
└── README.md          # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- FFmpeg (for video processing)
- Google Gemini API key

### Setup Instructions

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd sales-inventory-system
   ```

2. **Create and activate a virtual environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` file with your actual values (see Configuration section below).

5. **Install FFmpeg** (if not already installed):

   **macOS**:

   ```bash
   brew install ffmpeg
   ```

   **Ubuntu/Debian**:

   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

   **Windows**:
   Download from [FFmpeg official website](https://ffmpeg.org/download.html)

## Configuration

### API Key Setup

#### Google Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add the key to your `.env` file:
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

#### JWT Secret Key

Generate a secure secret key for JWT tokens:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Add the generated key to your `.env` file:

```
JWT_SECRET_KEY=your_generated_secret_key
```

### Environment Variables

Required environment variables (see `.env.example` for full list):

- `GEMINI_API_KEY`: Your Google Gemini API key
- `JWT_SECRET_KEY`: Secret key for JWT token signing
- `DATABASE_URL`: Database connection string
- `FFMPEG_PATH`: Path to FFmpeg executable (optional, auto-detected if in PATH)

## Basic Usage

### Starting the Application

```bash
# Run the development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

- API Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`

### Example Usage

```python
from src.models.inventory import Product, InventoryItem
from src.workflows.sales_workflow import SalesWorkflow
from src.tools.gemini_tool import GeminiAnalyzer

# Create a product
product = Product(
    name="Gaming Laptop",
    sku="LAP-001",
    price=1299.99,
    category="Electronics"
)

# Initialize workflow
workflow = SalesWorkflow()

# Analyze inventory with AI
analyzer = GeminiAnalyzer()
insights = await analyzer.analyze_inventory_trends(product)
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/test_models.py
```

### Development Tools

Format code:

```bash
black src/ tests/
```

Lint code:

```bash
ruff check src/ tests/
```

Type checking:

```bash
mypy src/
```

## API Endpoints

### Authentication

- `POST /auth/login` - User authentication
- `POST /auth/register` - User registration
- `POST /auth/refresh` - Refresh JWT token

### Inventory Management

- `GET /inventory/` - List all inventory items
- `POST /inventory/` - Create new inventory item
- `GET /inventory/{item_id}` - Get specific inventory item
- `PUT /inventory/{item_id}` - Update inventory item
- `DELETE /inventory/{item_id}` - Delete inventory item

### Sales Operations

- `GET /sales/` - List sales records
- `POST /sales/` - Create new sale
- `GET /sales/analytics` - Sales analytics and insights

### AI Features

- `POST /ai/analyze-inventory` - AI-powered inventory analysis
- `POST /ai/predict-demand` - Demand prediction
- `POST /ai/optimize-pricing` - Price optimization suggestions

## Architecture

The system follows a modular architecture with clear separation of concerns:

- **Models**: Pydantic models for data validation and serialization
- **Agents**: LangGraph agents for complex AI-driven workflows
- **Workflows**: Orchestrated business logic using LangGraph
- **Tools**: External integrations (Gemini AI, FFmpeg, databases)
- **API Layer**: FastAPI REST endpoints with automatic documentation

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run tests and linting: `pytest && black . && ruff check .`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:

- Create an issue in the GitHub repository
- Check the documentation at `http://localhost:8000/docs` when running the application
- Review the examples in the `examples/` directory
