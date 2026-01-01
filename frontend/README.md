# Research Paper Curator - Vue.js Frontend

A modern Vue.js 3 frontend for the Research Paper Curator project, featuring Vuetify 3 Material Design components.

## Tech Stack

- **Vue 3.4+** - Composition API
- **Vite 5** - Build tool
- **TypeScript 5** - Type safety
- **Vuetify 3.5** - Material Design components
- **Pinia 2** - State management
- **Vue Router 4** - Routing
- **Axios** - HTTP client

## Features

- **Paper Search** - Hybrid semantic and keyword search
- **AI Q&A** - Get answers with real-time streaming
- **Paper Collections** - Save papers and add notes
- **Search History** - Track your searches
- **Dark/Light Theme** - With system preference detection
- **Full Authentication** - Login, register, profile

## Development

### Prerequisites

- Node.js 18+
- npm or yarn

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:3000

### Build

```bash
# Type check and build
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
src/
├── components/         # Reusable Vue components
│   ├── common/        # Shared components
│   ├── papers/        # Paper-related components
│   ├── qa/            # Q&A components
│   ├── auth/          # Authentication components
│   └── collections/   # Collection components
├── pages/             # Route page components
├── layouts/           # Layout wrappers
├── stores/            # Pinia stores
├── services/          # API and WebSocket services
├── plugins/           # Vue plugins (Vuetify, Axios)
├── router/            # Vue Router config
├── types/             # TypeScript interfaces
└── composables/       # Vue composables
```

## Environment Variables

Create `.env` file:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_APP_TITLE=Research Paper Curator
```

## Docker

Build and run with Docker:

```bash
# From project root
docker build -f docker/Dockerfile.frontend -t research-paper-curator-frontend .
docker run -p 3000:3000 research-paper-curator-frontend
```

Or use Docker Compose:

```bash
cd docker
docker-compose up vue-frontend
```

## API Integration

The frontend connects to the FastAPI backend:

- `POST /auth/login` - User login
- `POST /auth/register` - User registration
- `GET /auth/me` - Current user
- `GET /api/papers` - List papers
- `POST /api/papers/search` - Search papers
- `POST /api/ask` - Ask questions
- `WS /ws/{client_id}` - Real-time streaming

## Contributing

1. Follow Vue.js style guide
2. Use Composition API with `<script setup>`
3. Type all props and emits
4. Use Pinia stores for global state
