export const ru = {
  loading: "Загружаем…",
  error: "Нет связи. Пробуем снова.",
  retry: "Повторить",
  brand: "balance",
  tagline: "найди свой баланс",
  heroTitle: "Кофе к твоему приходу",
  orderNow: "Заказать",
  lookMenu: "Меню",
  menuTitle: "Выбери свой кофе",
  menuSubtitle: "Каждый напиток — маленькая история. Смотри, как он готовится.",
  repeatLast: "Повторить последний заказ",
  all: "Все",
  emptyCategory: "Здесь пока пусто. Загляните в другие категории.",
  soldOut: "Закончилось",
  openNow: "Открыто сейчас",
  closed: "Закрыто",
  chooseLocation: "Выберите точку",
  locationConfirmTitle: "Сменить точку?",
  locationConfirmText: "В заказе уже есть напитки. При смене точки заказ очистится.",
  keep: "Оставить",
  change: "Сменить",
  back: "Назад",
  addToOrder: "Добавить в заказ",
  required: "Обязательно",
  chooseToContinue: "Выберите вариант, чтобы продолжить",
  unavailableOption: "Нет в наличии",
  bonusPlus: (n: number) => `+${n} баллов`,
  cart: "Заказ",
  added: "Добавлено",
  cartEmpty: "Пока пусто",
  checkoutSoon: "Оформление появится в следующей фазе",
  ordersSoon: "Заказы появятся в следующей фазе",
  bonusSoon: "Бонусы появятся позже",
  profileSoon: "Профиль появится позже",
  tabs: { menu: "Меню", orders: "Заказы", bonus: "Бонусы", profile: "Профиль" },
} as const;

export type Dict = typeof ru;

export function useT(): Dict {
  return ru;
}
