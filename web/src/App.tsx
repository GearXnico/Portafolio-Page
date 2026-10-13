import { Route, Routes } from "react-router";

import { AdminLayout } from "./components/AdminLayout";
import { RequireAdmin } from "./components/RequireAdmin";
import { AdminLoginPage } from "./pages/AdminLoginPage";
import { AdminExperiencePage } from "./pages/AdminExperiencePage";
import { AdminMessagesPage } from "./pages/AdminMessagesPage";
import { AdminPage } from "./pages/AdminPage";
import { AdminProfilePage } from "./pages/AdminProfilePage";
import { AdminProjectEditPage } from "./pages/AdminProjectEditPage";
import { AdminProjectsPage } from "./pages/AdminProjectsPage";
import { AdminSkillsPage } from "./pages/AdminSkillsPage";
import { AdminVisitsPage } from "./pages/AdminVisitsPage";
import { PublicSite } from "./pages/PublicSite";

/** Web routes: the admin panel at `/admin` and the public page everywhere else. */
export function App() {
  return (
    <Routes>
      <Route path="/admin" element={<AdminLayout />}>
        <Route path="login" element={<AdminLoginPage />} />
        {/* Everything inside RequireAdmin requires a session; without one, it redirects to the login. */}
        <Route element={<RequireAdmin />}>
          <Route index element={<AdminPage />} />
          <Route path="projects" element={<AdminProjectsPage />} />
          <Route path="projects/new" element={<AdminProjectEditPage />} />
          <Route path="projects/:id" element={<AdminProjectEditPage />} />
          <Route path="profile" element={<AdminProfilePage />} />
          <Route path="skills" element={<AdminSkillsPage />} />
          <Route path="experience" element={<AdminExperiencePage />} />
          <Route path="messages" element={<AdminMessagesPage />} />
          <Route path="visits" element={<AdminVisitsPage />} />
        </Route>
      </Route>
      <Route path="*" element={<PublicSite />} />
    </Routes>
  );
}
