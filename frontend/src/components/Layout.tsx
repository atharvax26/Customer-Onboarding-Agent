import React from 'react'
import Navigation from './Navigation'

interface LayoutProps {
  children: React.ReactNode
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <Navigation />
        </div>
      </header>
      <main className="main">
        <div className="container">
          {children}
        </div>
      </main>
      <footer className="footer">
        <div className="container">
          © 2026 Customer Onboarding Agent. All rights reserved.
        </div>
      </footer>
    </div>
  )
}

export default Layout