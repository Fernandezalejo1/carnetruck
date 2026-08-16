import { Navigate, Route, Routes } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ShipmentDetail from "./pages/ShipmentDetail";
import Alerts from "./pages/Alerts";
import Certificates from "./pages/Certificates";
import NewShipment from "./pages/NewShipment";

function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center text-slate-500">
        Cargando…
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

export default function App() {
  const { user } = useAuth();
  return (
    <Routes>
      <Route path="/login" element={user ? <Navigate to="/" replace /> : <Login />} />
      <Route
        element={
          <RequireAuth>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Dashboard />} />
        <Route path="/shipments/:id" element={<ShipmentDetail />} />
        <Route path="/shipments/new" element={<NewShipment />} />
        <Route path="/alerts" element={<Alerts />} />
        <Route path="/certificates" element={<Certificates />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
