import http from './http'

export interface LoginPayload { username: string; password: string }
export interface LoginResp { access: string; refresh: string }

export const authApi = {
  login: (p: LoginPayload) => http.post<LoginResp>('/auth/login', p).then(r => r.data),
  refresh: (refresh: string) => http.post<{ access: string }>('/auth/refresh', { refresh }).then(r => r.data),
}
