import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ThemeProvider } from "@/contexts/ThemeContext";
import { ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { LoginPage } from "@/pages/LoginPage";
import { RegisterPage } from "@/pages/RegisterPage";
import { EventsPage } from "@/pages/EventsPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { YahooFinancePage } from "@/pages/YahooFinancePage";
import { SettingsPage } from "@/pages/SettingsPage";
import { EventDetailPage } from "@/pages/EventDetailPage";
import { ThemeDetailPage } from "@/pages/ThemeDetailPage";
import { EntityDetailPage } from "@/pages/EntityDetailPage";
import { ChatPage } from "@/pages/ChatPage";

export function App() {
  return (
    <AuthProvider>
      <ThemeProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route index element={<EventsPage />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="yahoo-finance" element={<YahooFinancePage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="event/:eventId" element={<EventDetailPage />} />
                <Route path="theme/:themeName" element={<ThemeDetailPage />} />
                <Route path="entity/:entityType/:entityName" element={<EntityDetailPage />} />
                <Route path="chat" element={<ChatPage />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </AuthProvider>
  );
}
