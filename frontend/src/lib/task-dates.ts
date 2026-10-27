export function parseTaskDate(value: string): Date {
  // Legacy API responses without an offset represent UTC.
  const date = new Date(
    /[zZ]|[+-]\d{2}:\d{2}$/.test(value) ? value : `${value}Z`
  )
  if (Number.isNaN(date.getTime())) throw new Error('Enter a valid deadline')
  return date
}

export function toLocalDateTime(value?: string | null): string {
  if (!value) return ''
  const date = parseTaskDate(value)
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
  return local.toISOString().slice(0, 16)
}

export function toUtcDateTime(value: string): string | null {
  if (!value) return null
  if (!/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(value)) {
    throw new Error('Enter a valid deadline')
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) throw new Error('Enter a valid deadline')
  if (toLocalDateTime(date.toISOString()) !== value) {
    throw new Error('That local time does not exist. Choose another deadline.')
  }
  return date.toISOString()
}
