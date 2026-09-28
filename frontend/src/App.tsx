import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ChildrenList from './pages/ChildrenList'
import ChildDetail from './pages/ChildDetail'
import MeetingsList from './pages/MeetingsList'
import MeetingDetail from './pages/MeetingDetail'
import TeamMembers from './pages/TeamMembers'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/children" element={<ChildrenList />} />
        <Route path="/children/:id" element={<ChildDetail />} />
        <Route path="/meetings" element={<MeetingsList />} />
        <Route path="/meetings/:id" element={<MeetingDetail />} />
        <Route path="/team" element={<TeamMembers />} />
      </Routes>
    </Layout>
  )
}

export default App
