import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

const nav = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/alerts", label: "Alertas" },
  { to: "/certificates", label: "Certificados" },
  { to: "/shipments/new", label: "Nuevo embarque" },
];

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="flex min-h-screen">
      <aside className="w-56 shrink-0 bg-slate-900 text-slate-200">
        <div className="px-5 py-5">
          <div className="text-lg font-bold text-white">❄️ Carnetruck</div>
          <div className="text-xs text-slate-400">Cadena de frío</div>
        </div>
        <nav className="mt-2 space-y-1 px-3">
          {nav.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-md px-3 py-2 text-sm transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-300 hover:bg-slate-800 hover:text-white"
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
          <div className="text-sm text-slate-500">Monitoreo en tiempo real</div>
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm font-medium">{user?.full_name || user?.email}</div>
              <div className="text-xs text-slate-400">{user?.role}</div>
            </div>
            <button
              onClick={handleLogout}
              className="rounded-md border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
            >
              Salir
            </button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
