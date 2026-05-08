import { useState, useEffect } from 'react';
import Landing from './components/Landing';
import Login from './components/Login';
import ProjectList from './components/ProjectList';
import ProjectDashboard from './components/ProjectDashboard';
import InstitutionalDashboard from './components/InstitutionalDashboard';
import AIToolRegistry from './components/AIToolRegistry';
import UseCases from './components/UseCases';
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
  const [templateSeed, setTemplateSeed] = useState(null);

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

  let view;
  if (currentView === 'loading') {
    view = <div className="loading">Loading...</div>;
  } else if (currentView === 'landing') {
    view = <Landing onGetStarted={(opts) => { setLoginPrefill(!!opts?.prefill); setCurrentView('login'); }} />;
  } else if (currentView === 'login') {
    view = <Login onLogin={handleLogin} onBack={() => setCurrentView('landing')} prefillDemo={loginPrefill} />;
  } else if (currentView === 'dashboard') {
    view = <InstitutionalDashboard user={currentUser} role={userRole} onLogout={handleLogout} onBack={() => setCurrentView('projects')} onViewToolRegistry={() => setCurrentView('tool-registry')} />;
  } else if (currentView === 'tool-registry') {
    view = <AIToolRegistry user={currentUser} role={userRole} onLogout={handleLogout} onBack={() => setCurrentView('projects')} onViewDashboard={() => setCurrentView('dashboard')} onViewUseCases={() => setCurrentView('use-cases')} />;
  } else if (currentView === 'use-cases') {
    view = (
      <UseCases
        user={currentUser}
        role={userRole}
        onLogout={handleLogout}
        onBack={() => setCurrentView('projects')}
        onViewToolRegistry={() => setCurrentView('tool-registry')}
        onViewDashboard={() => setCurrentView('dashboard')}
        onUseAsTemplate={(seed) => { setTemplateSeed(seed); setCurrentView('projects'); }}
      />
    );
  } else if (currentView === 'project-detail' && selectedProject) {
    view = (
      <ProjectDashboard
        project={selectedProject}
        user={currentUser}
        role={userRole}
        onBack={handleBackToProjects}
        onLogout={handleLogout}
        onProjectUpdated={(updated) => setSelectedProject(updated)}
        onViewToolRegistry={() => setCurrentView('tool-registry')}
        onViewDashboard={() => setCurrentView('dashboard')}
        onViewUseCases={() => setCurrentView('use-cases')}
      />
    );
  } else {
    view = (
      <ProjectList
        user={currentUser}
        role={userRole}
        onSelectProject={handleSelectProject}
        onLogout={handleLogout}
        onViewDashboard={() => setCurrentView('dashboard')}
        onViewToolRegistry={() => setCurrentView('tool-registry')}
        onViewUseCases={() => setCurrentView('use-cases')}
        templateSeed={templateSeed}
        onTemplateConsumed={() => setTemplateSeed(null)}
      />
    );
  }

  return (
    <>
      <div className="prototype-banner" role="status" aria-label="Prototype notice">
        <span className="prototype-banner-dot" aria-hidden="true"></span>
        Prototype · For TiE 2026 demonstration · Demo data only · Not connected to live student records
      </div>
      <div className="prototype-banner-spacer" aria-hidden="true"></div>
      {view}
    </>
  );
}

export default App;
