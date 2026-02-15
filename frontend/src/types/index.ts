// 用户类型
export interface User {
  id: number;
  username: string;
  email?: string;
  preferences?: {
    primary_categories: string[];
    sub_categories: string[];
  };
  created_at: string;
}

// 会话类型
export interface Session {
  id: number;
  user_id: number;
  token: string;
  expires_at: string;
  created_at: string;
}

// 分类类型
export interface Category {
  name: string;
  level: number;
}

// 注册请求类型
export interface RegisterRequest {
  username: string;
  password: string;
  email?: string;
  primary_categories: string[];
  sub_categories: string[];
}

// 登录请求类型
export interface LoginRequest {
  username: string;
  password: string;
}

// API 响应类型
export interface ApiResponse<T = any> {
  code: number;
  message: string;
  data?: T;
}
