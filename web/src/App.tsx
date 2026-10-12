import { Route, Routes } from "react-router";

import { AdminLayout } from "./components/AdminLayout";
import { RequireAdmin } from "./components/RequireAdmin";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { AdminPage } from "./pages/AdminPage";
import { PublicSite } from "./pages/PublicSite";

/** Rutas de la web: el panel en `/admin` y la página pública en todo lo demás. */
export function App() {
  return (
    <Routes>
      <Route path="/admin" element={<AdminLayout />}>
        <Route path="login" element={<AdminLoginPage />} />
        {/* Todo lo que va dentro de RequireAdmin exige sesión; sin ella, redirige al login. */}
        <Route element={<RequireAdmin />}>
          <Route index element={<AdminPage />} />
        </Route>
      </Route>
      <Route path="*" element={<PublicSite />} />
    </Routes>
  );
}
