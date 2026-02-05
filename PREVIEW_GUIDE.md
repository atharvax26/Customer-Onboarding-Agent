# How to Preview the Customer Onboarding Agent Frontend

## Prerequisites
You need Node.js and npm installed on your system. If you don't have them:
1. Download Node.js from https://nodejs.org/ (LTS version recommended)
2. Install it - this will also install npm

## Steps to Preview

### 1. Navigate to the frontend directory
```bash
cd frontend
```

### 2. Install dependencies
```bash
npm install
```

### 3. Start the development server
```bash
npm run dev
```

### 4. Open your browser
The development server will typically start on `http://localhost:5173` (Vite's default port).
You should see a message in the terminal like:
```
Local:   http://localhost:5173/
Network: use --host to expose
```

## What You'll See

### Home Page
- Welcome message and feature overview
- Navigation bar with Home, Login, Register links

### Authentication Flow
1. **Register Page** (`/register`):
   - Email input field
   - Role selection (Developer, Business User, Admin)
   - Password and confirm password fields
   - Create Account button

2. **Login Page** (`/login`):
   - Email and password fields
   - Sign In button
   - Link to registration page

### After Authentication
- Navigation updates to show user email and role
- Onboarding link becomes available
- Analytics link (Admin users only)
- User dropdown menu with logout option

### Protected Routes
- `/onboarding` - Requires authentication
- `/analytics` - Requires Admin role
- Unauthorized access redirects to login or shows unauthorized page

## Current Limitations

Since the backend isn't running yet, the authentication will fail when you try to login/register. The forms will show error messages like "Login failed" or "Registration failed" because there's no backend API to connect to.

## Next Steps

To make authentication work, you'll need to:
1. Start the backend server (from the `backend` directory)
2. Ensure the backend is running on the expected port
3. Update the API endpoints in the frontend if needed

## Troubleshooting

### Port Already in Use
If port 5173 is busy, Vite will automatically try the next available port (5174, 5175, etc.)

### Module Not Found Errors
Run `npm install` to ensure all dependencies are installed

### TypeScript Errors
The code should compile without errors. If you see TypeScript issues, check that all files are saved properly.