# Frontend Setup

## Overview

React application with TypeScript, built using Vite and managed with pnpm.

## Requirements

- [Node.js](https://nodejs.org/) >= 20.19 (or 22+) — **Node 18 is not supported** (Vite 7 + Tailwind CSS 4 require Node 20.19+)
- [pnpm](https://pnpm.io/) >= 10

> **Note**: If using nvm, switch to Node 22 before installing:
> ```bash
> nvm use 22
> ```

```bash
npm install -g pnpm
```

## Getting Started

### Install dependencies

```bash
pnpm install
```

### Start development server

```bash
pnpm dev
```

The app will be available at [http://localhost:5173](http://localhost:5173).

## Available Scripts

| Command | Description |
|---------|-------------|
| `pnpm dev` | Start development server with HMR |
| `pnpm build` | Build for production (outputs to `dist/`) |
| `pnpm preview` | Preview the production build locally |
| `pnpm lint` | Lint with oxlint |
| `pnpm format` | Format with oxfmt (indent: 2 spaces) |
| `pnpm format:check` | Check formatting without writing |
| `pnpm typecheck` | Type-check with tsgo (TypeScript native) |

## Environment Variables

Copy `.env.local` and adjust as needed:

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:8000` | Backend API base URL |
| `VITE_WS_URL` | `ws://localhost:8000` | WebSocket base URL (simulation progress) |

## Tech Stack

### Runtime

- **React** 19
- **TypeScript** 5
- **Vite** 7
- **react-router-dom** 7 — client-side routing
- **@tanstack/react-query** 5 — server state management
- **axios** — HTTP client (`src/lib/api.ts`)
- **recharts** 3 — bar charts / distribution visualization
- **Tailwind CSS** 4 — utility-first styling

### Dev Tools

| Tool | Package | Description |
|------|---------|-------------|
| oxlint | `oxlint` | Fast linter (Rust-based, Oxc project) |
| oxfmt | `oxfmt` | Fast formatter (alpha, indent: 2 spaces) |
| tsgo | `@typescript/native-preview` | TypeScript Go-based compiler preview (TS7) |
