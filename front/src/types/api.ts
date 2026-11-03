/**
 * 对齐后端统一响应模型 APIResponse（src/app/schemas/common.py）。
 * 注意：后端全局异常处理器返回的 code 为字符串、错误信息字段为 message，
 * 因此前端需同时兼容 msg / message、number / string 两种形态。
 */
export interface ApiRes<T = unknown> {
  code: number | string
  msg?: string
  /** 异常处理器使用的错误字段 */
  message?: string
  data: T | null
}
