
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Keywords from './pages/Keywords';
import Mentions from './pages/Mentions';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import Influencers from './pages/influencers';
import Geography from './pages/Geography';
import Reports from './pages/Reports';

// Créer le QueryClient
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="keywords" element={<Keywords />} />
            <Route path="mentions" element={<Mentions />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="settings" element={<Settings />} />
            <Route path="influencers" element={<Influencers />} />
            <Route path="geography" element={<Geography />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
