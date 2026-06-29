import React from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { AppShell } from "@/components/AppShell";
import { PublicShell } from "@/components/PublicShell";
import { UpgradeRequiredModal } from "@/components/UpgradeRequiredModal";
import { LandingPage } from "@/pages/LandingPage";
import { AboutPage } from "@/pages/AboutPage";
import { BlogPage } from "@/pages/BlogPage";
import { LoginPage, RegisterPage } from "@/pages/AuthPages";
import { DashboardPage } from "@/pages/DashboardPage";
import { RunsListPage, RunDetailPage } from "@/pages/RunsPages";
import { IntegrationsPage } from "@/pages/IntegrationsPage";
import { InsightsPage } from "@/pages/InsightsPage";
import { AlertsPage } from "@/pages/AlertsPage";
import { LivePipelinesPage } from "@/pages/LivePipelinesPage";
import { PricingPage } from "@/pages/PricingPage";

/**
 * Auth-gated route — redirects to login if user not authenticated.
 */
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
          Authenticating…
        </div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/auth/login" state={{ from: location.pathname }} replace />;
  }

  return children;
}

/**
 * Auth-only route — redirects to dashboard if already logged in.
 */
function PublicRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) return <Navigate to="/" replace />;
  return children;
}

/**
 * Pricing route — renders inside AppShell for authenticated users,
 * and inside PublicShell for visitors.
 */
function PricingRoute() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (user) {
    return (
      <AppShell>
        <PricingPage />
      </AppShell>
    );
  }
  return (
    <PublicShell>
      <PricingPage />
    </PublicShell>
  );
}

/**
 * Root route — landing page for visitors, dashboard for authenticated users.
 */
function RootRoute() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-muted-foreground font-mono text-xs uppercase tracking-wider animate-status-pulse">
          Loading…
        </div>
      </div>
    );
  }
  if (user) {
    return (
      <AppShell>
        <DashboardPage />
      </AppShell>
    );
  }
  return (
    <PublicShell>
      <LandingPage />
    </PublicShell>
  );
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <UpgradeRequiredModal />
        <Toaster
          theme="dark"
          position="bottom-right"
          toastOptions={{
            classNames: {
              toast: "bg-card border border-border text-foreground font-mono text-xs",
              description: "text-muted-foreground",
            },
          }}
        />
        <Routes>
          {/* Public auth routes */}
          <Route
            path="/auth/login"
            element={
              <PublicRoute>
                <LoginPage />
              </PublicRoute>
            }
          />
          <Route
            path="/auth/register"
            element={
              <PublicRoute>
                <RegisterPage />
              </PublicRoute>
            }
          />

          {/* Public marketing routes — Home, About, Blog (always public shell) */}
          <Route path="/" element={<RootRoute />} />
          <Route
            path="/about"
            element={
              <PublicShell>
                <AboutPage />
              </PublicShell>
            }
          />
          <Route
            path="/blog"
            element={
              <PublicShell>
                <BlogPage />
              </PublicShell>
            }
          />

          {/* Protected routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <AppShell>
                  <DashboardPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs"
            element={
              <ProtectedRoute>
                <AppShell>
                  <RunsListPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/live"
            element={
              <ProtectedRoute>
                <AppShell>
                  <LivePipelinesPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/runs/:runId"
            element={
              <ProtectedRoute>
                <AppShell>
                  <RunDetailPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/integrations"
            element={
              <ProtectedRoute>
                <AppShell>
                  <IntegrationsPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/insights"
            element={
              <ProtectedRoute>
                <AppShell>
                  <InsightsPage />
                </AppShell>
              </ProtectedRoute>
            }
          />
          <Route
            path="/alerts"
            element={
              <ProtectedRoute>
                <AppShell>
                  <AlertsPage />
                </AppShell>
              </ProtectedRoute>
            }
          />


          {/* Pricing — accessible publicly and to authenticated users */}
          <Route
            path="/pricing"
            element={<PricingRoute />}
          />

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
