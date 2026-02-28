import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'

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
  login: vi.fn(),
}))

import { login } from '../api/auth'

const mockLogin = vi.mocked(login)

// 包装组件以提供 Router 上下文
const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  )
}

// 辅助函数：查找登录按钮（Ant Design 按钮文本可能有空格）
const getLoginButton = () => {
  return screen.getByRole('button', { name: /登\s*录/ })
}

describe('Login 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('应该正确渲染登录表单', () => {
    renderWithRouter(<Login />)
    
    // 检查标题
    expect(screen.getByText('NexusMemo 登录')).toBeInTheDocument()
    
    // 检查表单字段
    expect(screen.getByPlaceholderText('请输入用户名')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入密码')).toBeInTheDocument()
    
    // 检查按钮（使用正则匹配）
    expect(getLoginButton()).toBeInTheDocument()
    
    // 检查注册链接
    expect(screen.getByText('立即注册')).toBeInTheDocument()
  })

  it('当用户名为空时应该显示错误提示', async () => {
    renderWithRouter(<Login />)
    
    const loginButton = getLoginButton()
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入用户名')).toBeInTheDocument()
    })
  })

  it('当密码为空时应该显示错误提示', async () => {
    renderWithRouter(<Login />)
    
    const usernameInput = screen.getByPlaceholderText('请输入用户名')
    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    
    const loginButton = getLoginButton()
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(screen.getByText('请输入密码')).toBeInTheDocument()
    })
  })

  it('登录成功后应该保存 token 并跳转到首页', async () => {
    mockLogin.mockResolvedValueOnce({
      code: 200,
      data: {
        token: 'test-token',
        user: {
          id: 1,
          username: 'testuser',
        },
      },
    })
    
    renderWithRouter(<Login />)
    
    // 填写表单
    const usernameInput = screen.getByPlaceholderText('请输入用户名')
    const passwordInput = screen.getByPlaceholderText('请输入密码')
    
    fireEvent.change(usernameInput, { target: { value: 'testuser' } })
    fireEvent.change(passwordInput, { target: { value: 'password123' } })
    
    // 提交表单
    const loginButton = getLoginButton()
    fireEvent.click(loginButton)
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password123',
      })
    })
    
    // 检查 localStorage 是否被设置
    await waitFor(() => {
      expect(localStorage.setItem).toHaveBeenCalled()
    })
  })

  it('点击注册链接应该跳转到注册页面', () => {
    renderWithRouter(<Login />)
    
    const registerLink = screen.getByText('立即注册')
    fireEvent.click(registerLink)
    
    expect(mockNavigate).toHaveBeenCalledWith('/register')
  })
})
