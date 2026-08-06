import { useState, useEffect, useRef } from 'react'
import { Search, ServerCrash, Database, Braces, User, Settings, FileText, Activity } from 'lucide-react'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  
  // Filter state
  const [activeFilter, setActiveFilter] = useState('all')

  // Debounce search
  const timeoutRef = useRef(null)

  const performSearch = async (searchQuery) => {
    if (!searchQuery.trim()) {
      setResults([])
      setSearched(false)
      return
    }

    setLoading(true)
    setSearched(true)
    try {
      const response = await fetch(`/search?q=${encodeURIComponent(searchQuery)}`)
      const data = await response.json()
      setResults(data.results || [])
    } catch (error) {
      console.error("Error fetching search results:", error)
      setResults([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => performSearch(query), 400)
    return () => clearTimeout(timeoutRef.current)
  }, [query])

  const getSourceIcon = (type) => {
    switch (type?.toLowerCase()) {
      case 'slack': return <ServerCrash size={14} />
      case 'confluence': return <Database size={14} />
      case 'github': return <Braces size={14} />
      default: return <FileText size={14} />
    }
  }

  const [showProfileMenu, setShowProfileMenu] = useState(false)

  const handleSettingsClick = () => {
    alert("Settings panel coming soon! This is where we'll configure database connections and API keys.")
  }

  // Apply frontend filter
  const filteredResults = results.filter(result => {
    if (activeFilter === 'all') return true
    if (activeFilter === 'github') return result.source_type === 'github'
    if (activeFilter === 'confluence') return result.source_type === 'confluence'
    if (activeFilter === 'slack') return result.source_type === 'slack'
    return true
  })

  return (
    <div className="app-layout">
      {/* Standard Top Navigation */}
      <header className="top-nav">
        <div className="brand">
          <img src="/logo.jpg" alt="SearchOps Logo" style={{height: '24px', width: 'auto', borderRadius: '4px'}} />
          SearchOps Workspace
        </div>
        <div className="nav-actions" style={{ position: 'relative' }}>
          <Settings size={18} style={{cursor: 'pointer'}} onClick={handleSettingsClick} />
          
          <div 
            className="avatar" 
            style={{cursor: 'pointer'}} 
            onClick={() => setShowProfileMenu(!showProfileMenu)}
          >
            <User size={18} />
          </div>

          {showProfileMenu && (
            <div style={{
              position: 'absolute', 
              top: '40px', 
              right: '0', 
              backgroundColor: 'white', 
              border: '1px solid var(--border-color)', 
              borderRadius: '6px', 
              boxShadow: 'var(--shadow-md)', 
              padding: '0.5rem', 
              width: '180px',
              zIndex: 100
            }}>
              <div style={{padding: '0.5rem', fontSize: '0.85rem', fontWeight: '600', borderBottom: '1px solid var(--border-color)', marginBottom: '0.25rem'}}>
                Signed in as Admin
              </div>
              <div 
                style={{padding: '0.5rem', fontSize: '0.85rem', cursor: 'pointer', borderRadius: '4px'}} 
                onMouseOver={(e) => e.target.style.backgroundColor = 'var(--bg-sidebar)'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                onClick={() => alert("Profile coming soon!")}
              >
                View Profile
              </div>
              <div 
                style={{padding: '0.5rem', fontSize: '0.85rem', cursor: 'pointer', borderRadius: '4px', color: 'red'}}
                onMouseOver={(e) => e.target.style.backgroundColor = '#fef2f2'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'transparent'}
                onClick={() => { alert("Signed out!"); setShowProfileMenu(false); }}
              >
                Sign Out
              </div>
            </div>
          )}
        </div>
      </header>

      <div className="main-wrapper">
        {/* Interactive Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-title">Discovery</div>
          <ul className="sidebar-nav">
            <li 
              className={activeFilter === 'all' ? 'active' : ''} 
              onClick={() => setActiveFilter('all')}
            >
              <Search size={16} /> Global Search
            </li>
            <li onClick={() => alert("Activity feed coming soon!")}><Activity size={16} /> Recent Activity</li>
            <li onClick={() => alert("Saved queries coming soon!")}><FileText size={16} /> Saved Queries</li>
          </ul>
          
          <div className="sidebar-title" style={{marginTop: '2rem'}}>Filters</div>
          <ul className="sidebar-nav">
            <li 
              className={activeFilter === 'github' ? 'active' : ''} 
              onClick={() => setActiveFilter('github')}
            >
              <Braces size={16} /> Codebase
            </li>
            <li 
              className={activeFilter === 'confluence' ? 'active' : ''} 
              onClick={() => setActiveFilter('confluence')}
            >
              <Database size={16} /> Documentation
            </li>
            <li 
              className={activeFilter === 'slack' ? 'active' : ''} 
              onClick={() => setActiveFilter('slack')}
            >
              <ServerCrash size={16} /> Incident Reports
            </li>
          </ul>
        </aside>

        {/* Content Area */}
        <main className="content-area">
          <div className="search-section">
            <div className="search-container">
              <input 
                type="text" 
                className="search-input" 
                placeholder="Search across all internal data..." 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                autoFocus
              />
              <Search className="search-icon" size={20} />
            </div>
            {searched && !loading && (
              <div className="results-count">
                Found {filteredResults.length} results for "{query}" {activeFilter !== 'all' ? `in ${activeFilter}` : ''}
              </div>
            )}
          </div>

          {loading && (
            <div className="loader">
              <div className="spinner"></div>
              Loading results...
            </div>
          )}

          {!loading && searched && filteredResults.length === 0 && (
            <div className="empty-state">
              <Search className="empty-icon" size={48} />
              <p>No results found for your active filters. Try clearing them.</p>
            </div>
          )}

          {!loading && filteredResults.length > 0 && (
            <div className="results-container">
              {filteredResults.map((result, index) => (
                <div key={index} className="result-card">
                  <div className="result-header">
                    <span className={`result-source-badge source-${result.source?.toLowerCase()}`}>
                      {result.source?.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <h3 className="result-title">{result.title}</h3>
                  <p className="result-content">{result.content_snippet}</p>
                  
                  <div className="result-footer">
                    <div className="footer-item">
                      <User size={14} /> 
                      {result.author_name}
                    </div>
                    <div className="footer-item">
                      {getSourceIcon(result.source_type)}
                      {result.source_type || 'Document'}
                    </div>
                    <div className="footer-item" style={{marginLeft: 'auto'}}>
                      Rank: {index + 1} | Score: {result.rrf_score ? result.rrf_score.toFixed(3) : result.score.toFixed(3)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App
