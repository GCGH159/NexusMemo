# 前端组件测试指南

本文档介绍如何使用 Vitest + Testing Library 进行 React 组件测试。

## 目录

- [环境配置](#环境配置)
- [运行测试](#运行测试)
- [编写测试](#编写测试)
- [常用技巧](#常用技巧)
- [最佳实践](#最佳实践)

---

## 环境配置

### 已安装的依赖

| 依赖 | 用途 |
|------|------|
| vitest | 测试运行器 |
| @testing-library/react | React 组件测试工具 |
| @testing-library/jest-dom | DOM 断言扩展 |
| @testing-library/user-event | 用户交互模拟 |
| jsdom | DOM 环境模拟 |
| @vitest/ui | 测试 UI 界面 |

### 配置文件

- `vite.config.ts` - Vitest 配置
- `src/setupTests.ts` - 测试环境初始化（mock localStorage、matchMedia 等）

---

## 运行测试

```bash
# 进入前端目录
cd frontend

# 监听模式运行测试（推荐开发时使用）
npm run test

# 单次运行测试
npm run test:run

# 打开测试 UI 界面
npm run test:ui

# 生成测试覆盖率报告
npm run test:coverage
```

---

## 编写测试

### 测试文件位置

测试文件放在 `src/__tests__/` 目录下，命名格式为 `*.test.tsx` 或 `*.test.ts`。

### 基本结构

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import MyComponent from '../pages/MyComponent'

describe('MyComponent 组件', () => {
  beforeEach(() => {
    // 每个测试前执行的代码
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('应该正确渲染', () => {
    render(<MyComponent />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })
})
```

### 核心概念

#### 1. describe - 测试套件

用于组织相关的测试用例：

```tsx
describe('Login 组件', () => {
  // 测试用例...
})
```

#### 2. it/test - 测试用例

定义单个测试：

```tsx
it('应该显示错误提示', () => {
  // 测试逻辑
})

// 或者使用 test
test('应该显示错误提示', () => {
  // 测试逻辑
})
```

#### 3. expect - 断言

验证测试结果：

```tsx
expect(element).toBeInTheDocument()
expect(value).toBe(1)
expect(array).toHaveLength(3)
```

---

## 常用技巧

### 1. 渲染组件

#### 基本渲染

```tsx
import { render } from '@testing-library/react'

render(<MyComponent />)
```

#### 包装 Provider

如果组件需要 Router 或其他 Provider：

```tsx
import { BrowserRouter } from 'react-router-dom'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'

const renderWithProviders = (component: React.ReactElement) => {
  return render(
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </ConfigProvider>
  )
}

renderWithProviders(<MyComponent />)
```

### 2. 查询元素

#### getBy* - 获取单个元素

```tsx
// 通过文本
screen.getByText('登录')
screen.getByText(/登录/)  // 正则匹配

// 通过角色（推荐）
screen.getByRole('button', { name: '登录' })
screen.getByRole('textbox', { name: '用户名' })

// 通过占位符
screen.getByPlaceholderText('请输入用户名')

// 通过测试 ID
screen.getByTestId('submit-button')
```

#### getAllBy* - 获取多个元素

```tsx
// 当有多个匹配时使用
screen.getAllByText('学习')
```

#### queryBy* - 查询元素（不存在时不报错）

```tsx
// 用于断言元素不存在
expect(screen.queryByText('错误信息')).not.toBeInTheDocument()
```

### 3. 模拟用户交互

#### fireEvent

```tsx
import { fireEvent } from '@testing-library/react'

// 点击
fireEvent.click(button)

// 输入
fireEvent.change(input, { target: { value: 'test' } })

// 提交表单
fireEvent.submit(form)
```

#### userEvent（更真实）

```tsx
import userEvent from '@testing-library/user-event'

it('用户输入测试', async () => {
  const user = userEvent.setup()
  
  await user.type(input, 'hello')
  await user.click(button)
  await user.clear(input)
})
```

### 4. 等待异步操作

```tsx
import { waitFor } from '@testing-library/react'

it('异步测试', async () => {
  render(<Component />)
  
  await waitFor(() => {
    expect(screen.getByText('加载完成')).toBeInTheDocument()
  })
})
```

### 5. Mock 模块

#### Mock 函数

```tsx
const mockFn = vi.fn()

// 设置返回值
mockFn.mockReturnValue('value')
mockFn.mockResolvedValue('async value')

// 验证调用
expect(mockFn).toHaveBeenCalled()
expect(mockFn).toHaveBeenCalledWith('arg1', 'arg2')
```

#### Mock 模块

```tsx
// Mock API
vi.mock('../api/auth', () => ({
  login: vi.fn(),
  getCurrentUser: vi.fn(),
}))

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})
```

### 6. Mock localStorage

已在 `setupTests.ts` 中配置，可直接使用：

```tsx
it('localStorage 测试', () => {
  localStorage.setItem('token', 'test-token')
  expect(localStorage.getItem('token')).toBe('test-token')
  
  // 验证调用
  expect(localStorage.setItem).toHaveBeenCalledWith('token', 'test-token')
})
```

---

## 最佳实践

### 1. 测试用户行为，而非实现细节

```tsx
// ❌ 不推荐：测试实现细节
expect(component.state.isLoading).toBe(true)

// ✅ 推荐：测试用户看到的内容
expect(screen.getByRole('status')).toBeInTheDocument()
```

### 2. 使用语义化查询

```tsx
// ❌ 不推荐
screen.getByClassName('btn-primary')

// ✅ 推荐
screen.getByRole('button', { name: '提交' })
```

### 3. 测试用例命名清晰

```tsx
// ❌ 不推荐
it('test 1', () => {})

// ✅ 推荐
it('当用户名为空时应该显示错误提示', () => {})
```

### 4. 每个测试独立

```tsx
describe('Component', () => {
  beforeEach(() => {
    // 重置状态
    vi.clearAllMocks()
    localStorage.clear()
  })
  
  // 测试用例...
})
```

### 5. 避免测试第三方库

```tsx
// ❌ 不推荐：测试 Ant Design 的功能
it('Button 应该有正确的样式', () => {})

// ✅ 推荐：测试你的组件如何使用它
it('点击按钮应该提交表单', () => {})
```

---

## 示例：完整的组件测试

```tsx
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'

// Mock 导航
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

// Mock API
vi.mock('../api/auth', () => ({
  login: vi.fn(),
}))

import { login } from '../api/auth'
const mockLogin = vi.mocked(login)

// 包装组件
const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('Login 组件', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('应该正确渲染登录表单', () => {
    renderWithRouter(<Login />)
    
    expect(screen.getByText('NexusMemo 登录')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入用户名')).toBeInTheDocument()
    expect(screen.getByPlaceholderText('请输入密码')).toBeInTheDocument()
  })

  it('登录成功后应该跳转到首页', async () => {
    mockLogin.mockResolvedValueOnce({
      code: 200,
      data: { token: 'test-token', user: { id: 1, username: 'test' } },
    })
    
    renderWithRouter(<Login />)
    
    fireEvent.change(screen.getByPlaceholderText('请输入用户名'), {
      target: { value: 'testuser' },
    })
    fireEvent.change(screen.getByPlaceholderText('请输入密码'), {
      target: { value: 'password' },
    })
    fireEvent.click(screen.getByRole('button', { name: /登\s*录/ }))
    
    await waitFor(() => {
      expect(mockLogin).toHaveBeenCalledWith({
        username: 'testuser',
        password: 'password',
      })
    })
  })
})
```

---

## 常见问题

### 1. Ant Design 组件文本有空格

Ant Design 按钮文本可能包含空格，使用正则匹配：

```tsx
screen.getByRole('button', { name: /登\s*录/ })
```

### 2. 元素出现多次

使用 `getAllBy*`：

```tsx
expect(screen.getAllByText('学习').length).toBeGreaterThan(0)
```

### 3. 异步更新警告

使用 `waitFor` 包装断言：

```tsx
await waitFor(() => {
  expect(screen.getByText('成功')).toBeInTheDocument()
})
```

### 4. Spin 组件没有 role

使用 class 查询：

```tsx
const spinElement = document.querySelector('.ant-spin')
expect(spinElement).toBeInTheDocument()
```

---

## 参考资源

- [Vitest 官方文档](https://vitest.dev/)
- [Testing Library 官方文档](https://testing-library.com/docs/react-testing-library/intro/)
- [Testing Library 查询方法](https://testing-library.com/docs/queries/about/)
- [User Event 文档](https://testing-library.com/docs/user-event/intro/)
