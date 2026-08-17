import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import Onboarding from "./pages/Onboarding"
import Login from "./pages/Login"
import Context from "./pages/Context"
import Incident from "./pages/Incident"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/login" element={<Login />} />
        <Route path="/context" element={<Context />} />
        <Route path="/incident" element={<Incident />} />

        {/* P4 result page — your teammate will implement this */}
        <Route
          path="/result/:incidentId"
          element={<div>Result</div>}
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App