export const ru = {
  loading: "Загружаем…",
  error: "Нет связи. Пробуем снова.",
  retry: "Повторить",
} as const;

export type Dict = typeof ru;

export function useT(): Dict {
  return ru;
}
