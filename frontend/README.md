# Chat RAG Frontend

React + TypeScript frontend cho Chat RAG Desktop Application với **Shadcn/ui**.

## 🎨 UI Library: Shadcn/ui

### Tại sao Shadcn/ui?
- ✅ **Dễ custom**: Copy-paste components, full control
- ✅ **Đẹp**: Modern design, dark mode support
- ✅ **Chuyên nghiệp**: Used by Vercel, Linear, và nhiều startups
- ✅ **TypeScript**: Full TypeScript support
- ✅ **Accessible**: WCAG compliant

## 🚀 Tech Stack

- **React 18** với TypeScript
- **Vite** - Build tool nhanh
- **Shadcn/ui** - UI component library
- **Tailwind CSS** - Utility-first CSS
- **Zustand** - State management
- **React Query** - Data fetching & caching
- **Axios** - HTTP client
- **Lucide React** - Icons

## 📦 Installation

```bash
# Install dependencies
npm install

# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## 📁 Project Structure

```
src/
├── components/
│   ├── ui/              # Shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   └── ...
│   ├── sidebar/         # Custom components
│   ├── chat/            # Custom components
│   └── knowledge-base/  # Custom components
├── pages/               # Main pages
├── services/            # API clients
├── store/               # Zustand stores
├── types/               # TypeScript types
├── lib/                 # Utilities (cn, etc.)
└── utils/               # Helper functions
```

## 🎨 Adding Shadcn/ui Components

```bash
# Sử dụng CLI (nếu có)
npx shadcn-ui@latest add button

# Hoặc copy-paste từ https://ui.shadcn.com/docs/components
```

## 🎯 Features

- 🎨 Modern UI với dark theme
- 💬 Chat interface với streaming
- 📁 File upload & management
- 🔍 Source management
- ⚙️ Settings panel
- 🌙 Dark mode support

## 📚 Resources

- [Shadcn/ui Documentation](https://ui.shadcn.com)
- [Tailwind CSS](https://tailwindcss.com)
- [Vite Documentation](https://vite.dev)
