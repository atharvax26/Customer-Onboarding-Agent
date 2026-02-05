import React from 'react'
import { Link } from 'react-router-dom'

const Unauthorized: React.FC = () => {
  return (
    <div className="unauthorized-page">
      <h1>Unauthorized Access</h1>
      <p>You don't have permission to access this page.</p>
      <p>Please contact your administrator or <Link to="/login">login</Link> with appropriate credentials.</p>
      <Link to="/" className="btn btn-primary">
        Go Home
      </Link>
    </div>
  )
}

export default Unauthorized