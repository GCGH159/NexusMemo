import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Home from '../pages/Home'

// Mock react-router-dom 的 useNavigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock auth API
vi.mock('../api/auth', () => ({
  getCurrentUser: vi.fn(),
}))

import { getCurrentUser } from '../api/auth'

const mockGetCurrentUser = vi.mocked(getCurrentUser)

// 包装组件以提供 Router 上下文
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

describe('Home 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('加载中应该显示 Spin 组件', () => {
    mockGetCurrentUser.mockImplementation(() => new Promise(() => {}))
    
    renderWithRouter(<Home />)
    
    // Ant Design Spin 组件使用 class 包含 "ant-spin"
    const spinElement = document.querySelector('.ant-spin')
    expect(spinElement).toBeInTheDocument()
  })

  it('应该正确显示用户信息', async () => {
    mockGetCurrentUser.mockResolvedValueOnce({
      code: 200,
      data: {
        id: 1,
        username: 'testuser',
        preferences: {
          primary_categories: ['学习', '工作'],
        },
      },
    })
    
    renderWithRouter(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('欢迎, testuser')).toBeInTheDocument()
    })
  })

  it('应该正确渲染侧边栏菜单', async () => {
    mockGetCurrentUser.mockResolvedValueOnce({
      code: 200,
      data: {
        id: 1,
        username: 'testuser',
        preferences: {
          primary_categories: ['学习', '工作'],
        },
      },
    })
    
    renderWithRouter(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('NexusMemo')).toBeInTheDocument()
      expect(screen.getByText('全部')).toBeInTheDocument()
      // 使用 getAllByText 因为可能有多个匹配
      expect(screen.getAllByText('学习').length).toBeGreaterThan(0)
      expect(screen.getAllByText('工作').length).toBeGreaterThan(0)
    })
  })

  it('点击退出登录应该清除 localStorage 并跳转', async () => {
    mockGetCurrentUser.mockResolvedValueOnce({
      code: 200,
      data: {
        id: 1,
        username: 'testuser',
        preferences: {},
      },
    })
    
    renderWithRouter(<Home />)
    
    await waitFor(() => {
      expect(screen.getByText('欢迎, testuser')).toBeInTheDocument()
    })
    
    // 使用文本查找按钮（Ant Design 按钮可能包含图标）
    const logoutButton = screen.getByText('退出登录').closest('button')
    if (logoutButton) {
      fireEvent.click(logoutButton)
    }
    
    expect(localStorage.removeItem).toHaveBeenCalledWith('token')
    expect(localStorage.removeItem).toHaveBeenCalledWith('user')
    expect(mockNavigate).toHaveBeenCalledWith('/login')
  })

  it('点击菜单项应该可以正常交互', async () => {
    mockGetCurrentUser.mockResolvedValueOnce({
      code: 200,
      data: {
        id: 1,
        username: 'testuser',
        preferences: {
          primary_categories: ['学习', '工作'],
        },
      },
    })
    
    renderWithRouter(<Home />)
    
    await waitFor(() => {
      // 等待菜单渲染完成
      expect(screen.getByText('NexusMemo')).toBeInTheDocument()
    })
    
    // 点击"全部"菜单项（这个文本是唯一的）
    const allMenuItem = screen.getByText('全部')
    fireEvent.click(allMenuItem)
    
    // 验证组件仍然正常渲染
    expect(screen.getByText('NexusMemo')).toBeInTheDocument()
  })
})
