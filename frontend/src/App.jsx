import { useState, useEffect } from 'react';
import Landing from './components/Landing';
import Login from './components/Login';
import ProjectList from './components/ProjectList';
import ProjectDashboard from './components/ProjectDashboard';
import InstitutionalDashboard from './components/InstitutionalDashboard';
import AIToolRegistry from './components/AIToolRegistry';
import './App.css';

// Map auth roles to dashboard roles
function mapRole(authRole) {
  const roleMap = { faculty: 'pi', student: 'student' };
  return roleMap[authRole] || authRole;
}

function App() {
  const [currentView, setCurrentView] = useState('loading');
  const [currentUser, setCurrentUser] = useState(null);
  const [userRole, setUserRole] = useState(null);
  const [selectedProject, setSelectedProject] = useState(null);
  const [loginPrefill, setLoginPrefill] = useState(false);

  useEffect(() => {
    const savedUser = localStorage.getItem('raise_user');
    if (savedUser) {
      const user = JSON.parse(savedUser);
      setCurrentUser(user);
      setUserRole(mapRole(user.role));
      setCurrentView('projects');
    } else {
      setCurrentView('landing');
    }
  }, []);

  function handleLogin(user) {
    localStorage.setItem('raise_user', JSON.stringify(user));
    setCurrentUser(user);
    setUserRole(mapRole(user.role));
    setCurrentView('projects');
  }

  function handleLogout() {
    localStorage.removeItem('raise_user');
    setCurrentView('landing');
    setCurrentUser(null);
    setUserRole(null);
    setCurrentView('login');
  }

  function handleSelectProject(project) {
    setSelectedProject(project);
    setCurrentView('project-detail');
  }

  function handleBackToProjects() {
    setSelectedProject(null);
    setCurrentView('projects');
  }

  if (currentView === 'loading') {
    return <div className="loading">Loading...</div>;
  }

  if (currentView === 'landing') {
    return <Landing onGetStarted={(opts) => { setLoginPrefill(!!opts?.prefill); setCurrentView('login'); }} />;
  }

  if (currentView === 'login') {
    return <Login onLogin={handleLogin} onBack={() => setCurrentView('landing')} prefillDemo={loginPrefill} />;
  }

  if (currentView === 'dashboard') {
    return <InstitutionalDashboard user={currentUser} role={userRole} onLogout={handleLogout} onBack={() => setCurrentView('projects')} onViewToolRegistry={() => setCurrentView('tool-registry')} />;
  }

  if (currentView === 'tool-registry') {
    return <AIToolRegistry user={currentUser} role={userRole} onLogout={handleLogout} onBack={() => setCurrentView('projects')} onViewDashboard={() => setCurrentView('dashboard')} />;
  }

  if (currentView === 'project-detail' && selectedProject) {
    return (
      <ProjectDashboard
        project={selectedProject}
        user={currentUser}
        role={userRole}
        onBack={handleBackToProjects}
        onLogout={handleLogout}
        onProjectUpdated={(updated) => setSelectedProject(updated)}
        onViewToolRegistry={() => setCurrentView('tool-registry')}
        onViewDashboard={() => setCurrentView('dashboard')}
      />
    );
  }

  return (
    <ProjectList
      user={currentUser}
      role={userRole}
      onSelectProject={handleSelectProject}
      onLogout={handleLogout}
      onViewDashboard={() => setCurrentView('dashboard')}
      onViewToolRegistry={() => setCurrentView('tool-registry')}
    />
  );
}

export default App;
