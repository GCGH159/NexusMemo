import { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

// 自定义渲染函数，包含常用的 Provider 包装
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, {
    wrapper: ({ children }) => (
      <ConfigProvider locale={zhCN}>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </ConfigProvider>
    ),
    ...options,
  })
}

// 重新导出所有 testing-library 的内容
export * from '@testing-library/react'
export { customRender as render }

// 常用的测试辅助函数

// 等待元素出现
export const waitForElement = async (text: string) => {
  const { findByText } = await import('@testing-library/react')
  return findByText(text)
}

// 模拟 localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {}
  
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key])
    }),
  }
}

// 创建 mock 用户数据
export const createMockUser = (overrides = {}) => ({
  id: 1,
  username: 'testuser',
  email: 'test@example.com',
  preferences: {
    primary_categories: ['学习', '工作'],
  },
  ...overrides,
})

// 创建 mock 登录响应
export const createMockLoginResponse = (overrides = {}) => ({
  code: 200,
  data: {
    token: 'test-token',
    user: createMockUser(),
    ...overrides,
  },
})
