import { Link, useLocation } from 'react-router-dom'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const location = useLocation()

  const navItems = [
    { path: '/', label: '首页', icon: '🏠' },
    { path: '/children', label: '儿童管理', icon: '👶' },
    { path: '/meetings', label: '会议管理', icon: '📋' },
    { path: '/team', label: '团队成员', icon: '👥' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-64 bg-white border-r border-gray-200 fixed h-full">
        <div className="p-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-primary-600">IEP会议系统</h1>
          <p className="text-sm text-gray-500 mt-1">自闭症儿童干预管理</p>
        </div>
        <nav className="p-4">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-1 transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary-50 text-primary-600 font-medium'
                  : 'text-gray-600 hover:bg-gray-50'
              }`}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </Link>
          ))}
        </nav>
      </aside>
      <main className="flex-1 ml-64 p-8">
        {children}
      </main>
    </div>
  )
}
