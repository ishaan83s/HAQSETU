import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom"

import Onboarding from "./pages/Onboarding"
import Login from "./pages/Login"
import VerifyOtp from "./pages/VerifyOtp"
import Context from "./pages/Context"
import Incident from "./pages/Incident"

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Onboarding />} />
        <Route path="/login" element={<Login />} />
        <Route path="/verify-otp" element={<VerifyOtp />} />
        <Route path="/context" element={<Context />} />
        <Route path="/incident" element={<Incident />} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App